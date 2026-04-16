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

Activated when a user asks to audit dependencies, check for known vulnerabilities, or find CVEs in project packages. Automatically detects the package manager in use (npm, Yarn, pnpm, pip, Cargo, bundler, Go modules, or .NET) and runs the appropriate native audit tool to surface vulnerable packages with severity levels and remediation guidance.
