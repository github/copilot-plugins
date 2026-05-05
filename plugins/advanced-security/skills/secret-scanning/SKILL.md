---
name: secret-scanning
description: Scan files, content, or recent changes for secrets such as API keys, passwords, tokens, and credentials using the GitHub MCP Server's run_secret_scanning tool.
metadata:
  agents:
    supported:
      - GitHub Copilot Coding Agent
      - Cursor
      - Codex
      - Claude Code
    requires:
      mcp_server: github
      mcp_tool: run_secret_scanning
allowed-tools: Bash(git:*) Glob Grep Read
---

# Secret Scanning Skill

## Overview

This skill uses the GitHub MCP Server's `run_secret_scanning` tool to detect secrets in content, files, or git changes. It helps identify sensitive material like API keys, passwords, and credentials that could pose a security risk if exposed.

### What counts as a secret?

In this context, values that grant access, impersonate a user or service, sign requests, or decrypt protected data are generally treated as secrets.

Treat these as high-confidence secret material:

- Access tokens, API keys, and bearer credentials
- Passwords, database DSNs with embedded credentials, and SMTP auth values
- Private keys, signing keys, certificates with private key blocks, and SSH keys
- OAuth client secrets, refresh tokens, and webhook secrets
- Cloud credentials (AWS/GCP/Azure) and CI/CD deployment credentials

Prefer context, not just regex:

- Values near names like `password`, `token`, `secret`, `client_secret`, `private_key`, or `authorization` are higher risk
- Long high-entropy strings in config files, scripts, and test fixtures deserve review even if unlabeled
- Treat uncertain findings as sensitive until verified

Not everything that looks random is a secret. Example placeholders such as `YOUR_API_KEY_HERE`, obvious test stubs, and documented sample values can be false positives.

### Why this is important

This skill scans for secrets that could compromise security if leaked. A committed secret can persist in git history, trigger incident response, and block deployment at push protection checks.

**Important**: Only use this skill when a user explicitly asks to scan content or check for secrets. Do not run secret scanning unprompted or as part of general workflows.

## Common Scenarios

| User goal                              | How to respond       | Tools needed       |
| -------------------------------------- | -------------------- | ------------------ |
| Check a config snippet or code paste   | Scan as content      | MCP                |
| Check a specific file in the repo      | Read file, then scan | Read + MCP         |
| Check all staged changes before commit | Get diff, then scan  | Bash(git:\*) + MCP |

## Installation

### Prerequisites & Inputs

**GitHub MCP Server**: The skill requires the GitHub MCP Server with the `run_secret_scanning` tool enabled.

Configure in your MCP settings:

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  }
}
```

> **Note:** Cursor uses `servers` instead of `mcpServers` as the top-level key.

**Required information for scanning**:

- **Repository owner**: Usually available from `git remote get-url origin` or ask the user
- **Repository name**: Usually available from `git remote get-url origin` or ask the user
- **Content to scan**: Either a code snippet from the user, file content (read using the `Read` tool), or git diff output (from `git diff`)

If the user doesn't provide repository owner and repository name, ask for them before running the scan.

**What NOT to scan**: By default, avoid scanning large generated or vendor content (for example: `node_modules/`, build artifacts, compiled assets, or other machine-generated files) for performance and noise reduction. Files listed in `.gitignore` may still contain secrets (such as `.env` or local config), so only skip them if the user agrees; if the user explicitly asks to scan them, include them in the scan.

### Scan Content

**When to use**: The user provides text or code snippets they want checked for secrets.

**How**: Use the `run_secret_scanning` tool with the content as input (as a single-item array).

**Example**

```
You: Check if this config snippet has secrets
User provides:
DB_PASSWORD=MyP@ssw0rd123
API_KEY=abc123xyz

Agent: I'll scan that for secrets.

     ⚠️ Found 2 potential secret(s):
     1. DB_PASSWORD value looks like a password
     2. API_KEY value looks like an API key

     Consider replacing hardcoded values with environment variables.
```

### Scan File(s)

**When to use**: The user asks to check specific files in the repository for secrets.

**How**: Use the `Read` tool to get file contents, then pass them to `run_secret_scanning`.

**Example (secrets found)**

```
You: Check if config.py has secrets
Agent: I'll read and scan that file.

     ⚠️ Found 1 potential secret:
     - Line 10: database_password value looks like a password

     Suggestion: Move to environment variable or .env file.
```

**Example (no secrets found)**

```
You: Check if utils.js has any secrets
Agent: I'll read and scan that file.

     ✅ No secrets detected in utils.js
```

### Scan Staged Changes

**When to use**: The user wants to check git staged changes for secrets before committing.

**How**: Use `git diff --cached` to get staged content, then pass it to `run_secret_scanning`.

**Example (clean)**

```
You: Check my staged changes for secrets before I commit
Agent: I'll scan your staged changes.

     ✅ No secrets found in staged changes. Safe to commit.
```

**Example (secrets detected)**

```
You: Scan my staged changes
Agent: I'll check your staged changes.

     ⚠️ Found 1 potential secret in staged changes:
     - database.js line 5: password value looks like a credential

     Suggestion: Unstage that change, move the credential to env vars, and restage.
```

## How the Scan Works

When you call `run_secret_scanning`:

- **Input**: File contents to scan (passed as an array of strings), plus repository owner and name
- **Process**: GitHub's secret detection scans for patterns and context that match known secret types
- **Output**: List of potential secrets found with locations and confidence indicators

The tool works on content you provide. It doesn't need push access or special GitHub permissions.

## Scanning Transparency

### How Your Content Is Processed

When you request a scan, file contents are sent to GitHub's secret detection infrastructure. The scanning happens server-side against GitHub's known secret patterns. Scan results are returned without retaining the content on GitHub servers beyond the scan request.

### What to Do With Results

If secrets are found:

- **Obvious hardcoded values**: Move them to environment variables or `.env` files
- **Config files**: Check if `example.env` or documentation exists that shows the expected structure
- **Already committed**: If the secret was already pushed, credential rotation may be needed (outside this skill's scope)

If no secrets are found:

- The scan completed successfully
- Check the output format in the scan result to make sure coverage was complete

## Learn More

For more details on secret scanning, credential management, and GitHub security features:

- [GitHub Secret Scanning Docs](https://docs.github.com/en/code-security/secret-scanning): How to enable and use secret scanning on repositories
- [Credential Management Best Practices](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning): Guidance on handling credentials safely
- [GitHub Push Protection](https://docs.github.com/en/code-security/secret-scanning/working-with-push-protection): Preventing secrets from reaching your repository
