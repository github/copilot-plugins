---
name: sentry
description: Query Sentry for error monitoring, performance data, and issue management. USE THIS SKILL for ANY question about production errors, exceptions, application health, issue investigation, or debugging. This includes questions about what errors are happening, error frequency and impact, root cause analysis, issue assignment and triage, release health, performance traces, and event details. Trigger phrases include "what errors", "show me issues", "how many errors", "debug this issue", "what's failing", "root cause", "assign issue", "resolve issue", "error rate", "what's broken", "production errors", "investigate issue", "trace", "who is on-call for", etc.
---

# Sentry

Sentry is an application monitoring and error tracking platform. The Sentry MCP provides tools to search, inspect, triage, and manage issues and events across your Sentry organization directly from your development environment.

## CRITICAL: When to Use This Skill

**USE Sentry for ANY question about production errors, application health, or issue management.** If the answer involves error monitoring, exception tracking, or debugging production issues, use Sentry.

**ALWAYS use Sentry when the user asks about:**

| User Question Pattern | Example | Tool |
|-----------------------|---------|------|
| What errors are happening | "What errors are we seeing in production?" | `search_issues` |
| Error frequency or counts | "How many errors today?" | `search_events` |
| Specific issue details | "Tell me about PROJ-123" | `get_issue_details` |
| Root cause analysis | "Why is this error happening?" | `analyze_issue_with_seer` |
| Issue triage and assignment | "Assign this to the backend team" | `update_issue` |
| Resolve or ignore issues | "Resolve PROJ-456" | `update_issue` |
| Release health | "Any new errors in the latest release?" | `search_issues` / `find_releases` |
| Performance investigation | "Show me the trace for this request" | `get_trace_details` |
| Error impact | "How many users are affected by this bug?" | `get_issue_tag_values` |
| Error distribution | "Which browsers are hitting this error?" | `get_issue_tag_values` |
| Event-level details | "Show me recent events for this issue" | `search_issue_events` |
| Organizational context | "What projects do we have in Sentry?" | `find_projects` |
| User feedback | "Show me user feedback from production" | `search_issues` |

**DO NOT say "I don't have access to error data"** — use Sentry instead!

## Getting Started

### Find Your Organization

Before making most queries, you need the organization slug. Use `find_organizations` to discover which organizations you have access to.

| Tool | Parameters |
|------|------------|
| `find_organizations` | `{}` |

The response includes each organization's `slug` and `regionUrl` — use these in subsequent tool calls.

### Identify Yourself

To find your own user ID (useful for assigning issues to yourself):

| Tool | Parameters |
|------|------------|
| `whoami` | `{}` |

## Common Workflows

### 1. Investigate Current Issues

Start by searching for unresolved issues to understand what's happening in production.

| Tool | Parameters |
|------|------------|
| `search_issues` | `{ "organizationSlug": "<org>", "naturalLanguageQuery": "unresolved issues in the last 24 hours" }` |
| `search_issues` | `{ "organizationSlug": "<org>", "naturalLanguageQuery": "critical unhandled errors affecting more than 100 users" }` |
| `search_issues` | `{ "organizationSlug": "<org>", "naturalLanguageQuery": "new issues first seen today", "projectSlugOrId": "<project>" }` |

### 2. Get Issue Details and Context

Once you have an issue ID, dive deeper with `get_issue_details`. You can provide either an issue ID with organization or a full Sentry URL.

| Tool | Parameters |
|------|------------|
| `get_issue_details` | `{ "organizationSlug": "<org>", "issueId": "PROJ-123" }` |
| `get_issue_details` | `{ "issueUrl": "https://sentry.io/organizations/<org>/issues/PROJ-123/" }` |

### 3. Analyze Root Cause with Seer

When you need help understanding *why* an error is happening, use Seer for AI-powered root cause analysis. This provides code-level explanations and suggested fixes.

| Tool | Parameters |
|------|------------|
| `analyze_issue_with_seer` | `{ "organizationSlug": "<org>", "issueId": "PROJ-123" }` |
| `analyze_issue_with_seer` | `{ "issueUrl": "https://sentry.io/organizations/<org>/issues/PROJ-123/" }` |

> **Note:** Seer analysis may take 2–5 minutes if no cached analysis exists. Results are cached for subsequent calls.

### 4. Understand Error Impact

Use tag values to understand who and what is affected by an issue.

| Tool | Parameters |
|------|------------|
| `get_issue_tag_values` | `{ "organizationSlug": "<org>", "issueId": "PROJ-123", "tagKey": "browser" }` |
| `get_issue_tag_values` | `{ "organizationSlug": "<org>", "issueId": "PROJ-123", "tagKey": "environment" }` |
| `get_issue_tag_values` | `{ "organizationSlug": "<org>", "issueId": "PROJ-123", "tagKey": "url" }` |
| `get_issue_tag_values` | `{ "organizationSlug": "<org>", "issueId": "PROJ-123", "tagKey": "user" }` |
| `get_issue_tag_values` | `{ "organizationSlug": "<org>", "issueId": "PROJ-123", "tagKey": "os" }` |
| `get_issue_tag_values` | `{ "organizationSlug": "<org>", "issueId": "PROJ-123", "tagKey": "release" }` |

Common tag keys: `url`, `browser`, `browser.name`, `os`, `environment`, `release`, `device`, `user`.

### 5. Triage and Manage Issues

Resolve, ignore, or assign issues directly from your editor.

**Resolve an issue:**

| Tool | Parameters |
|------|------------|
| `update_issue` | `{ "organizationSlug": "<org>", "issueId": "PROJ-123", "status": "resolved" }` |

**Assign to a user:**

| Tool | Parameters |
|------|------------|
| `update_issue` | `{ "organizationSlug": "<org>", "issueId": "PROJ-123", "assignedTo": "user:<user_id>" }` |

**Assign to a team:**

| Tool | Parameters |
|------|------------|
| `update_issue` | `{ "organizationSlug": "<org>", "issueId": "PROJ-123", "assignedTo": "team:<team_slug>" }` |

**Mark as ignored:**

| Tool | Parameters |
|------|------------|
| `update_issue` | `{ "organizationSlug": "<org>", "issueId": "PROJ-123", "status": "ignored" }` |

Valid status values: `resolved`, `resolvedInNextRelease`, `unresolved`, `ignored`.

### 6. Search Events and Get Counts

Use `search_events` for counts, aggregations, and individual event lookups. This is the **only** tool for statistics.

| Tool | Parameters |
|------|------------|
| `search_events` | `{ "organizationSlug": "<org>", "naturalLanguageQuery": "how many errors today" }` |
| `search_events` | `{ "organizationSlug": "<org>", "naturalLanguageQuery": "count of database connection failures this week" }` |
| `search_events` | `{ "organizationSlug": "<org>", "naturalLanguageQuery": "error events from the last hour", "projectSlug": "<project>" }` |
| `search_events` | `{ "organizationSlug": "<org>", "naturalLanguageQuery": "average response time for /api/users" }` |
| `search_events` | `{ "organizationSlug": "<org>", "naturalLanguageQuery": "total tokens used by AI model" }` |

### 7. Filter Events Within an Issue

To drill into specific events for a known issue — by time, environment, release, user, or other tags:

| Tool | Parameters |
|------|------------|
| `search_issue_events` | `{ "issueId": "PROJ-123", "organizationSlug": "<org>", "naturalLanguageQuery": "from the last hour" }` |
| `search_issue_events` | `{ "issueId": "PROJ-123", "organizationSlug": "<org>", "naturalLanguageQuery": "in production with release v2.1.0" }` |
| `search_issue_events` | `{ "issueUrl": "https://sentry.io/.../issues/PROJ-123/", "naturalLanguageQuery": "affecting user alice@example.com" }` |

### 8. Investigate Performance with Traces

When investigating latency or performance issues, look up traces by their 32-character hex ID.

| Tool | Parameters |
|------|------------|
| `get_trace_details` | `{ "organizationSlug": "<org>", "traceId": "a4d1aae7216b47ff8117cf4e09ce9d0a" }` |

### 9. Check Releases

Find recent releases or look up a specific version.

| Tool | Parameters |
|------|------------|
| `find_releases` | `{ "organizationSlug": "<org>" }` |
| `find_releases` | `{ "organizationSlug": "<org>", "projectSlug": "<project>", "query": "v2.1" }` |

### 10. Download Event Attachments

Retrieve screenshots, log files, or other attachments from a specific event.

| Tool | Parameters |
|------|------------|
| `get_event_attachment` | `{ "organizationSlug": "<org>", "projectSlug": "<project>", "eventId": "<event_id>" }` |
| `get_event_attachment` | `{ "organizationSlug": "<org>", "projectSlug": "<project>", "eventId": "<event_id>", "attachmentId": "<attachment_id>" }` |

## Tool Selection Guide

Choose the right tool based on what you need:

| I want to... | Use this tool |
|---------------|--------------|
| **List** issues matching criteria | `search_issues` |
| **Count** errors or get statistics | `search_events` |
| **Inspect** a specific issue (stacktrace, metadata) | `get_issue_details` |
| **Understand** root cause and get fix suggestions | `analyze_issue_with_seer` |
| **See** who/what is affected by an issue | `get_issue_tag_values` |
| **Filter** events within a single issue | `search_issue_events` |
| **Resolve**, ignore, or assign an issue | `update_issue` |
| **Trace** a request across services | `get_trace_details` |
| **Find** organizations, projects, or teams | `find_organizations` / `find_projects` / `find_teams` |
| **Check** recent releases | `find_releases` |
| **Download** event attachments | `get_event_attachment` |
| **Identify** the current user | `whoami` |

## Tips

- **Use Sentry URLs directly.** Many tools accept an `issueUrl` parameter — paste the full Sentry URL and it will extract the organization, project, and issue automatically.
- **Scope to a project.** When possible, pass `projectSlug` or `projectSlugOrId` to narrow results and improve response time.
- **`search_issues` vs `search_events`:** Use `search_issues` for a *list* of grouped issues. Use `search_events` for *counts*, *aggregations*, or *individual event records*.
- **Use `regionUrl`** when querying organizations on specific Sentry regions (e.g., `https://us.sentry.io`). You can find the correct `regionUrl` from the `find_organizations` response.
- **Chain tools for full context.** A typical investigation flow: `search_issues` → `get_issue_details` → `get_issue_tag_values` → `analyze_issue_with_seer`.

## MCP Tool Reference

### whoami

Identify the currently authenticated Sentry user.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| *(none)* | — | — | Returns user name and email |

### find_organizations

Find organizations the user has access to.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | No | Filter by name or slug |

### find_projects

Find projects in an organization.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `organizationSlug` | string | Yes | Organization slug |
| `query` | string | No | Filter by name or slug |

### find_teams

Find teams in an organization.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `organizationSlug` | string | Yes | Organization slug |
| `query` | string | No | Filter by name or slug |

### find_releases

Find releases in an organization.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `organizationSlug` | string | Yes | Organization slug |
| `projectSlug` | string | No | Scope to a specific project |
| `query` | string | No | Search for a version string |

### search_issues

Search for grouped issues. Returns a list of issues with metadata.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `organizationSlug` | string | Yes | Organization slug |
| `naturalLanguageQuery` | string | Yes | Describe what issues to find |
| `projectSlugOrId` | string | No | Scope to a specific project |
| `limit` | number | No | Max results (1–100, default 10) |

### search_events

Search events and perform aggregations. The **only** tool for counts and statistics.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `organizationSlug` | string | Yes | Organization slug |
| `naturalLanguageQuery` | string | Yes | Describe what to search or count |
| `projectSlug` | string | No | Scope to a specific project |
| `limit` | number | No | Max results (1–100, default 10) |

### search_issue_events

Search and filter events within a specific issue.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issueId` | string | Conditional | Issue ID (e.g., `PROJ-123`). Requires `organizationSlug`. |
| `issueUrl` | string | Conditional | Full Sentry issue URL (alternative to `issueId`) |
| `organizationSlug` | string | Conditional | Required when using `issueId` |
| `naturalLanguageQuery` | string | Yes | Describe what events to find |
| `limit` | number | No | Max results (1–100, default 50) |

### get_issue_details

Get detailed information about a specific issue including stacktrace and metadata.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issueId` | string | Conditional | Issue ID (e.g., `PROJ-123`). Requires `organizationSlug`. |
| `issueUrl` | string | Conditional | Full Sentry issue URL (alternative to `issueId`) |
| `organizationSlug` | string | Conditional | Required when using `issueId` |
| `eventId` | string | No | Specific event ID to inspect |

### get_issue_tag_values

Get tag value distribution for an issue (e.g., affected browsers, environments, URLs).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issueId` | string | Conditional | Issue ID. Requires `organizationSlug`. |
| `issueUrl` | string | Conditional | Full Sentry issue URL (alternative to `issueId`) |
| `organizationSlug` | string | Conditional | Required when using `issueId` |
| `tagKey` | string | Yes | Tag to inspect (e.g., `browser`, `url`, `environment`) |

### get_trace_details

Get an overview of a distributed trace.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `organizationSlug` | string | Yes | Organization slug |
| `traceId` | string | Yes | 32-character hex trace ID |

### analyze_issue_with_seer

Run AI-powered root cause analysis on an issue. Returns code-level explanations and fix suggestions.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issueId` | string | Conditional | Issue ID. Requires `organizationSlug`. |
| `issueUrl` | string | Conditional | Full Sentry issue URL (alternative to `issueId`) |
| `organizationSlug` | string | Conditional | Required when using `issueId` |
| `instruction` | string | No | Custom instruction for the analysis |

### update_issue

Update an issue's status or assignment.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issueId` | string | Conditional | Issue ID. Requires `organizationSlug`. |
| `issueUrl` | string | Conditional | Full Sentry issue URL (alternative to `issueId`) |
| `organizationSlug` | string | Conditional | Required when using `issueId` |
| `status` | string | No | `resolved`, `resolvedInNextRelease`, `unresolved`, or `ignored` |
| `assignedTo` | string | No | `user:<id>` or `team:<id_or_slug>` |

### get_event_attachment

List or download attachments from a Sentry event.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `organizationSlug` | string | Yes | Organization slug |
| `projectSlug` | string | Yes | Project slug |
| `eventId` | string | Yes | Event ID |
| `attachmentId` | string | No | Specific attachment to download (omit to list all) |
