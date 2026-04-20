---
name: ambient-submit
description: >-
  Submit tasks to the Genesis Conductor Ambient Agent Access Layer from natural
  language, and check job status. Trigger this skill whenever the user says
  "run this in the background", "submit to GC", "let kiro handle", "let codex
  handle", "ambient execute", "queue this job", "submit this task", "route to
  the agent", or describes any work that should execute asynchronously via a
  specialized agent (kiro, codex, claude, gemini, copilot). Also trigger for
  job status checks: "what's the status of", "check job", "poll progress",
  "is it done yet". This skill IS the Claude surface adapter for the Ambient
  Access Layer - it resolves request_type, constructs a valid TaskEnvelope,
  POSTs to the Ambient API, and returns task_id + routing confirmation. No
  setup required beyond AMBIENT_API_KEY.
---

# ambient-submit

Claude surface adapter for the Genesis Conductor Ambient Agent Access Layer.

Natural language in → TaskEnvelope constructed → job queued → task_id + routing confirmation out.

---

## Config

| Variable | Default | Required |
|----------|---------|----------|
| `AMBIENT_API_KEY` | — | Yes — ask user if not in context |
| `AMBIENT_BASE_URL` | `https://optimization-inversion.genesisconductor.io` | No |

If `AMBIENT_API_KEY` is absent, tell the user: "Set `AMBIENT_API_KEY` in your environment or paste it here." Do not proceed without it.

---

## Step 1 — Parse Intent

Extract from natural language:

**request_type** — resolve via routing table:

| NL signal | request_type | primaryAgent | requiresApproval | policyTier |
|-----------|-------------|--------------|-----------------|------------|
| "implement from spec", "spec-driven", "from the spec" | `implement_feature_from_spec` | kiro | false | standard |
| "implement", "build", "code", "develop" (no spec mention) | `implement_feature` | kiro | false | standard |
| "security fix", "vulnerability", "patch CVE", "remediate" | `security_fix` | codex | true | prod_sensitive |
| "architecture review", "design review", "review system" | `deep_architecture_review` | claude | false | standard |
| "GCP", "gcloud", "cloud ops", "provision infra", "firestore", "cloud run" | `gcp_ops` | gemini | true | prod_sensitive |
| "suggest inline", "editor suggestion", "quick autocomplete", "complete this code", "inline fix", "copilot this" | `inline_suggestion` | copilot | false | standard |
| "deploy", "release", "push to prod", "cut release" | `deploy` | kiro | true | prod_sensitive |
| anything else | `implement_feature` | kiro | true | standard |

**priority** — infer from signal words:
- `critical` — "urgent", "ASAP", "blocking", "critical", "now"
- `high` — "high priority", "important", "soon", "today"
- `low` — "low priority", "whenever", "no rush", "background"
- `normal` — default (no signal)

**candidate_agents** — explicit override if user names an agent: "let kiro handle", "use codex", "route to gemini" → set `candidate_agents: [<agent>]`

**context_refs** — extract repo/spec references: "the nexus-membrane spec", "repo: ambient-access-layer", "spec: membrane-v1" → format as `["repo:<name>", "spec:<name>"]`

**title** — synthesize a concise imperative title from the request (max 80 chars). Example: "Implement Nexus Membrane dependency provisioning"

---

## Step 2 — Construct TaskEnvelope

```json
{
  "task_id": "<will be assigned by API>",
  "workspace_id": "<derived from API key — omit in request body>",
  "source_surface": "claude",
  "request_type": "<resolved above>",
  "title": "<synthesized title>",
  "description": "<user's full natural language input, verbatim>",
  "requested_by": "claude-surface",
  "context_refs": ["<extracted refs, if any>"],
  "priority": "<resolved above>",
  "requires_approval": <true|false from routing table>,
  "candidate_agents": ["<agent if explicitly named>"],
  "policy_tier": "<standard|prod_sensitive from routing table>"
}
```

Omit `context_refs` and `candidate_agents` if empty rather than sending `[]`.

---

## Step 3 — POST to API

```
POST {AMBIENT_BASE_URL}/v1/tasks
Authorization: Bearer {AMBIENT_API_KEY}
Content-Type: application/json

<TaskEnvelope body>
```

**Expected 201 response:**
```json
{
  "task_id": "tsk_xxxxxxxx",
  "job_id": "job_xxxxxxxx",
  "workspace_id": "ws_genesis",
  "status": "pending"
}
```

Cache `task_id → workspace_id` in-session on every successful submission. Used by the approval shortcut — no secondary fetch needed.

**Error handling:**

| HTTP | Action |
|------|--------|
| 401 | Tell user: "API key rejected. Verify AMBIENT_API_KEY." |
| 400 | Show validation error from response body. Ask user to clarify input. |
| 404 | Tell user: "Endpoint not found. Verify AMBIENT_BASE_URL." |
| 5xx | Tell user: "Server error. Retry or check Worker logs." |
| Network failure | Tell user: "Could not reach {AMBIENT_BASE_URL}. Verify the Worker is deployed." |

---

## Step 4 — Present Confirmation

Output this block on successful submission:

```
✅ Task queued

task_id:           tsk_xxxxxxxx
job_id:            job_xxxxxxxx
workspace_id:      ws_genesis
agent:             kiro
request_type:      implement_feature_from_spec
policy_tier:       standard
requires_approval: false
priority:          high
status:            pending
```

If `requires_approval: true`, append:
```
⚠️  This task requires approval before execution.
    Run: ambient approve <approval_id>
    Or say: "approve the pending task"
```

---

## Step 5 — Job Status (on demand)

Trigger when user asks: "check status", "what's happening with", "poll job", "is it done", "show progress".

```
GET {AMBIENT_BASE_URL}/v1/jobs?task_id={task_id}
Authorization: Bearer {AMBIENT_API_KEY}
```

Or by explicit job_id:
```
GET {AMBIENT_BASE_URL}/v1/jobs/{job_id}
Authorization: Bearer {AMBIENT_API_KEY}
```

Present:
```
📊 Job status

job_id:    job_xxxxxxxx
agent:     kiro
status:    running
stage:     provisioning
progress:  42%
updated:   2026-04-09T00:15:00Z
```

If `status: blocked`, always prompt: "This job is blocked. Say 'approve the pending task' or check approvals."

---

## Approval shortcut (optional, in-skill)

If `requires_approval: true` and user says "approve it" / "go ahead" / "approve the pending task":

Fetch the `approval_id` from the job record:
```
GET {AMBIENT_BASE_URL}/v1/jobs/{job_id}
Authorization: Bearer {AMBIENT_API_KEY}
```
Extract `approval_id` from the response, then:

```
POST {AMBIENT_BASE_URL}/v1/approvals/{approval_id}/approve
Authorization: Bearer {AMBIENT_API_KEY}
Content-Type: application/json
{}
```

Confirm: `✅ Approved. Job will resume.`

For state projection checks, use the cached `workspace_id` from the 201 response — no secondary fetch needed:
```
GET {AMBIENT_BASE_URL}/v1/state/{workspace_id}   ← workspace_id from in-session cache
```
If cache miss (fresh session), extract `workspace_id` from `GET /v1/tasks/{task_id}`.

---

## What this skill does NOT do (v1 scope)

- No artifact retrieval (v1.5 — `GET /v1/tasks/:id/artifacts`)
- No state projection display beyond job status
- No webhook registration
- No workspace management

If user asks for these, respond: "That's in the v1.5 adapter scope. For now: task_id `{id}` is queued and I can poll job status on request."

---

## Example interactions

**Submit:**
> "Let kiro implement the Nexus Membrane dependency spec — this is blocking deploy, treat it urgent"

→ request_type: `implement_feature_from_spec`, agent: `kiro` (explicit), priority: `critical`, policy_tier: `standard`, requires_approval: `false`

---

**Submit with prod risk:**
> "Deploy ambient-access-layer to production"

→ request_type: `deploy`, agent: `kiro`, priority: `normal`, policy_tier: `prod_sensitive`, requires_approval: `true`

→ Output includes approval warning.

---

**Status check:**
> "What's the status of tsk_a3f9c21b?"

→ GET /v1/jobs?task_id=tsk_a3f9c21b → present job status block.

