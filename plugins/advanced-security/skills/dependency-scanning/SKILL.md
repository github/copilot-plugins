---
name: dependency-scanning
description: Scan project dependencies for known CVEs and security vulnerabilities using ecosystem-native audit tools (npm audit, yarn audit, pnpm audit, pip-audit, cargo audit, govulncheck, bundler-audit, dotnet list package).
metadata:
  agents:
    supported:
      - GitHub Copilot Coding Agent
      - Cursor
      - Codex
      - Claude Code
allowed-tools: Bash(npm:*) Bash(yarn:*) Bash(pnpm:*) Bash(pip-audit:*) Bash(cargo:*) Bash(govulncheck:*) Bash(bundler-audit:*) Bash(dotnet:*) Bash(git:*) Bash(gh:*) Bash(curl:*) Glob Read
---

# Dependency Scanning Skill

## Overview

This skill detects known CVEs and security vulnerabilities in project dependencies by running the audit tool native to each package ecosystem. It supports JavaScript, Python, Rust, Ruby, Go, and .NET projects -- including multi-ecosystem monorepos.

### What counts as a vulnerable dependency?

A dependency is flagged when it has a publicly disclosed vulnerability that is catalogued in a security advisory database (the National Vulnerability Database, GitHub Advisory Database, OSV, RustSec Advisory Database, etc.).

Treat these as actionable findings:

- **Critical / High severity**: Actively exploitable vulnerabilities, remote code execution, privilege escalation. Prioritise these.
- **Moderate severity**: Vulnerabilities with limited exploitability, denial-of-service, or that require specific preconditions.
- **Low / Informational severity**: Minor issues, speculative attack vectors, or things requiring local access. Still worth reviewing but lower urgency.

Not every flagged package represents actual risk to the project. Context matters:

- A vulnerability in a **dev-only** dependency that never runs in production carries much lower risk.
- A vulnerability requiring **specific user input or environment conditions** may not be reachable in the current application.
- Some advisories are **disputed or already mitigated** upstream -- check the advisory link before escalating.

### Why this is important

Supply-chain attacks and dependency vulnerabilities are one of the most common entry points for security incidents. Running a dependency audit regularly -- and especially before releases -- helps catch known bad versions early, when the fix is simply upgrading a package.

**Important**: Only run this skill when the user explicitly asks to scan dependencies or check for vulnerabilities. Do not trigger it as part of unrelated general workflows.

## Ecosystem Support

| Ecosystem        | Lock / manifest file(s)                                       | Audit tool              | Availability                       |
| ---------------- | ------------------------------------------------------------- | ----------------------- | ---------------------------------- |
| npm              | `package-lock.json`, `npm-shrinkwrap.json`                    | `npm audit`             | Built-in (npm >= 6)                 |
| Yarn Classic (v1) | `yarn.lock` (no `.yarnrc.yml`)                               | `yarn audit`            | Built-in                           |
| Yarn Berry (v2+) | `yarn.lock` + `.yarnrc.yml`                                   | `yarn npm audit`        | Built-in                           |
| pnpm             | `pnpm-lock.yaml`                                              | `pnpm audit`            | Built-in                           |
| Python           | `Pipfile.lock`, `pyproject.toml`, `requirements*.txt`         | `pip-audit`             | Install: `pip install pip-audit`   |
| Rust             | `Cargo.lock`                                                  | `cargo audit`           | Install: `cargo install cargo-audit` |
| Ruby             | `Gemfile.lock`                                                | `bundler-audit`         | Install: `gem install bundler-audit` |
| Go               | `go.sum`                                                      | `govulncheck`           | Install: `go install golang.org/x/vuln/cmd/govulncheck@latest` |
| .NET             | `*.csproj`, `*.sln`, `packages.config`                        | `dotnet list package`   | Built-in (.NET SDK >= 6)            |

## Common Scenarios

| User goal                                           | How to respond                                                    |
| --------------------------------------------------- | ----------------------------------------------------------------- |
| "Scan my project for vulnerabilities"               | Auto-detect ecosystem(s), run audit, report findings              |
| "Check npm dependencies for CVEs"                   | Run `npm audit --json`, parse and report                          |
| "Are there any critical vulnerabilities?"           | Run audit, filter for critical/high severity, surface those first |
| "How do I fix the vulnerabilities you found?"       | Show the fix command (e.g. `npm audit fix`) per finding           |
| "Scan only production dependencies"                 | Pass `--production` / `--prod` flag where supported               |

## Detecting the Ecosystem

Before running any audit, use `Glob` to identify which ecosystems are present. A project may have multiple.

```
Detection order (check all, not just the first match):
1. package-lock.json or npm-shrinkwrap.json  -> npm
2. yarn.lock + .yarnrc.yml present           -> Yarn Berry (v2+): yarn npm audit
   yarn.lock without .yarnrc.yml             -> Yarn Classic (v1): yarn audit
3. pnpm-lock.yaml                            -> pnpm
4. Cargo.lock                                -> cargo audit
5. Gemfile.lock                              -> bundler-audit
6. go.sum                                    -> govulncheck
7. Pipfile.lock / pyproject.toml / requirements*.txt -> pip-audit
8. *.csproj / *.sln / packages.config        -> dotnet list package --vulnerable
```

If multiple ecosystems are detected, run each audit in turn and aggregate the results. Monorepos with workspaces are common -- run from the relevant workspace root if applicable.

## Running the Audit

### JavaScript -- npm

```bash
npm audit --json 2>/dev/null
```

To auto-fix non-breaking upgrades:

```bash
npm audit fix
```

To fix breaking upgrades (bumps major versions -- review carefully):

```bash
npm audit fix --force
```

To scan production dependencies only:

```bash
npm audit --json --production 2>/dev/null
```

### JavaScript -- Yarn Classic (v1)

```bash
yarn audit --json 2>/dev/null
```

Yarn v1 does not have an automatic fix command; fix by upgrading specific packages in `package.json`.

### JavaScript -- Yarn Berry (v2+)

```bash
yarn npm audit --json 2>/dev/null
```

### JavaScript -- pnpm

```bash
pnpm audit --json 2>/dev/null
```

To fix:

```bash
pnpm audit --fix
```

To scan production dependencies only:

```bash
pnpm audit --json --prod 2>/dev/null
```

### Python -- pip-audit

```bash
pip-audit -f json 2>/dev/null
```

If `pip-audit` is not installed, inform the user:

> `pip-audit` is not installed. Install it with: `pip install pip-audit`

To scan a specific requirements file:

```bash
pip-audit -f json -r requirements.txt 2>/dev/null
```

### Rust -- cargo audit

```bash
cargo audit --json 2>/dev/null
```

If `cargo audit` is not installed, inform the user:

> `cargo audit` is not installed. Install it with: `cargo install cargo-audit`

To fix (updates `Cargo.toml` where possible):

```bash
cargo audit fix
```

### Ruby -- bundler-audit

First update the advisory database, then scan:

```bash
bundler-audit update && bundler-audit check --format json 2>/dev/null
```

If `bundler-audit` is not installed, inform the user:

> `bundler-audit` is not installed. Install it with: `gem install bundler-audit`

### Go -- govulncheck

```bash
govulncheck -json ./... 2>/dev/null
```

If `govulncheck` is not installed, inform the user:

> `govulncheck` is not installed. Install it with: `go install golang.org/x/vuln/cmd/govulncheck@latest`

### .NET -- dotnet list package

```bash
dotnet list package --vulnerable 2>/dev/null
```

For JSON output (.NET SDK >= 8):

```bash
dotnet list package --vulnerable --format json 2>/dev/null
```

---

## Presenting Results

Structure your report clearly. Lead with a summary, then detail each finding.

### Summary line (always show)

```
Dependency scan complete -- X vulnerabilities found (A critical, B high, C moderate, D low)
```

If nothing is found:

```
No known vulnerabilities found in your dependencies.
```

### Per-finding format

For each vulnerability, show:

```
[SEVERITY] package-name@affected-version
  CVE: CVE-YYYY-NNNNN (or advisory ID)
  Description: <one-line summary>
  Fix: Upgrade to package-name@fixed-version
  Advisory: <URL if available>
```

### Severity ordering

Always present findings in this order: **Critical -> High -> Moderate -> Low -> Informational**

### Example output (npm)

```
Dependency scan complete -- 3 vulnerabilities found (1 critical, 1 high, 1 moderate)

[CRITICAL] lodash@4.17.15
  CVE: CVE-2021-23337
  Description: Command injection via template
  Fix: npm audit fix  (upgrades to lodash@4.17.21)
  Advisory: https://github.com/advisories/GHSA-35jh-r3h4-6jhm

[HIGH] axios@0.21.0
  CVE: CVE-2021-3749
  Description: Inefficient regular expression complexity
  Fix: npm audit fix  (upgrades to axios@0.21.2)
  Advisory: https://github.com/advisories/GHSA-cph5-m8f7-6c5x

[MODERATE] glob-parent@3.1.0
  CVE: CVE-2020-28469
  Description: Regular expression denial of service
  Fix: npm audit fix  (upgrades to glob-parent@5.1.2)
  Advisory: https://github.com/advisories/GHSA-ww39-953v-wcq6

Tip: Run `npm audit fix` to automatically resolve all 3 issues.
```

### Example output (no vulnerabilities)

```
No known vulnerabilities found in your npm dependencies.
   Scanned: 312 packages (189 direct, 123 transitive)
```

---

## Handling Errors and Edge Cases

| Situation                                              | What to do                                                                                       |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| Audit tool not installed                               | Inform the user and provide the install command. Do not silently skip.                           |
| No lock file found                                     | Inform the user: "No lock file detected. Run the package manager install command first."         |
| `npm audit` returns exit code 1 (vulnerabilities exist)| This is expected -- parse the JSON output normally.                                               |
| Network error / registry unreachable                   | Report the error and suggest retrying or checking connectivity.                                  |
| Production-only scan requested                         | Use `--production` / `--prod` flags where supported; note in the report which scope was scanned. |
| `yarn audit` exits non-zero even with no issues        | Check the JSON output; a non-zero exit alone is not sufficient to indicate vulnerabilities.       |
| `govulncheck` output references only stdlib            | Mention that no third-party vulnerabilities were found but stdlib entries exist.                  |

---

## Remediation Guidance

After reporting findings, always include the appropriate fix command(s):

| Ecosystem        | Fix command                                                               |
| ---------------- | ------------------------------------------------------------------------- |
| npm              | `npm audit fix` (or `npm audit fix --force` for breaking changes)         |
| Yarn Classic     | Manually update `package.json` and re-run `yarn install`                  |
| Yarn Berry       | `yarn up <package>`                                                        |
| pnpm             | `pnpm audit --fix` or `pnpm update <package>`                             |
| Python           | `pip install --upgrade <package>`                                         |
| Rust             | `cargo update <package>` or `cargo audit fix`                             |
| Ruby             | `bundle update <gem>`                                                      |
| Go               | `go get <module>@<fixed-version>` + `go mod tidy`                         |
| .NET             | `dotnet add package <package> --version <fixed-version>`                  |

If a fix is not yet available (no patched version released), clearly state:

> Warning: No fix is currently available for `package@version`. Consider evaluating whether this package can be replaced, isolated, or whether the vulnerable code path is reachable in your project.

---

## Scope and Limitations

- This skill runs **locally** using the audit tools available in the development environment. It does not require GitHub credentials or network access to GitHub (though some tools query external advisory databases).
- Results reflect the **advisory databases** used by each tool at the time of the scan. Keep audit tools and their databases up to date for best coverage.
- This skill does **not** modify any files automatically unless the user explicitly asks for a fix. Always confirm before running a destructive fix command.
- **Dev dependencies**: By default, scan all dependencies including dev. If the user only wants production scope, pass the appropriate flag and note it in the report.

## Optional: Dependabot Alerts (GitHub repositories)

If the project lives on GitHub and the user wants to cross-reference local audit results with what GitHub already knows, you can pull open Dependabot alerts directly. This is optional -- run it only when the user asks, or to enrich a local scan.

### Prerequisites

- The repository must have **Dependabot alerts** enabled (Settings -> Code security -> Dependabot alerts).
- You need either the **GitHub CLI** (`gh`) authenticated, or a token with `security_events` scope (or `repo` for private repos).

Infer `{owner}` and `{repo}` from `git remote get-url origin` if not provided by the user.

### Via GitHub CLI

```bash
gh api repos/{owner}/{repo}/dependabot/alerts \
  --paginate \
  --jq '.[] | select(.state=="open") | {severity: .security_vulnerability.severity, package: .security_vulnerability.package.name, affected: .security_vulnerability.vulnerable_version_range, fixed_in: .security_vulnerability.first_patched_version.identifier, summary: .security_advisory.summary, url: .html_url}'
```

To surface only critical and high alerts:

```bash
gh api repos/{owner}/{repo}/dependabot/alerts \
  --paginate \
  --jq '[.[] | select(.state=="open" and (.security_vulnerability.severity == "critical" or .security_vulnerability.severity == "high"))]'
```

### Via REST API

```bash
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/{owner}/{repo}/dependabot/alerts?state=open&per_page=100"
```

### Presenting Dependabot results

Clearly label alerts as coming from GitHub so the user knows the source:

```
Dependabot alerts (GitHub) -- 2 open alerts

[CRITICAL] package-name (affected: < 2.0.1)
  Fixed in: 2.0.1
  https://github.com/{owner}/{repo}/security/dependabot/1

[HIGH] another-package (affected: >= 1.0.0, < 1.4.3)
  Fixed in: 1.4.3
  https://github.com/{owner}/{repo}/security/dependabot/2
```

### When Dependabot alerts are unavailable

If the API returns 403 or 404, inform the user:

> Warning: Dependabot alerts could not be retrieved. Either the feature is not enabled for this repository, or the token lacks the `security_events` permission. Enable Dependabot alerts under **Settings -> Code security -> Dependabot alerts**.

---

## Learn More
- [pnpm audit docs](https://pnpm.io/cli/audit)
- [pip-audit on PyPI](https://pypi.org/project/pip-audit/)
- [cargo-audit on crates.io](https://crates.io/crates/cargo-audit)
- [bundler-audit on GitHub](https://github.com/rubysec/bundler-audit)
- [govulncheck docs](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck)
- [GitHub Advisory Database](https://github.com/advisories)
- [National Vulnerability Database (NVD)](https://nvd.nist.gov/)
- [OSV -- Open Source Vulnerabilities](https://osv.dev/)
