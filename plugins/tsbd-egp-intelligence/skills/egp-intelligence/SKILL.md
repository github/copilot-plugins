---
name: egp-intelligence
description: >
  Run evidence-first, local analysis of Bangladesh e-GP OTM Works award data.
  Use when the user asks for a Tender Passport, exact-ID Firm Passport,
  award-history timeline, evidence graph, Less%/APP analysis, deterministic
  review detectors, data-quality self-audit, or to use this plugin's local
  analyzer. Requires the user's trusted read-only q.py helper and local data.
compatibility: Python 3.10+ and the user's separately installed read-only query runner.
---

# e-GP Intelligence (local analyzer)

## Safety and evidence rules

- Never copy tender databases, private exports, credentials, or the separate
  HTML workbench into this repository.
- Never edit the source database, query helper, workbench, or source snapshots.
- Run the bundled script only with the user's explicitly configured trusted
  read-only query helper. Do not guess a runner path or substitute an
  unrestricted database client.
- The runner uses SELECT-only statements against `production_contracts` and
  related audit tables. Temporary CSV exports are kept in an OS temporary
  directory and removed at completion. Reports go to stdout unless the user
  names an absolute output path outside the repository.
- Before writing a file report, explain that it contains tender/firm details
  and ask for a destination if none was given. Stdout is the default. Never
  overwrite an existing report without explicit `--overwrite` authorization.
- Do not present review alerts as proof of fraud, collusion, or wrongdoing.
  State the source evidence, calculation, threshold, sample size, and
  limitations.

## Workflow

1. Confirm that the request is for the primary OTM Works scope and that the
   installed read-only query helper is available. If the helper is not
   configured, ask for its path rather than searching for databases or
   guessing.
2. Use the configured `TSBD_EGP_QUERY_RUNNER` or the user-provided `--runner`.
   Default date is inclusive NOA `2025-09-15`; preserve or explicitly state
   any user-requested `--since` date.
3. For a selected record, use `--tender-id` and, where needed, exact
   `--package-no`. For a firm history, use exact `--firm-id`. Never match
   firms by display name.
4. Write outside the repository only when the user requests a file report.
   Otherwise, the script prints JSON to stdout.
5. Explain that `production_contracts` is a filtered view, not an independent
   completeness denominator. Separate NOT_RECORDED/NOT_FOUND from
   NOT_ATTEMPTED when source status fields allow; do not invent an attempt
   state when they do not.
6. Summarize findings with formula IDs, thresholds, peer counts, source
   hashes/URLs, database audit history, and limitations. The script does not
   infer participation, bidder rank, losses, responsiveness, licences, or a
   weighted risk score.

## Commands

```powershell
python .\plugins\tsbd-egp-intelligence\scripts\run_analysis.py
python .\plugins\tsbd-egp-intelligence\scripts\run_analysis.py --tender-id 123456 --package-no 'GOB/WORKS/01'
python .\plugins\tsbd-egp-intelligence\scripts\run_analysis.py --firm-id 'EXACT-TENDERER-ID'
```

Pass `--output 'C:\absolute\path\report.json'` to save a report outside this
repository. See the plugin README and formula catalog for setup and
interpretation.
