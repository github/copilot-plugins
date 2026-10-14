# TSBD e-GP Intelligence

A local Copilot skill and deterministic Python analyzer for Bangladesh e-GP
OTM Works awards. It can produce Tender and Firm Passports, award-history
timelines, an evidence graph, descriptive comparisons, a small review-only
detector set, and a view-relative self-audit.

This plugin contains no tender records, database, credentials, collector, or
copy of the user's workbench. It reads from a separately installed query
runner and writes reports only to stdout or to an explicitly selected
absolute path outside this repository. The runner itself must be trusted and
configured by the user.

## Requirements

- Python 3.10 or newer; no third-party Python packages are required.
- The user's installed, read-only `q.py` query helper.
- Access to the local e-GP data store through that helper.

Configure the runner path for the current shell:

```powershell
$env:TSBD_EGP_QUERY_RUNNER = 'C:\path\to\q.py'
```

Or provide `--runner` on every invocation. A summary report is printed to
stdout by default:

```powershell
python .\plugins\tsbd-egp-intelligence\scripts\run_analysis.py
```

For an identity-focused report, select a tender or exact firm ID. Write a
report only to an absolute path outside the repository; replacing an existing
report requires `--overwrite`.

```powershell
python .\plugins\tsbd-egp-intelligence\scripts\run_analysis.py `
  --tender-id 123456 --package-no 'GOB/WORKS/01' `
  --output 'C:\Users\you\Documents\egp-report.json'

python .\plugins\tsbd-egp-intelligence\scripts\run_analysis.py `
  --firm-id 'EXACT-TENDERER-ID' `
  --output 'C:\Users\you\Documents\firm-report.json'
```

The default inclusive NOA date is `2025-09-15`; set `--since YYYY-MM-DD` to
change it. The primary query is limited to `production_contracts`, OTM,
Works, and that date range. That view has its own collection and exclusion
rules and is **not** a denominator for raw-contract completeness.

The runner emits temporary CSV exports in an operating-system temporary
directory and removes them after report generation. Export and query SHA-256
hashes, formula version, and generation time are included in the report;
the database path is not. A report may still contain tender and firm
identifiers, public source URLs, and local source-snapshot paths; store and
share it accordingly.

## Scope and interpretation

- Less% is calculated only for an exact, confirmed APP package match with a
  positive estimate and explicitly BDT-denominated award price.
- Firm histories group by exact `firm_tenderer_id`. Name variants are shown
  for review; names are never fuzzy-merged.
- Comparisons are descriptive and include peer counts. No composite risk
  score or unsupported anomaly threshold is emitted.
- Detector outputs are review prompts, not findings of misconduct.
- Award-only records do not establish participation, losses, bidder rank, or
  responsiveness. The inspected schema has no credential-history table.
- No data from the separate HTML workbench or private database is bundled or
  modified by this plugin.

See [FORMULAS_AND_DETECTORS.md](FORMULAS_AND_DETECTORS.md) for the formula
definitions, detector rules, and limitations.
