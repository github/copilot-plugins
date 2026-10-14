# Formula and Detector Catalog

All calculations are deterministic and versioned. The implementation does
not infer missing data, combine procurement scopes, or produce a weighted
risk score.

## Scope

Primary scope: records selected from the `production_contracts` view where
`procurement_method` is OTM, `contract_nature` is Works, and `noa_date` is on
or after the requested inclusive date (default `2025-09-15`). The view applies
its own collection, validation, deduplication, and exclusion rules. Reports
explicitly disclaim use of the view as a raw-source completeness denominator.

Blank currency may remain in the primary record population, but it is never
treated as BDT in value calculations. Comparisons include only peers with
usable Less% values under the same explicit currency and APP-match gates.

## Formulas

| ID | Definition | Interpretation |
|---|---|---|
| `LESS_PCT_V1` | `(contract_price - app_estimated_cost) / app_estimated_cost * 100` | Requires confirmed APP match, positive estimate, exact package number, OTM Works scope, and `contract_price_unit=BDT`; Decimal rounded HALF_UP to 0.01 percentage point. |
| `BDT_SUM_V1` | Sum positive contract prices with explicit BDT units | Reports usable count, award denominator, and excluded invalid/unknown-unit rows. |
| `CONCENTRATION_HHI_V1` | `sum((group amount / total amount) ** 2)` | Descriptive HHI over award counts or explicit BDT value; no alert threshold. Missing firm IDs are excluded and counted. |
| `DISTRIBUTION_V1` | Linear-interpolated p25, median, p75; MAD is median absolute deviation from median | Descriptive statistics only; every result carries its sample size. |
| `FIRM_HISTORY_DEVIATION_V1` | Selected Less% minus the median Less% of other awards for the same exact Tenderer ID | Percentage-point description; reports peer `n`, no threshold or score. |
| `PE_HISTORY_DEVIATION_V1` | Selected Less% minus the median of other awards with the same procuring-entity display name | Descriptive only; display name is not treated as a verified entity identifier. |
| `DISTRICT_DEVIATION_V1` | Selected Less% minus the median of other awards in the same district | Descriptive only; no threshold or score. |
| `APP_GATE_V1` | Confirmed match AND positive estimate AND exact APP package number | Eligibility/data consistency gate, not an accusation. |
| `DATE_ORDER_V1` | Expected completion date precedes contract signing date | Date consistency check only. |

## Review detectors

| ID | Rule | Status and limitation |
|---|---|---|
| `D001` | Confirmed Less% is strictly below -40% or strictly above +10% | Exclusive bounds from TSBD e-GP analysis guidance; review alert only. |
| `D015` | One exact Tenderer ID has multiple source-reported display names | Keeps variants separate and requests review; does not assert an identity collision. |
| `D016` | Duplicate `(tender_id, exact_package_no, contract_nature)` in the extracted view | Structural review alert. |
| `D018` | Expected completion date is earlier than signing date | Source-data consistency review. |
| `D019` | APP marked confirmed but its positive estimate or exact package key is unusable | Match-gate review; no Less% is calculated. |
| `D020` | Firm name, district, procuring-entity code, or price unit is missing | Missing-context notice; no inference about collection intent. |
| `D022` | Source snapshot hash or snapshot path is missing | Provenance gap; a source URL alone is not a retained snapshot. |
| `D026` | Firm Tenderer ID is missing | Identity remains unresolved; no name-based merge. |
| Upstream | Existing `audit_flags` row for an in-scope award | Reproduced as a database-sourced flag with its original reason/state; no reinterpretation. |

No ranking, participation-loss history, bidder responsiveness, credential
validity, source-staleness threshold, or composite risk score is calculated.
An absent record from this report is not evidence that the award did not
exist.
