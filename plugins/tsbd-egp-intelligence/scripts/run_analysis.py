"""Run local OTM Works analysis via the installed read-only q.py runner."""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from engine import DEFAULT_SINCE, FORMULA_VERSION, build_report

FIELDS = (
    "tender_id", "exact_package_no", "contract_nature", "ministry_division", "agency",
    "procuring_entity", "procuring_entity_code", "district", "firm_name", "firm_tenderer_id",
    "business_address", "package_name", "tender_reference", "advertisement_date", "noa_date",
    "contract_signing_date", "expected_completion_date", "contract_price", "contract_price_unit",
    "procurement_method", "framework_agreement", "source_url", "scrape_date",
    "app_estimated_cost", "app_package_no", "app_project_name", "app_financial_year",
    "app_source_reference", "app_searched_at", "match_status", "audit_result", "audit_reason",
    "app_match_confirmed", "app_match_status", "app_match_detail", "source_html_sha256",
    "source_fields_sha256", "source_captured_at", "source_snapshot_path", "source_confirmed",
    "source_status", "source_detail", "financial_year", "app_gate_status", "app_search_status",
    "app_match_confirmed_status", "duplicate_status", "conflict_status", "data_quality_status",
    "final_audit_status", "snapshot_status", "record_version",
)
RELATED_QUERIES = {
    "audit_log": (
        "SELECT a.* FROM audit_log a",
        "a.tender_id", "a.exact_package_no", "a.contract_nature", "a.id",
    ),
    "contract_revisions": (
        "SELECT a.* FROM contract_revisions a",
        "a.tender_id", "a.exact_package_no", "a.contract_nature", "a.changed_at",
    ),
    "field_recovery": (
        "SELECT a.* FROM field_recovery a",
        "a.tender_id", "a.exact_package_no", "a.contract_nature", "a.id",
    ),
    "audit_flags": (
        "SELECT a.* FROM audit_flags a",
        "a.tender_id", "a.exact_package_no", "a.contract_nature", "a.id",
    ),
    "data_quality": (
        "SELECT a.* FROM data_quality a",
        "a.tender_id", "a.exact_package_no", "a.contract_nature", "a.assessed_at",
    ),
    "source_health": (
        "SELECT DISTINCT sh.* FROM source_health sh",
        "p.tender_id", "p.exact_package_no", "p.contract_nature", "sh.source_id",
    ),
}


class RunnerError(RuntimeError):
    pass


def validate_since(value: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("--since must be a valid YYYY-MM-DD date.") from error
    if parsed.isoformat() != value:
        raise ValueError("--since must use YYYY-MM-DD format.")
    return value


def export_query(runner: Path, sql: str, destination: Path) -> tuple[list[dict[str, str]], str]:
    command = [
        sys.executable,
        str(runner),
        sql,
        "--csv",
        str(destination),
        "--max",
        "0",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RunnerError(f"Could not run the configured read-only query runner: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        raise RunnerError(f"Read-only query failed: {detail}")
    if not destination.is_file():
        raise RunnerError("The query runner reported success but did not create its temporary CSV result.")
    raw = destination.read_bytes()
    with destination.open("r", encoding="utf-8-sig", newline="") as stream:
        records = list(csv.DictReader(stream))
    return records, hashlib.sha256(raw).hexdigest()


def query_bundle(runner: Path, temp_dir: Path, since: str) -> tuple[dict[str, list[dict[str, str]]], dict[str, Any]]:
    fields = ", ".join(FIELDS)
    main_sql = (
        f"SELECT {fields} FROM production_contracts "
        f"WHERE upper(trim(procurement_method))='OTM' "
        f"AND contract_nature='Works' AND noa_date >= '{since}' "
        "ORDER BY tender_id, exact_package_no, contract_nature"
    )
    queries = {"production_contracts": main_sql}
    for table, (select_clause, key_tender, key_package, key_nature, order_by) in RELATED_QUERIES.items():
        if table == "source_health":
            sql = (
                f"{select_clause} WHERE EXISTS (SELECT 1 FROM production_contracts p "
                f"WHERE p.source_url=sh.url AND upper(trim(p.procurement_method))='OTM' "
                f"AND p.contract_nature='Works' AND p.noa_date >= '{since}') "
                f"ORDER BY {order_by}"
            )
        else:
            sql = (
                f"{select_clause} WHERE EXISTS (SELECT 1 FROM production_contracts p "
                f"WHERE p.tender_id={key_tender} AND p.exact_package_no={key_package} "
                f"AND p.contract_nature={key_nature} AND upper(trim(p.procurement_method))='OTM' "
                f"AND p.contract_nature='Works' AND p.noa_date >= '{since}') "
                f"ORDER BY {order_by}"
            )
        queries[table] = sql

    datasets: dict[str, list[dict[str, str]]] = {}
    snapshots: dict[str, Any] = {}
    for index, (name, sql) in enumerate(queries.items()):
        path = temp_dir / f"{index:02d}-{name}.csv"
        records, digest = export_query(runner, sql, path)
        datasets[name] = records
        snapshots[name] = {
            "row_count": len(records),
            "export_sha256": digest,
            "query_sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
        }
    return datasets, snapshots


def validate_output_path(value: str) -> Path:
    supplied = Path(value).expanduser()
    if not supplied.is_absolute():
        raise ValueError("--output must be an absolute path outside the repository.")
    target = supplied.resolve()
    repo_root = Path(__file__).resolve().parents[3]
    try:
        target.relative_to(repo_root)
    except ValueError:
        pass
    else:
        raise ValueError("Refusing to write tender data inside the plugin repository.")
    if not target.parent.is_dir():
        raise ValueError("The --output parent directory must already exist.")
    return target


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze local OTM Works awards without writing to the source database.")
    parser.add_argument("--runner", default=os.environ.get("TSBD_EGP_QUERY_RUNNER"), help="Path to the installed read-only q.py runner; may use TSBD_EGP_QUERY_RUNNER.")
    parser.add_argument("--since", default=DEFAULT_SINCE, help=f"Inclusive NOA start date (default: {DEFAULT_SINCE}).")
    parser.add_argument("--tender-id", help="Build a Tender Passport and its winner's exact-ID history.")
    parser.add_argument("--package-no", help="Optional exact package number filter.")
    parser.add_argument("--firm-id", help="Build a Firm Passport grouped only by exact firm_tenderer_id.")
    parser.add_argument("--output", help="Optional absolute JSON report path outside this repository.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing --output file.")
    args = parser.parse_args(argv)
    args.since = validate_since(args.since)
    if args.tender_id and args.firm_id:
        parser.error("Use either --tender-id or --firm-id for one identity view, not both.")
    if not args.runner:
        parser.error("Set --runner or TSBD_EGP_QUERY_RUNNER to the installed read-only q.py script.")
    args.runner = Path(args.runner).expanduser().resolve()
    if not args.runner.is_file():
        parser.error(f"Read-only query runner not found: {args.runner}")
    if args.output:
        try:
            args.output = validate_output_path(args.output)
        except ValueError as error:
            parser.error(str(error))
        if args.output.exists() and not args.overwrite:
            parser.error("Output file already exists; pass --overwrite to replace it.")
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        with tempfile.TemporaryDirectory(prefix="tsbd-egp-intel-") as name:
            temp_dir = Path(name)
            datasets, snapshots = query_bundle(args.runner, temp_dir, args.since)
            report = build_report(
                datasets["production_contracts"],
                audit_log=datasets["audit_log"],
                revisions=datasets["contract_revisions"],
                recoveries=datasets["field_recovery"],
                upstream_flags=datasets["audit_flags"],
                quality_records=datasets["data_quality"],
                source_health=datasets["source_health"],
                tender_id=args.tender_id,
                package_no=args.package_no,
                firm_id=args.firm_id,
                since=args.since,
            )
            report["reproducibility"] = {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "formula_version": FORMULA_VERSION,
                "query_runner_sha256": hashlib.sha256(args.runner.read_bytes()).hexdigest(),
                "input_exports": snapshots,
                "temporary_csvs_removed_after_run": True,
                "source_database_path_included": False,
            }
            output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
            if args.output:
                descriptor, temp_name = tempfile.mkstemp(prefix=f".{args.output.name}.", suffix=".tmp", dir=args.output.parent)
                temp_output = Path(temp_name)
                try:
                    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                        stream.write(output)
                        stream.flush()
                        os.fsync(stream.fileno())
                    if args.overwrite:
                        os.replace(temp_output, args.output)
                    else:
                        os.link(temp_output, args.output)
                finally:
                    temp_output.unlink(missing_ok=True)
                print(f"Report written to {args.output}")
            else:
                sys.stdout.write(output)
        return 0
    except (OSError, RunnerError, ValueError) as error:
        print(f"e-GP analysis failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
