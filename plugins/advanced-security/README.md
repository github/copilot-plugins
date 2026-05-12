# Advanced Security

Security-focused plugin that brings GitHub Advanced Security capabilities into AI coding workflows through skills and MCP integrations.

## What it does

Advanced Security helps agents identify and prevent security risks during development by:

- Scanning code snippets, files, and git changes for potential secrets
- Using GitHub secret detection patterns through MCP tooling
- Supporting pre-commit checks to catch leaked credentials early
- Auditing project dependencies for known CVEs and security advisories across multiple ecosystems

## Skills

### `secret-scanning`

Activated when a user asks to check code, files, or git changes for exposed credentials. Uses the `run_secret_scanning` MCP tool to scan content for potential secrets before code is committed.

### `dependency-scanning`

Activated when a user asks to check repository dependencies for known vulnerabilities. Uses the GitHub MCP Server's Dependabot toolset along with the GitHub Advisory Database to audit lockfiles and verify that packages are free from known security issues before merging code.
