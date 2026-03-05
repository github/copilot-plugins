# WorkIQ Plugin for GitHub Copilot

WorkIQ connects GitHub Copilot to Microsoft 365 Copilot, giving Copilot access to workplace intelligence grounded in your organization's data. Ask natural language questions about emails, meetings, documents, Teams messages, and people, and receive answers sourced directly from your Microsoft 365 environment.

## Overview

| | |
|---|---|
| **Provider** | Microsoft |
| **Type** | MCP Server + Skill |
| **Requires** | Microsoft 365 Copilot license |

## What WorkIQ Can Do

WorkIQ gives Copilot access to your organization's Microsoft 365 data through a single natural language interface:

- **Emails:** Find messages, summarize threads, surface action items
- **Meetings:** Retrieve decisions, summaries, and action items from calendar events
- **Documents:** Locate files across OneDrive and SharePoint
- **Teams messages:** Search conversations and channel discussions
- **People:** Identify experts, understand roles, and discover who owns what

## Skills

### `workiq`

Activates when you ask about anything that might exist in Microsoft 365. Example trigger phrases:

- "What did [person] say about..."
- "What are [person]'s priorities?"
- "What was decided in yesterday's meeting?"
- "Find emails from [person] about..."
- "Who is working on...?"
- "What's the status of...?"

## MCP Server

WorkIQ uses the `@microsoft/workiq` MCP server, launched automatically via `npx`:

```json
{
  "mcpServers": {
    "workiq": {
      "command": "npx",
      "args": ["-y", "@microsoft/workiq@latest", "mcp"],
      "tools": ["*"]
    }
  }
}
```

### Tool Reference

| Tool | Parameter | Type | Description |
|------|-----------|------|-------------|
| `ask_work_iq` | `question` | `string` (required) | A natural language question to ask Microsoft 365 Copilot |

**Example:**

```json
{
  "question": "What are the latest top of mind items from my manager?"
}
```

## Authentication

Authentication is handled automatically using the connected user's Microsoft 365 credentials. No additional configuration is required.

## Requirements

- A Microsoft 365 Copilot license associated with the authenticated user account
- Node.js (for `npx` to run the MCP server)
