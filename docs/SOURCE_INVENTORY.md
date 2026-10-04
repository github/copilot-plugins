# Repository Source Inventory

## Audit scope

- Repository: `github/copilot-plugins`
- Baseline commit: `fbf7c536a5c7af0c94ff5f528a39004c55129e6d`
- Baseline worktree: clean
- Scope: every tracked file in the selected checkout, plus an on-disk check excluding Git metadata.
- Machine-readable inventory: `data/source_inventory.json`

This is a frozen baseline inventory. The local analyzer plugin and audit
artifacts described below were created after the 30-file baseline was hashed
and are not represented as baseline source artifacts in the JSON inventory.

This checkout is the GitHub Copilot plugins collection. It contains 30 tracked files: 22 Markdown files, four JSON files, two PowerShell scripts, and two extensionless policy files. The local plugins are `spark` and `build-perf-cpp`; the marketplace also references plugins hosted in other repositories.

## e-GP source finding

No e-GP application, OTM award dataset, SQLite database, CSV/JSON award export, tender HTML report, collector, schema, or e-GP test suite is present in this checkout. Searches for `production_contracts`, `egp_data.db`, `TENDER_SOLUTION_BD`, `Firm Passport`, `OTM Works`, and `egp_data` returned no matches. The six HTML attachments and the separate tender workbench discussed in chat are not files in this repository and are therefore not treated as checked-in or authoritative repository sources.

Consequently, this inventory does not claim record counts, date coverage, entity coverage, or tender-data reliability for any repository file. The e-GP analytical scope and the requested passport, history, detector, and evidence features cannot be verified or implemented as a real data-backed engine from this checkout alone.

## Repository artifact groups

| Paths | Role and authority | Classification | e-GP records |
|---|---|---|---:|
| `.github\\plugin\\marketplace.json`, `.claude-plugin\\marketplace.json` | Marketplace source configuration and its Claude plugin pointer | System / operational | None |
| `plugins\\spark\\**` | Spark plugin overview, app-template skill, stack guidance, and design references | Reference / documentation | None |
| `plugins\\build-perf-cpp\\plugin.json`, `hooks\\hooks.json` | Build performance plugin and hook configuration | System / operational | None |
| `plugins\\build-perf-cpp\\scripts\\**` | Local vcperf installation and correlation-ID helper | Implementation / operational | None |
| `plugins\\build-perf-cpp\\skills\\**` | Build-performance analysis instructions and vcperf output/auth references | Reference / documentation | None |
| Root policy and contribution files | Repository governance and contributor guidance | Reference / documentation | None |

All checked-in artifacts are authoritative for the Copilot plugin repository content they define, but none is factual evidence about Bangladesh e-GP tenders, firms, PEs, awards, or credentials. File-level paths, types, sizes, SHA-256 hashes, classifications, purposes, and limitations are recorded in `data/source_inventory.json`.

## Writer and data-store review

There is no primary-record data store or tender-record write path in this repository. The build-perf plugin's `sessionStart` hook invokes `plugins\\build-perf-cpp\\scripts\\install-vcperf.ps1`, which uses NuGet to install/update vcperf under `%LOCALAPPDATA%\\vcperf\\build-perf-cpp`. Its `userPromptSubmitted` hook invokes `write-correlation-id.ps1`, which atomically replaces `%LOCALAPPDATA%\\vcperf\\correlation-id`. These operations are outside the repository and do not write tender or firm records.

## Reconciliation and overlap

- The Claude marketplace file points to the GitHub marketplace file; it is a pointer, not a second copy of e-GP data.
- Plugin READMEs, manifests, and skill documentation describe the same plugins at different levels. This is documentation/configuration overlap, not duplicated tender records.
- No source snapshots, normalized tender ledger, derived e-GP analytics, or exports exist in the checkout to reconcile.
- No database schema, migration, or reversible data migration is present.

## Post-audit local analyzer

The user selected a local-only analyzer plugin that calls an explicitly
configured read-only query helper. Its Python code, skill instructions,
formula catalog, and tests are analytical tooling, not primary e-GP records
or authoritative evidence. The plugin does not bundle the user's database,
runner, private exports, or separate HTML workbench. Refer to
`plugins/tsbd-egp-intelligence/README.md` and the updated
`docs/SELF_AUDIT_REPORT.md` for prototype capabilities and validation limits.
