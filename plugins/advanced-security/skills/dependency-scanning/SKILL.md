---
name: dependency-scanning
description: Scan repository dependencies for known vulnerabilities using the GitHub MCP Server's Dependabot toolset and the GitHub Advisory Database. Use when asked to check dependency security, audit lockfiles, or verify packages before merging.
metadata:
  agents:
    supported:
      - GitHub Copilot Coding Agent
      - Cursor
      - Codex
      - Claude Code
    requires:
      mcp_server: github
      mcp_tool: check_dependency_vulnerabilities
allowed-tools: Bash(git:*) Glob Grep Read
---

# Dependency Vulnerability Scanning Skill

## Overview

This skill uses the GitHub MCP Server's Dependabot toolset and the `check_dependency_vulnerabilities` tool to find known vulnerabilities in project dependencies. It can check existing Dependabot alerts, look up specific packages, and verify new dependencies before merging.

### What counts as a dependency vulnerability?

Dependency vulnerabilities are known security flaws (CVEs) in third-party packages your project depends on. Examples include:
- Outdated npm packages with remote code execution flaws
- Python libraries with SQL injection vulnerabilities
- Go modules with denial-of-service weaknesses
- Ruby gems with authentication bypass issues
- Transitive dependencies inheriting upstream vulnerabilities

### Why this is important

A single vulnerable dependency can allow remote code execution in your application, enable denial-of-service attacks, expose sensitive data through library flaws, fail compliance audits (SOC 2, PCI-DSS, HIPAA), or introduce supply chain attack vectors.

**Important**: Only use this skill when a user explicitly asks to check dependencies or scan for vulnerabilities. Do not run dependency scanning unprompted or as part of general workflows.

## Common Scenarios

| User goal | How to respond | Tools needed |
|---|---|---|
| Check existing alerts | Check Dependabot Alerts | MCP only |
| Check a specific package | Look Up a Specific Package | MCP only |
| Verify new deps before pushing | Scan Local Branch Changes | Bash + MCP |
| Full dependency audit | Audit All Dependencies | Bash + MCP |
| Deterministic post-commit check | Post-Commit Safety Net | `dependabot` CLI + MCP |

**Lightweight vs. heavyweight operations**: For lightweight operations (checking alerts, looking up a package), proceed automatically. For heavyweight operations (downloading the Dependabot CLI, running a full repository audit), ask the user for confirmation before proceeding.

### Check Dependabot Alerts

**When to use**: The repository is hosted on GitHub and has Dependabot enabled.

**How**:

List all open alerts:

```
Use the list_dependabot_alerts tool:
  owner: <repo-owner>
  repo: <repo-name>
  state: open
```

This returns all open Dependabot alerts including package name, ecosystem, severity, CVE identifiers, and patched version (if available).

Get details on a specific alert:

```
Use the get_dependabot_alert tool:
  owner: <repo-owner>
  repo: <repo-name>
  alert_number: <number>
```

This returns the vulnerability description, CVSS score, affected version range, fixed version, and advisory links.

**Fallback**: If Dependabot is not enabled on the repository, fall back to "Look Up a Specific Package" below.

**Example (vulnerabilities found)**
```
You: Check my repo for dependency vulnerabilities
Agent: Fetching Dependabot alerts...
       Found 3 open alerts:
       1. Critical — lodash@4.17.15 (CVE-2021-23337: Command Injection) → Fix: 4.17.21
       2. High — express@4.17.1 (CVE-2024-29041: Open Redirect) → Fix: 4.18.2
       3. Medium — axios@0.21.1 (CVE-2021-3749: ReDoS) → Fix: 0.21.2
```

**Example (no alerts)**
```
You: Check my repo for dependency vulnerabilities
Agent: Fetching Dependabot alerts...
       ✅ No open Dependabot alerts found for this repository.
```

### Look Up a Specific Package

**When to use**: Checking a specific package/version before adding it, or when Dependabot is not available.

**How**: Use the `check_dependency_vulnerabilities` tool with a single dependency:

```
Use the check_dependency_vulnerabilities tool:
  owner: <repo-owner>
  repo: <repo-name>
  dependencies:
    - name: <package-name>
      version: <version>
      ecosystem: <ecosystem>
```

Supported ecosystem values: `npm`, `pip`, `maven`, `nuget`, `composer`, `pub`, `actions`, `bundler`, `gomod`, `cargo`, `hex`, `swift`.

The tool checks for high-severity, critical-severity, and malware advisories in the GitHub Advisory Database.

**Example**:
```
You: Is lodash 4.17.15 safe to use?
Agent: ⚠️ lodash@4.17.15 has 1 known vulnerability:
       - CVE-2021-23337 (Critical): Command Injection via template function
         Fixed in: 4.17.21 — Recommendation: Update to lodash>=4.17.21
```

### Scan Local Branch Changes

**When to use**: The current branch adds or updates dependencies and you want to check them before pushing.

**Steps**:
1. Detect which dependency files changed on this branch
2. For each changed manifest/lockfile, parse the new or updated dependencies
3. Check them with `check_dependency_vulnerabilities` (batch up to 30 per call)

**Step 1 — Detect changed dependency files**:

```bash
# Check which dependency files changed on the current branch vs base
# Filter out vendor, build, and generated directories
git diff --name-only origin/main...HEAD \
  | grep -v -E '(^|/)vendor/' \
  | grep -v -E '(^|/)node_modules/' \
  | grep -v -E '(^|/)(build|dist|out|target)/' \
  | grep -E \
  '(package\.json|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|requirements\.txt|Pipfile\.lock|poetry\.lock|pyproject\.toml|setup\.py|go\.mod|go\.sum|Gemfile|Gemfile\.lock|Cargo\.toml|Cargo\.lock|pom\.xml|build\.gradle|build\.gradle\.kts|.*\.csproj|packages\.config|composer\.json|composer\.lock|pubspec\.yaml|pubspec\.lock|Package\.swift|Package\.resolved)'
```

If no dependency files changed, no further scanning is needed — exit early.

**Example (clean)**
```
You: Check if the new dependencies on this branch are safe
Agent: Scanning package-lock.json changes...
       ✅ All new dependencies are clean — no known vulnerabilities found.
```

**Example (vulnerabilities found)**
```
You: Check if the new dependencies on this branch are safe
Agent: Scanning package-lock.json changes...
       ⚠️ Found 1 vulnerability in newly added dependencies:
       - lodash@4.17.15: Critical — CVE-2021-23337 (Command Injection) → Fix: 4.17.21
```

### Audit All Dependencies

**When to use**: Running a full supply chain security audit of the entire project.

> **Ask the user for confirmation before proceeding.** Example: "This will scan all dependency files in the repository. For large projects this may take a few minutes. Would you like me to proceed?"

**Step 1 — Discover all dependency files**:

**Supported ecosystems and manifest files**:
- **npm**: `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
- **pip**: `requirements.txt`, `Pipfile.lock`, `poetry.lock`, `pyproject.toml`, `setup.py`
- **Go**: `go.mod`, `go.sum`
- **RubyGems**: `Gemfile`, `Gemfile.lock`
- **Rust**: `Cargo.toml`, `Cargo.lock`
- **Maven**: `pom.xml`, `build.gradle`, `build.gradle.kts`
- **NuGet**: `*.csproj`, `packages.config`, `*.deps.json`
- **Composer**: `composer.json`, `composer.lock`
- **Pub**: `pubspec.yaml`, `pubspec.lock`
- **Swift**: `Package.swift`, `Package.resolved`

Search up to 4 directories deep, excluding `node_modules/`, `.git/`, and `vendor/`.

**Step 2 — Parse and check dependencies**:

For each discovered manifest/lockfile, parse the dependency names, versions, and ecosystem, then check them with `check_dependency_vulnerabilities` (batch up to 30 per call):

```
Use the check_dependency_vulnerabilities tool:
  owner: <repo-owner>
  repo: <repo-name>
  dependencies:
    - name: <package-1>
      version: <version-1>
      ecosystem: <ecosystem>
    - name: <package-2>
      version: <version-2>
      ecosystem: <ecosystem>
    ...
```

Map manifest files to ecosystem values: `package.json`/`yarn.lock`/`pnpm-lock.yaml` → `npm`, `requirements.txt`/`Pipfile.lock`/`poetry.lock`/`pyproject.toml` → `pip`, `go.mod`/`go.sum` → `gomod`, `Gemfile`/`Gemfile.lock` → `bundler`, `Cargo.toml`/`Cargo.lock` → `cargo`, `pom.xml`/`build.gradle` → `maven`, `*.csproj`/`packages.config` → `nuget`, `composer.json`/`composer.lock` → `composer`, `pubspec.yaml`/`pubspec.lock` → `pub`, `Package.swift`/`Package.resolved` → `swift`.

**Example**
```
You: Audit all dependencies in this repository for security issues
Agent: Discovering dependency files...
       Found: package-lock.json, poetry.lock, go.sum
       Scan Results:
       - npm: 2 vulnerabilities (1 high, 1 medium)
       - pip: 0 vulnerabilities
       - Go: 1 vulnerability (1 low)
       Total: 3 vulnerabilities across 3 ecosystems
```

### Post-Commit Safety Net (Advanced)

**When to use**: After the agent commits changes, before merge — a deterministic backstop that ensures nothing slips through.

> **If the Dependabot CLI is not already installed, ask the user before downloading it.** Example: "This check requires the Dependabot CLI (~50MB). Would you like me to download and install it?"

#### Pipeline Architecture

```
┌──────────────────────────────┐
│  1. Detect Changed Manifests │  From git diff; filter vendor/build
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  2. Build Dependency Graphs  │  Base + HEAD using `dependabot graph`
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  3. Diff Dependency Graphs   │  Find newly added/updated direct deps
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────────────────────┐
│  4. check_dependency_vulnerabilities tool    │  Query GitHub Advisory Database
└──────────────┬───────────────────────────────┘
               ▼
┌──────────────────────────────┐
│  5. Report & Re-iterate      │  Report vulns; agent iterates to fix
└──────────────────────────────┘
```

#### Step 1: Detect Changed Manifest/Lockfiles

Use the same `git diff` command from "Scan Local Branch Changes" above. If no dependency files changed, exit early.

#### Step 2: Build Before/After Dependency Graphs

Map changed files to Dependabot CLI ecosystem values (using the ecosystem table in "Audit All Dependencies" above — e.g., `package.json` → `npm_and_yarn`, `go.mod` → `go_modules`, `Gemfile` → `bundler`).

```bash
ECOSYSTEM="npm_and_yarn"  # set based on the mapping table above

# Use a git worktree to get the base commit without modifying the working tree
git worktree add /tmp/base-ref origin/main --detach 2>/dev/null

# Build dependency graph at the base commit (before changes)
dependabot graph $ECOSYSTEM /tmp/base-ref --output=/tmp/before-deps.json

# Build dependency graph at current HEAD (after changes)
dependabot graph $ECOSYSTEM . --output=/tmp/after-deps.json

# Clean up the worktree
git worktree remove /tmp/base-ref 2>/dev/null
```

> **Note:** Replace `origin/main` with your base branch. You can extract `<owner>/<repo>` from your git remote: `git remote get-url origin | sed -E 's|.*github\.com[:/]([^/]+/[^/]+?)(\.git)?$|\1|'`

#### Step 3: Diff New/Updated Dependencies

The `dependabot graph` output is a JSON object with a `dependencies` array. Each entry has `name`, `version`, and `relationship` (`"direct"` or `"transitive"`).

```bash
python3 -c "
import json

# Load before/after dependency graphs produced by 'dependabot graph'
with open('/tmp/before-deps.json') as f:
    before_data = json.load(f)
with open('/tmp/after-deps.json') as f:
    after_data = json.load(f)

# Extract direct dependencies from the graph output
def get_direct_deps(data):
    deps = {}
    for dep in data.get('dependencies', []):
        if dep.get('relationship') == 'direct':
            deps[dep['name']] = dep['version']
    return deps

before = get_direct_deps(before_data)
after = get_direct_deps(after_data)

# Find new or version-changed direct dependencies
changed = []
for name, version in after.items():
    if name not in before:
        changed.append({'name': name, 'version': version, 'change': 'added'})
    elif before[name] != version:
        changed.append({'name': name, 'version': version, 'change': f'updated from {before[name]}'})

print(json.dumps(changed, indent=2))
print(f'\n{len(changed)} direct dependencies added or updated')
"
```

#### Step 4: Check Against Advisory Database

Feed the changed dependencies from Step 3 into the `check_dependency_vulnerabilities` tool (batch up to 30 per call):

```
Use the check_dependency_vulnerabilities tool:
  owner: <repo-owner>
  repo: <repo-name>
  dependencies:
    - name: <changed-dep-1>
      version: <version>
      ecosystem: <ecosystem>
    - name: <changed-dep-2>
      version: <version>
      ecosystem: <ecosystem>
    ...
```

Map the Dependabot CLI ecosystem to `check_dependency_vulnerabilities` ecosystem values: `npm_and_yarn` → `npm`, `pip` → `pip`, `go_modules` → `gomod`, `bundler` → `bundler`, `cargo` → `cargo`, `maven` → `maven`, `nuget` → `nuget`, `composer` → `composer`, `pub` → `pub`, `swift` → `swift`.

#### Step 5: Report Vulnerabilities and Re-Iterate

If vulnerabilities are found, report them back to the agent with specific remediation instructions. The agent should fix the vulnerable dependencies and the check runs again — repeating until all newly-introduced vulnerabilities are resolved.

```
Vulnerable dependencies detected in your changes:

1. lodash@4.17.15 (added in package.json)
   - GHSA-35jh-r3h4-6jhm: Command Injection (Critical, CVSS 9.8)
   - Fixed in: 4.17.21
   - Action: Update to lodash@4.17.21 in package.json

2. requests@2.25.0 (added in requirements.txt)
   - GHSA-j8r2-6x86-q33q: Proxy-Authorization header leak (Medium, CVSS 6.1)
   - Fixed in: 2.31.0
   - Action: Update to requests>=2.31.0 in requirements.txt

Please fix these vulnerabilities and commit the changes. The check will re-run automatically.
```

> **Key insight**: Running this as a *post-result* hook (after the agent commits) is more reliable than a pre-commit hook. Pre-commit hooks cause agents to add warnings to the PR description rather than actually fixing the vulnerability.

**Example**
```
[Agent finishes work and commits changes]
Hook: Detecting changed dependency files...
      Changed: package-lock.json
      Building dependency graphs with `dependabot graph`...
      3 direct dependencies added: lodash (new) 4.17.15, axios 0.21.1→1.6.0, express 4.17.1→4.18.2
      1 vulnerability found — requesting agent fix:
      - Critical — lodash@4.17.15 (GHSA-35jh-r3h4-6jhm: Command Injection → Fix: 4.17.21)
Agent: Updating package.json to use lodash@4.17.21... ✅ Fixed. Committing changes.
Hook: ✅ All newly-introduced dependencies are clean.
```

## Reporting Results

The `check_dependency_vulnerabilities` tool returns a formatted report with ✓/⚠ per dependency, GHSA IDs, severity, and summaries. Present this output directly to the user, supplemented with remediation guidance.

### Severity Legend

| Severity | CVSS Score | Action |
|----------|-----------|--------|
| Critical | 9.0–10.0 | Fix immediately |
| High | 7.0–8.9 | Fix as soon as possible |
| Medium | 4.0–6.9 | Schedule fix |
| Low | 0.1–3.9 | Track and fix when convenient |

For automated remediation, only block on **Critical** and **High** severity. Medium and low issues should be reported but should not block the agent's work. Focus remediation on direct dependencies (listed in manifests). Transitive dependencies require updating the parent to a version that pulls in the patched transitive dep, or adding `resolutions` (Yarn), `overrides` (npm), or equivalent. For each vulnerability, provide the exact package and target version, the fix command, any breaking-change warnings, and a mitigation if no patch exists.


## Installation

### Prerequisites & Inputs

**Optional — Dependabot CLI**: Required for the Post-Commit Safety Net use case. Ask the user before downloading.

   ```bash
   # Check if already installed
   which dependabot 2>/dev/null && dependabot --version

   # Install via Go
   go install github.com/dependabot/cli/cmd/dependabot@latest

   # Or download a prebuilt binary from GitHub releases (Linux/macOS/Windows, amd64/arm64)
   # https://github.com/dependabot/cli/releases
   PLATFORM="linux"   # or "darwin" or "windows"
   ARCH="amd64"       # or "arm64"
   VERSION=$(curl -s https://api.github.com/repos/dependabot/cli/releases/latest | grep tag_name | cut -d '"' -f4)
   curl -fsSL -o dependabot.tar.gz \
     "https://github.com/dependabot/cli/releases/download/${VERSION}/dependabot-${VERSION}-${PLATFORM}-${ARCH}.tar.gz"
   tar xzf dependabot.tar.gz
   chmod +x dependabot
   mv dependabot /usr/local/bin/
   ```

## Scanning Transparency

### How your data is processed

- **Dependabot alerts approach**: Only the repository owner/name is sent to the GitHub MCP Server. Dependency data is already stored by GitHub.
- **Vulnerability check approach**: Package names, versions, and ecosystems are sent to the GitHub MCP Server's `check_dependency_vulnerabilities` tool, which queries the GitHub Advisory Database.
- **Dependabot CLI approach**: Dependency information is processed locally. Network requests go to package registries.

## Learn More

For more details on dependency security, vulnerability scanning, and GitHub security features:
- [GitHub Dependabot Documentation](https://docs.github.com/en/code-security/dependabot): How to configure and use Dependabot for automated dependency updates
- [GitHub Advisory Database](https://github.com/advisories): Browse known vulnerabilities across ecosystems
- [Dependabot CLI](https://github.com/dependabot/cli): Run Dependabot locally for offline dependency analysis
- [GitHub MCP Server](https://github.com/github/github-mcp-server): The MCP server that powers this skill's integration
- [GHSA (GitHub Security Advisories)](https://docs.github.com/en/code-security/security-advisories): Understanding GitHub Security Advisory identifiers
