import hashlib
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_analysis


class QueryBundleTests(unittest.TestCase):
    def test_export_invokes_runner_and_parses_temporary_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = root / "fake_runner.py"
            runner.write_text(
                "from pathlib import Path\n"
                "import sys\n"
                "target = Path(sys.argv[sys.argv.index('--csv') + 1])\n"
                "target.write_text('id,value\\n1,ok\\n', encoding='utf-8')\n",
                encoding="utf-8",
            )
            records, digest = run_analysis.export_query(
                runner,
                "SELECT 1",
                root / "export.csv",
            )
        self.assertEqual(records, [{"id": "1", "value": "ok"}])
        self.assertEqual(len(digest), 64)

    def test_queries_are_scoped_and_source_health_joins_by_url(self):
        queries = []

        def fake_export(_runner, sql, destination):
            queries.append(sql)
            destination.write_text("", encoding="utf-8")
            return [], hashlib.sha256(sql.encode("utf-8")).hexdigest()

        with tempfile.TemporaryDirectory() as directory:
            runner = Path(directory) / "runner.py"
            runner.write_text("# local test double\n", encoding="utf-8")
            with patch.object(run_analysis, "export_query", side_effect=fake_export):
                datasets, snapshots = run_analysis.query_bundle(
                    runner,
                    Path(directory),
                    "2025-09-15",
                )

        self.assertEqual(len(queries), 7)
        self.assertEqual(set(datasets), {
            "production_contracts", "audit_log", "contract_revisions", "field_recovery",
            "audit_flags", "data_quality", "source_health",
        })
        for query in queries:
            self.assertIn("upper(trim", query)
            self.assertIn("'OTM'", query)
            self.assertIn("'Works'", query)
            self.assertIn("2025-09-15", query)
        self.assertIn("p.source_url=sh.url", queries[-1])
        self.assertEqual(snapshots["production_contracts"]["row_count"], 0)


class RunnerSafetyTests(unittest.TestCase):
    def test_rejects_output_path_inside_repository(self):
        repo_root = Path(__file__).resolve().parents[3]
        with self.assertRaisesRegex(ValueError, "inside the plugin repository"):
            run_analysis.validate_output_path(str(repo_root / "private-report.json"))

    def test_main_wires_quality_inputs_and_cleans_temporary_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = root / "runner.py"
            runner.write_text("# local test double\n", encoding="utf-8")
            output = root / "report.json"
            temp_dirs = []
            datasets = {
                name: [{"grade": "A"}] if name == "data_quality" else [{"status": "OK"}] if name == "source_health" else []
                for name in (
                    "production_contracts", "audit_log", "contract_revisions", "field_recovery",
                    "audit_flags", "data_quality", "source_health",
                )
            }

            def fake_query_bundle(_runner, temp_dir, _since):
                temp_dirs.append(temp_dir)
                return datasets, {"production_contracts": {"row_count": 0}}

            with patch.object(run_analysis, "query_bundle", side_effect=fake_query_bundle), \
                    patch.object(run_analysis, "build_report", return_value={"report_version": "test"}) as build_report:
                with redirect_stdout(StringIO()):
                    result = run_analysis.main([
                        "--runner", str(runner),
                        "--output", str(output),
                    ])

            self.assertEqual(result, 0)
            self.assertFalse(temp_dirs[0].exists())
            self.assertEqual(build_report.call_args.kwargs["quality_records"], datasets["data_quality"])
            self.assertEqual(build_report.call_args.kwargs["source_health"], datasets["source_health"])
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["reproducibility"]["input_exports"]["production_contracts"]["row_count"], 0)
            self.assertFalse(report["reproducibility"]["source_database_path_included"])

    def test_existing_output_requires_explicit_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner = root / "runner.py"
            runner.write_text("# local test double\n", encoding="utf-8")
            output = root / "report.json"
            output.write_text("existing", encoding="utf-8")
            with redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit):
                    run_analysis.parse_args([
                        "--runner", str(runner),
                        "--output", str(output),
                    ])


if __name__ == "__main__":
    unittest.main()
