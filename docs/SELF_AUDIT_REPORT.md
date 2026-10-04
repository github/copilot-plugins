# Repository Self-Audit

## Baseline scope and result

Audited the selected `github/copilot-plugins` checkout at baseline commit `fbf7c536a5c7af0c94ff5f528a39004c55129e6d`. The worktree was clean before the audit artifacts were added. All 30 tracked files were inventoried and hashed in `data/source_inventory.json`; no ignored or untracked application/data files were found in the baseline. This is a frozen baseline inventory, not a count of files added later.

This repository is a Copilot plugin collection, not the e-GP Tender Solution application or its data repository. The audit found two local plugins (`spark` and `build-perf-cpp`) and marketplace references to separately hosted plugins. It found no e-GP database, award records, data collector, tender workbench, HTML report, source snapshot, calculation engine, detector engine, or test framework.

## Requested capabilities: implementation status

| Capability | Status at baseline audit | Evidence / blocker |
|---|---|---|
| Tender Passport | Not implemented | No tender model or e-GP records |
| Firm Passport | Not implemented | No canonical firm IDs, aliases, or credential records |
| Historical Timeline | Not implemented | No event ledger or historical snapshots |
| Evidence Graph | Not implemented | No tender evidence IDs, normalized records, or source snapshots |
| Mathematical Detector Stack | Not implemented | No authoritative tender calculation engine or input records |
| Automatic Self-Audit | This repository-level audit is recorded here; an e-GP self-audit is not implemented | No e-GP code/data paths to inspect |

These are explicit gaps, not zero counts or negative findings about the external e-GP system. No synthetic production records or demo intelligence were created.

## Checks performed

1. Confirmed a clean baseline and recorded the commit.
2. Enumerated tracked files and inspected on-disk files while excluding Git metadata.
3. Searched the checkout for `production_contracts`, `egp_data.db`, `TENDER_SOLUTION_BD`, `Firm Passport`, `OTM Works`, and `egp_data`; no matches were found.
4. Checked file types and project structure. No SQLite/database, CSV award data, tender HTML, application dependency manifest, test directory, or application entry point was present.
5. Inspected the marketplace configuration, local plugin manifests, hooks, operational PowerShell scripts, plugin READMEs, and relevant skill references.
6. Reviewed repository write paths. The only observed writers are the build-perf plugin's local vcperf installation and correlation-ID update beneath `%LOCALAPPDATA%\\vcperf`; neither handles primary tender data.
7. Created and verified a baseline archive before adding audit documentation. Archive SHA-256: `382AEA0B6A812303BE8840AB10521632A640E6628FB251EF392E9EC7067CD56D`.

## Audit questions

| Question | Finding |
|---|---|
| Which files are unused? | No usage graph or plugin runtime was present to prove unused files. Do not infer that documentation is unused. |
| Which data is duplicated? | No tender data exists here. Marketplace pointer/configuration and plugin descriptions overlap by design; they are not record duplication. |
| Which records lack evidence? | No tender/firm records exist in this checkout to assess. |
| Which calculations lack tests? | No e-GP calculations or tests exist here. |
| Which detectors lack evidence? | No e-GP detectors exist here. |
| Which firm IDs have collisions? | Not assessable: no firm IDs or records. |
| Which licences have unknown validity? | Not assessable: no firm credential/licence data. |
| Which records are NOT_ATTEMPTED? | Not assessable: no e-GP collection-state model or records. |
| Which data is stale? | No e-GP source timestamps or datasets exist here. |
| Which primary OTM Works records are not analyzed? | The repository contains no defined primary universe or records. |
| Which analytical results are not reproducible? | No e-GP analytical results exist here. |
| Which alerts cannot be traced to source? | No e-GP alert system exists here. |
| Which code paths can write primary records? | None found. The build-perf operational scripts write only under `%LOCALAPPDATA%\\vcperf`. |
| Which migrations are not reversible? | No database migrations exist here. |
| Which documentation is inconsistent with implementation? | No e-GP implementation exists to compare against. Plugin documentation is outside the requested tender engine scope. |

## Follow-up: local analyzer plugin

After the baseline audit, the user selected a limited local analyzer plugin
that links to their separately installed read-only query runner. The
`plugins/tsbd-egp-intelligence/` prototype implements deterministic award
summaries and the six requested module patterns without bundling private
records:

| Capability | Current prototype status | Verification boundary |
|---|---|---|
| Tender Passport | Implemented for selected `production_contracts` awards | Requires a configured local runner and actual database use to validate live fields |
| Firm Passport | Exact `firm_tenderer_id` histories; name variants remain separate | No alias resolution, participation/loss history, or credentials |
| Historical Timeline | Joins matching audit-log, revision, and recovery events | Only the inspected related tables and matching records are included |
| Evidence Graph | Links awards, firms, sources, snapshots, calculations, source-health observations, and review results | Graph is built only for a selected analysis subset |
| Detector Stack | Deterministic data-consistency and review alerts; no weighted score | Must not be interpreted as misconduct; threshold and evidence limits are documented |
| Self-Audit | Counts fields and statuses within the filtered view | Does not claim independent raw-contract completeness |

Synthetic fixtures test the pure engine only. Unit tests and mocked runner tests
do not establish that the user's local query-helper schema or production data
has been validated end-to-end. The original database, query helper, source
snapshots, and separate workbench were not modified or copied into the repo.

## Safe implementation boundary

Do not describe the local analyzer as a complete e-GP system or a validated
production data pipeline until the configured read-only helper and source
schema have been checked against the user's actual environment. The earlier
attached HTML snapshots have conflicting windows and a failed integrity
panel; they are not substitutes for a reconciled primary record store.

The original plugin files and the separate user workbench were not modified during this audit.
