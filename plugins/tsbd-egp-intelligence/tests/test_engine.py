import unittest
from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import (
    build_evidence_graph,
    build_firm_passports,
    build_report,
    build_timeline,
    distribution,
    less_percent,
    peer_comparisons,
    primary_rows,
    run_detectors,
    self_audit,
    stable_id,
)


def award(**changes):
    row = {
        "tender_id": "123456",
        "exact_package_no": "GOB/WORKS/01",
        "contract_nature": "Works",
        "procurement_method": "OTM",
        "contract_price_unit": "BDT",
        "noa_date": "2026-01-15",
        "contract_price": "90.005",
        "app_estimated_cost": "100",
        "app_package_no": "GOB/WORKS/01",
        "app_match_confirmed": "TRUE",
        "app_match_status": "APP_MATCH_CONFIRMED",
        "app_search_status": "SEARCHED",
        "firm_tenderer_id": "TID-1",
        "firm_name": "Example Builders",
        "procuring_entity": "Office A",
        "district": "District A",
        "source_url": "https://example.invalid/award/123456",
        "source_html_sha256": "a" * 64,
        "source_snapshot_path": "private/snapshot.html",
        "source_confirmed": "TRUE",
        "scrape_date": "2026-01-16",
        "framework_agreement": "No",
        "contract_signing_date": "2026-01-20",
        "expected_completion_date": "2026-08-20",
    }
    row.update(changes)
    return row


class ScopeTests(unittest.TestCase):
    def test_only_primary_otm_works_after_default_date_and_supported_currency(self):
        rows = [
            award(),
            award(tender_id="0", contract_price_unit="bdt"),
            award(tender_id="2", contract_nature="Goods"),
            award(tender_id="3", procurement_method="LTM"),
            award(tender_id="4", noa_date="2025-09-14"),
            award(tender_id="5", contract_price_unit="USD"),
        ]
        self.assertEqual([row["tender_id"] for row in primary_rows(rows)], ["123456", "0"])


class CalculationTests(unittest.TestCase):
    def test_less_percent_uses_decimal_and_half_up_rounding(self):
        self.assertEqual(less_percent(award()), Decimal("-10.00"))
        self.assertEqual(less_percent(award(app_match_confirmed=1)), Decimal("-10.00"))

    def test_less_percent_requires_confirmed_exact_package_and_explicit_bdt(self):
        self.assertIsNone(less_percent(award(app_match_confirmed="FALSE")))
        self.assertIsNone(less_percent(award(app_package_no="different")))
        self.assertIsNone(less_percent(award(contract_price_unit="")))
        self.assertIsNone(less_percent(award(app_estimated_cost="0")))
        self.assertIsNone(less_percent(award(procurement_method="LTM")))
        self.assertIsNone(less_percent(award(contract_nature="Goods")))

    def test_distribution_exposes_sample_size_and_robust_statistics(self):
        actual = distribution([Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4")])
        self.assertEqual(actual["n"], 4)
        self.assertEqual(actual["median"], "2.5")
        self.assertEqual(actual["mad"], "1.00")
        self.assertEqual(actual["iqr"], "1.50")

    def test_extreme_less_boundaries_are_exclusive(self):
        rows = [
            award(tender_id="10", contract_price="110"),
            award(tender_id="11", contract_price="110.01"),
            award(tender_id="12", contract_price="60"),
            award(tender_id="13", contract_price="59.99"),
        ]
        flagged = {item["record_id"] for item in run_detectors(rows) if item["detector_id"] == "D001"}
        expected = {
            stable_id("AWD", "11", "GOB/WORKS/01", "Works"),
            stable_id("AWD", "13", "GOB/WORKS/01", "Works"),
        }
        self.assertEqual(flagged, expected)


class IdentityAndLineageTests(unittest.TestCase):
    def test_firms_group_only_by_exact_tenderer_id_not_display_name(self):
        rows = [
            award(tender_id="1", firm_tenderer_id="ID-A"),
            award(tender_id="2", firm_tenderer_id="ID-B"),
            award(tender_id="3", firm_tenderer_id=""),
        ]
        firms = build_firm_passports(rows)
        self.assertEqual({firm["firm_id"] for firm in firms}, {"ID-A", "ID-B"})
        self.assertEqual([firm["award_count"] for firm in firms], [1, 1])

    def test_name_variants_are_reported_for_review_without_merging_ids(self):
        rows = [
            award(tender_id="1", firm_name="Example Builders"),
            award(tender_id="2", firm_name="Example Builder Ltd"),
            award(tender_id="3", firm_tenderer_id="ID-OTHER", firm_name="Example Builders"),
        ]
        passports = {firm["firm_id"]: firm for firm in build_firm_passports(rows)}
        self.assertEqual(passports["TID-1"]["name_variant_count"], 2)
        self.assertEqual(passports["TID-1"]["identity_review"], "REVIEW_NAME_VARIANTS")
        findings = [item for item in run_detectors(rows) if item["detector_id"] == "D015"]
        self.assertEqual(len(findings), 2)
        self.assertIn("not an automatic identity collision", findings[0]["reason"])

    def test_history_is_keyed_to_primary_award_identity(self):
        keys = {("123456", "GOB/WORKS/01", "Works")}
        events = build_timeline(
            keys,
            [{"id": 7, "at": "2026-01-18", "tender_id": "123456", "exact_package_no": "GOB/WORKS/01", "contract_nature": "Works", "action": "UPDATED", "field": "firm_name", "old_value": "Old", "new_value": "Example Builders"}],
            [{"tender_id": "123456", "exact_package_no": "GOB/WORKS/01", "contract_nature": "Works", "changed_at": "2026-01-19", "column_name": "contract_price", "old_value": "80", "new_value": "90"}],
            [],
        )
        self.assertEqual(len(events), 2)
        self.assertEqual([event["event_type"] for event in events], ["AUDIT_LOG", "CONTRACT_REVISION"])
        self.assertTrue(all(event["record_id"] == stable_id("AWD", *next(iter(keys))) for event in events))

    def test_graph_traces_source_calculation_and_detector_to_award(self):
        row = award(contract_price="120")
        finding = next(item for item in run_detectors([row]) if item["detector_id"] == "D001")
        graph = build_evidence_graph([row], findings=[finding])
        node_types = {node["type"] for node in graph["nodes"]}
        edge_types = {edge["type"] for edge in graph["edges"]}
        self.assertTrue({"AWARD_RECORD", "SOURCE_URL", "SOURCE_SNAPSHOT", "CALCULATION", "DETECTOR_RESULT"} <= node_types)
        self.assertTrue({"EVIDENCED_BY", "CAPTURED_AS", "HAS_CALCULATION", "PRODUCED_BY", "SUPPORTED_BY"} <= edge_types)

    def test_graph_links_source_health_as_a_separate_observation(self):
        row = award()
        graph = build_evidence_graph(
            [row],
            source_health=[{
                "url": row["source_url"],
                "source_id": "source-1",
                "status": "HEALTHY",
                "last_check_at": "2026-02-01T00:00:00Z",
                "last_success_at": "2026-02-01T00:00:00Z",
                "consecutive_failures": "0",
            }],
        )
        self.assertIn("SOURCE_HEALTH", {node["type"] for node in graph["nodes"]})
        self.assertIn("HAS_HEALTH_OBSERVATION", {edge["type"] for edge in graph["edges"]})

    def test_peer_comparison_reports_peer_n_and_never_scores(self):
        selected = award(tender_id="1")
        population = [
            selected,
            award(tender_id="2", contract_price="80", district="District B"),
            award(tender_id="3", contract_price="70", district="District B"),
        ]
        comparisons = peer_comparisons([selected], population)
        firm = next(item for item in comparisons if item["formula_id"] == "FIRM_HISTORY_DEVIATION_V1")
        district = next(item for item in comparisons if item["formula_id"] == "DISTRICT_DEVIATION_V1")
        self.assertEqual(firm["n"], 2)
        self.assertEqual(firm["status"], "DESCRIPTIVE")
        self.assertNotIn("score", firm)
        self.assertEqual(district["n"], 0)
        self.assertEqual(district["status"], "INSUFFICIENT_DATA")


class ReportTests(unittest.TestCase):
    def test_unselected_report_is_summary_only_and_separates_not_attempted(self):
        rows = [award(), award(tender_id="654321", app_search_status="NOT_STARTED", app_match_confirmed="FALSE")]
        report = build_report(rows)
        self.assertEqual(report["analysis_subset"]["award_records"], 0)
        self.assertEqual(report["tender_passports"], [])
        self.assertEqual(report["firm_passports"], [])
        self.assertEqual(report["self_audit"]["app_search_status_counts"]["NOT_STARTED"], 1)
        self.assertEqual(report["population"]["award_records"], 2)

    def test_tender_report_reconstructs_exact_firm_history(self):
        rows = [
            award(tender_id="123456"),
            award(tender_id="654321", noa_date="2026-03-01", contract_price="200"),
            award(tender_id="777777", firm_tenderer_id="ID-OTHER"),
        ]
        report = build_report(rows, tender_id="123456")
        self.assertEqual(len(report["tender_passports"]), 1)
        self.assertEqual(report["tender_passports"][0]["app"]["less_pct"], "-10.00")
        self.assertEqual(len(report["firm_passports"]), 1)
        self.assertEqual(report["firm_passports"][0]["award_count"], 2)
        self.assertEqual(len(report["history_timeline"]), 0)

    def test_unconfirmed_estimate_is_not_exposed_as_a_number(self):
        passport = build_report(
            [award(app_match_confirmed="FALSE", app_estimated_cost="100")],
            tender_id="123456",
        )["tender_passports"][0]
        self.assertEqual(passport["app"]["estimate"], "NOT_FOUND")
        self.assertEqual(passport["app"]["less_pct"], "NOT_FOUND")

    def test_self_audit_counts_value_coverage_without_treating_blank_as_bdt(self):
        audit = self_audit([award(), award(tender_id="2", contract_price_unit="")])
        self.assertEqual(audit["records_with_bdt_unit_for_value_analysis"], 1)
        self.assertEqual(audit["records_with_blank_or_non_bdt_unit_excluded_from_bdt_math"], 1)


if __name__ == "__main__":
    unittest.main()
