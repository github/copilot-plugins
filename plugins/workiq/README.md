# WorkIQ

Workplace intelligence plugin that connects AI agents to Microsoft 365 Copilot, providing access to organizational data from Outlook, Teams, SharePoint, OneDrive, and Calendar.

Powered by the [`@microsoft/workiq`](https://github.com/microsoft/work-iq-mcp) MCP server.

> ⚠️ **Public Preview:** Features and APIs may change.

## What it does

WorkIQ grounds AI assistance in real workplace context by querying Microsoft 365 data sources. It enables agents to answer questions about:

| Data type | Example questions |
| --- | --- |
| **Emails** | "What did John say about the proposal?" |
| **Meetings** | "What's on my calendar tomorrow?" |
| **Documents** | "Find my recent PowerPoint presentations" |
| **Teams** | "Summarize today's messages in the Engineering channel" |
| **People** | "Who is working on Project Alpha?" |

## Skills

### `workiq`

Activated when a user asks about workplace context — what someone said, meeting outcomes, document locations, team priorities, or organizational knowledge. Uses the `ask_work_iq` MCP tool to query Microsoft 365 Copilot with natural language questions.

## MCP server

WorkIQ includes an MCP server configuration (`.mcp.json`) that runs the [`@microsoft/workiq`](https://www.npmjs.com/package/@microsoft/workiq) package. Authentication is automatic using the connected user's existing Microsoft 365 credentials.

## Prerequisites

- **Node.js 18+** — [Download from nodejs.org](https://nodejs.org/)
- **Microsoft 365 account** with Copilot access

## Admin consent

To access Microsoft 365 tenant data, the WorkIQ MCP server needs permissions that require administrative rights on the tenant. On first access, a consent dialog appears. If you are not an administrator, contact your tenant administrator to grant access.

For more information, see Microsoft's [User and Admin Consent Overview](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/user-admin-consent-overview).
