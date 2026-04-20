# Ambient Submit

Claude surface adapter for the Genesis Conductor Ambient Agent Access Layer.

## What it does

Natural language task submission to specialized agents (kiro, codex, claude, gemini, copilot). Routes requests based on intent, constructs TaskEnvelopes, and returns task_id + routing confirmation.

## Skills

### `ambient-submit`

Activated when user says "run in background", "submit to GC", "let kiro handle", "queue this job", or describes async work for specialized agents.

## Configuration

| Variable | Default | Required |
|----------|---------|----------|
| `AMBIENT_API_KEY` | — | Yes |
| `AMBIENT_BASE_URL` | `https://gc-ambient-gateway.iholt.workers.dev` | No |
