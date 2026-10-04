"""Deterministic e-GP analysis primitives; this module never accesses a database."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import re
from typing import Any, Iterable, Mapping, Sequence

PRIMARY_SCOPE = "PRIMARY_OTM_WORKS"
DEFAULT_SINCE = "2025-09-15"
FORMULA_VERSION = "1.0.0"
EXTREME_LESS_LOW = Decimal("-40")
EXTREME_LESS_HIGH = Decimal("10")


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _upper(value: Any) -> str:
    return _text(value).upper()


def _is_true(value: Any) -> bool:
    return _upper(value) in {"TRUE", "1"}


def parse_decimal(value: Any) -> Decimal | None:
    raw = _text(value).replace(",", "")
    if not raw or not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", raw):
        return None
    try:
        number = Decimal(raw)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def format_decimal(value: Decimal, minimum_places: int = 2) -> str:
    places = max(minimum_places, max(0, -value.as_tuple().exponent))
    return f"{value:,.{places}f}"


def record_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        _text(row.get("tender_id")),
        _text(row.get("exact_package_no")),
        _text(row.get("contract_nature")),
    )


def stable_id(prefix: str, *parts: Any) -> str:
    canonical = "\x1f".join(_text(part) for part in parts)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20].upper()
    return f"{prefix}-{digest}"


def in_primary_scope(row: Mapping[str, Any], since: str = DEFAULT_SINCE) -> bool:
    if _upper(row.get("procurement_method")) != "OTM":
        return False
    if _text(row.get("contract_nature")) != "Works":
        return False
    if _upper(row.get("contract_price_unit")) not in ("", "BDT"):
        return False
    noa = _text(row.get("noa_date"))
    try:
        date.fromisoformat(since)
        date.fromisoformat(noa)
    except ValueError:
        return False
    return noa >= since


def primary_rows(rows: Iterable[Mapping[str, Any]], since: str = DEFAULT_SINCE) -> list[dict[str, Any]]:
    return [dict(row) for row in rows if in_primary_scope(row, since)]


def app_match_is_confirmed(row: Mapping[str, Any]) -> bool:
    estimate = parse_decimal(row.get("app_estimated_cost"))
    return (
        _is_true(row.get("app_match_confirmed"))
        and estimate is not None
        and estimate > 0
        and _text(row.get("app_package_no")) == _text(row.get("exact_package_no"))
    )


def less_percent(row: Mapping[str, Any]) -> Decimal | None:
    """LESS_PCT v1: award versus exact-package confirmed APP estimate, in percent."""
    if (
        _upper(row.get("procurement_method")) != "OTM"
        or _text(row.get("contract_nature")) != "Works"
        or not app_match_is_confirmed(row)
        or _upper(row.get("contract_price_unit")) != "BDT"
    ):
        return None
    price = parse_decimal(row.get("contract_price"))
    estimate = parse_decimal(row.get("app_estimated_cost"))
    if price is None or estimate is None or price <= 0 or estimate <= 0:
        return None
    return (((price - estimate) / estimate) * Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def _quantile(values: Sequence[Decimal], numerator: int, denominator: int) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    position = Decimal(len(ordered) - 1) * Decimal(numerator) / Decimal(denominator)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def distribution(values: Iterable[Decimal]) -> dict[str, Any]:
    items = sorted(values)
    if not items:
        return {
            "n": 0,
            "median": None,
            "mean": None,
            "mad": None,
            "iqr": None,
            "p25": None,
            "p75": None,
        }
    median = _quantile(items, 1, 2)
    p25 = _quantile(items, 1, 4)
    p75 = _quantile(items, 3, 4)
    deviations = [abs(value - median) for value in items] if median is not None else []
    mad = _quantile(deviations, 1, 2)
    mean = sum(items, Decimal(0)) / Decimal(len(items))
    return {
        "n": len(items),
        "median": str(median),
        "mean": str(mean),
        "mad": str(mad) if mad is not None else None,
        "iqr": str(p75 - p25) if p25 is not None and p75 is not None else None,
        "p25": str(p25) if p25 is not None else None,
        "p75": str(p75) if p75 is not None else None,
    }


def _bdt_price(row: Mapping[str, Any]) -> Decimal | None:
    if _upper(row.get("contract_price_unit")) != "BDT":
        return None
    amount = parse_decimal(row.get("contract_price"))
    return amount if amount is not None and amount > 0 else None


def _group_key(row: Mapping[str, Any], field: str) -> str:
    return _text(row.get(field))


def _group_summaries(rows: Sequence[Mapping[str, Any]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        key = _group_key(row, field)
        if key:
            groups[key].append(row)
    results = []
    for key, group in sorted(groups.items()):
        less = [value for row in group if (value := less_percent(row)) is not None]
        prices = [value for row in group if (value := _bdt_price(row)) is not None]
        results.append({
            "key": key,
            "award_count": len(group),
            "contract_value_bdt_n": len(prices),
            "contract_value_bdt": format_decimal(sum(prices, Decimal(0))) if prices else None,
            "less_pct": distribution(less),
        })
    return results


def peer_comparisons(
    selected: Sequence[Mapping[str, Any]],
    population: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    comparisons = []
    peer_fields = (
        ("firm_tenderer_id", "FIRM_HISTORY_DEVIATION_V1"),
        ("procuring_entity", "PE_HISTORY_DEVIATION_V1"),
        ("district", "DISTRICT_DEVIATION_V1"),
    )
    for row in selected:
        current = less_percent(row)
        if current is None:
            continue
        for field, formula_id in peer_fields:
            key = _group_key(row, field)
            if not key:
                comparisons.append({
                    "record_id": stable_id("AWD", *record_key(row)),
                    "formula_id": formula_id,
                    "group_key": None,
                    "n": 0,
                    "status": "INSUFFICIENT_EVIDENCE",
                })
                continue
            peers = [
                value for other in population
                if _group_key(other, field) == key and record_key(other) != record_key(row)
                if (value := less_percent(other)) is not None
            ]
            stats = distribution(peers)
            median = parse_decimal(stats["median"])
            comparisons.append({
                "record_id": stable_id("AWD", *record_key(row)),
                "formula_id": formula_id,
                "formula_version": FORMULA_VERSION,
                "group_field": field,
                "group_key": key,
                "current_less_pct": str(current),
                "n": len(peers),
                "median_less_pct": str(median) if median is not None else None,
                "deviation_percentage_points": str(
                    (current - median).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                ) if median is not None else None,
                "status": "DESCRIPTIVE" if peers else "INSUFFICIENT_DATA",
                "interpretation": "Descriptive comparison only; no anomaly threshold or score is configured.",
            })
    return comparisons


def concentration_index(rows: Sequence[Mapping[str, Any]], by: str, value_based: bool = False) -> dict[str, Any]:
    amounts: dict[str, Decimal] = defaultdict(Decimal)
    excluded = 0
    for row in rows:
        key = _group_key(row, by)
        if not key:
            excluded += 1
            continue
        if value_based:
            amount = _bdt_price(row)
            if amount is None:
                excluded += 1
                continue
            amounts[key] += amount
        else:
            amounts[key] += Decimal(1)
    total = sum(amounts.values(), Decimal(0))
    hhi = sum(((amount / total) ** 2 for amount in amounts.values()), Decimal(0)) if total else None
    return {
        "formula_id": "CONCENTRATION_HHI_V1",
        "basis": "BDT contract value" if value_based else "award count",
        "group_field": by,
        "groups": len(amounts),
        "denominator": str(total) if total else "0",
        "excluded_missing_key_or_value": excluded,
        "hhi": str(hhi) if hhi is not None else None,
    }


def _value_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := _bdt_price(row)) is not None]
    return {
        "formula_id": "BDT_SUM_V1",
        "n": len(values),
        "denominator_awards": len(rows),
        "excluded_unknown_unit_or_invalid": len(rows) - len(values),
        "total": format_decimal(sum(values, Decimal(0))) if values else None,
    }


def build_firm_passports(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    unresolved = []
    for row in rows:
        firm_id = _text(row.get("firm_tenderer_id"))
        if firm_id:
            groups[firm_id].append(row)
        else:
            unresolved.append(row)
    passports = []
    for firm_id, group in sorted(groups.items()):
        names = sorted({_text(row.get("firm_name")) for row in group if _text(row.get("firm_name"))})
        pe_counts = Counter(_text(row.get("procuring_entity")) for row in group if _text(row.get("procuring_entity")))
        district_counts = Counter(_text(row.get("district")) for row in group if _text(row.get("district")))
        months = Counter(_text(row.get("noa_date"))[:7] for row in group if _text(row.get("noa_date")))
        passports.append({
            "firm_id": firm_id,
            "identity_resolution": "EXACT_TENDERER_ID",
            "name_variants": names,
            "name_variant_count": len(names),
            "identity_review": "REVIEW_NAME_VARIANTS" if len(names) > 1 else "NO_VARIANT_OBSERVED",
            "award_count": len(group),
            "contract_value_bdt": _group_summaries(group, "firm_tenderer_id")[0]["contract_value_bdt"],
            "contract_value_bdt_n": sum(_bdt_price(row) is not None for row in group),
            "less_pct": distribution(value for row in group if (value := less_percent(row)) is not None),
            "procuring_entities": dict(sorted(pe_counts.items())),
            "districts": dict(sorted(district_counts.items())),
            "monthly_awards": dict(sorted(months.items())),
            "participation_or_loss_history": "NOT_AVAILABLE_IN_AWARD_RECORDS",
            "credential_history": "NOT_AVAILABLE_IN_INSPECTED_SCHEMA",
        })
    return passports


def build_tender_passports(
    rows: Sequence[Mapping[str, Any]],
    tender_id: str | None = None,
    package_no: str | None = None,
    quality_records: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    selected = [
        row for row in rows
        if (tender_id is None or _text(row.get("tender_id")) == tender_id)
        and (package_no is None or _text(row.get("exact_package_no")) == package_no)
    ]
    passports = []
    for row in selected:
        confirmed = app_match_is_confirmed(row)
        rid = stable_id("AWD", *record_key(row))
        quality = next((item for item in quality_records if record_key(item) == record_key(row)), None)
        passports.append({
            "record_id": rid,
            "scope_class": "PRIMARY",
            "scope": PRIMARY_SCOPE,
            "identity": {
                "tender_id": _text(row.get("tender_id")),
                "package_no": _text(row.get("exact_package_no")),
                "nature": _text(row.get("contract_nature")),
                "reference": _text(row.get("tender_reference")) or None,
            },
            "classification": {
                "method": _text(row.get("procurement_method")),
                "framework_agreement": _text(row.get("framework_agreement")) or "NOT_FOUND",
                "financial_year": _text(row.get("financial_year")) or None,
            },
            "location": {
                "district": _text(row.get("district")) or "NOT_FOUND",
                "ministry_division": _text(row.get("ministry_division")) or "NOT_FOUND",
                "agency": _text(row.get("agency")) or "NOT_FOUND",
                "procuring_entity": _text(row.get("procuring_entity")) or "NOT_FOUND",
                "procuring_entity_code": _text(row.get("procuring_entity_code")) or "NOT_FOUND",
            },
            "dates": {
                "advertisement": _text(row.get("advertisement_date")) or "NOT_FOUND",
                "noa": _text(row.get("noa_date")) or "NOT_FOUND",
                "contract_signing": _text(row.get("contract_signing_date")) or "NOT_FOUND",
                "expected_completion": _text(row.get("expected_completion_date")) or "NOT_FOUND",
            },
            "award": {
                "amount": _text(row.get("contract_price")) or "NOT_FOUND",
                "currency": _text(row.get("contract_price_unit")) or "NOT_CONFIRMED",
                "firm_id": _text(row.get("firm_tenderer_id")) or "UNRESOLVED",
                "firm_name": _text(row.get("firm_name")) or "NOT_FOUND",
            },
            "app": {
                "estimate": _text(row.get("app_estimated_cost")) if confirmed else "NOT_FOUND",
                "match_status": _text(row.get("app_match_status")) or "NOT_FOUND",
                "confirmed": confirmed,
                "less_pct": str(less_percent(row)) if less_percent(row) is not None else "NOT_FOUND",
            },
            "provenance": {
                "source_url": _text(row.get("source_url")) or None,
                "evidence_id": stable_id(
                    "EVD", "production_contracts", *record_key(row),
                    _text(row.get("source_html_sha256")) or _text(row.get("source_url")),
                ),
                "source_confirmed": _is_true(row.get("source_confirmed")),
                "source_html_sha256": _text(row.get("source_html_sha256")) or None,
                "source_fields_sha256": _text(row.get("source_fields_sha256")) or None,
                "source_snapshot_path": _text(row.get("source_snapshot_path")) or None,
                "scrape_date": _text(row.get("scrape_date")) or None,
            },
            "data_quality": {
                "grade": _text(quality.get("grade")) if quality else "NOT_RECORDED",
                "score": _text(quality.get("score")) if quality and _text(quality.get("score")) else None,
                "score_source": "database data_quality record; not recomputed" if quality else None,
                "assessed_at": _text(quality.get("assessed_at")) if quality else None,
            },
        })
    return passports


def build_timeline(
    keys: set[tuple[str, str, str]],
    audit_log: Sequence[Mapping[str, Any]],
    revisions: Sequence[Mapping[str, Any]],
    recoveries: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    sources = (
        ("AUDIT_LOG", audit_log, "at"),
        ("CONTRACT_REVISION", revisions, "changed_at"),
        ("FIELD_RECOVERY", recoveries, "recovered_at"),
    )
    for event_type, records, date_field in sources:
        for row in records:
            if record_key(row) not in keys:
                continue
            event_key = (
                event_type, *record_key(row), _text(row.get(date_field)),
                _text(row.get("field") or row.get("column_name")),
                _text(row.get("action") or row.get("recovery_method")),
                _text(row.get("old_value") or row.get("previous_value")),
                _text(row.get("new_value")),
            )
            events.append({
                "event_id": stable_id("EVT", *event_key),
                "event_type": event_type,
                "at": _text(row.get(date_field)),
                "record_id": stable_id("AWD", *record_key(row)),
                "field": _text(row.get("field") or row.get("column_name")) or None,
                "action": _text(row.get("action") or row.get("recovery_method") or row.get("verification")) or None,
                "old_value": _text(row.get("old_value") or row.get("previous_value")) or None,
                "new_value": _text(row.get("new_value")) or None,
                "reason": _text(row.get("reason") or row.get("note")) or None,
                "source": _text(row.get("source") or row.get("source_url")) or None,
                "status": _text(row.get("status") or row.get("verification")) or None,
            })
    return sorted(events, key=lambda event: (event["at"], event["event_id"]))


def build_evidence_graph(
    rows: Sequence[Mapping[str, Any]],
    timeline: Sequence[Mapping[str, Any]] = (),
    findings: Sequence[Mapping[str, Any]] = (),
    source_health: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    def add_node(node_id: str, node_type: str, label: str, **attrs: Any) -> None:
        nodes.setdefault(node_id, {"id": node_id, "type": node_type, "label": label, **attrs})

    for row in rows:
        award_id = stable_id("AWD", *record_key(row))
        add_node(award_id, "AWARD_RECORD", " / ".join(record_key(row)), source_table="production_contracts")
        firm_id = _text(row.get("firm_tenderer_id"))
        if firm_id:
            fid = stable_id("FIRM", firm_id)
            add_node(fid, "FIRM", _text(row.get("firm_name")) or "Name unavailable", tenderer_id=firm_id)
            edges.append({"from": award_id, "to": fid, "type": "AWARDED_TO"})
        pe_name = _text(row.get("procuring_entity"))
        if pe_name:
            pe_id = stable_id("PE", _text(row.get("procuring_entity_code")) or pe_name)
            add_node(pe_id, "PROCURING_ENTITY", pe_name, code=_text(row.get("procuring_entity_code")) or None)
            edges.append({"from": award_id, "to": pe_id, "type": "PROCURED_BY"})
        district = _text(row.get("district"))
        if district:
            district_id = stable_id("DISTRICT", district)
            add_node(district_id, "DISTRICT", district)
            edges.append({"from": award_id, "to": district_id, "type": "LOCATED_IN"})
        source_url = _text(row.get("source_url"))
        if source_url:
            source_id = stable_id("SOURCE", source_url)
            add_node(source_id, "SOURCE_URL", source_url)
            edges.append({"from": award_id, "to": source_id, "type": "EVIDENCED_BY"})
            health = next((item for item in source_health if _text(item.get("url")) == source_url), None)
            if health:
                health_id = stable_id("SOURCE_HEALTH", _text(health.get("source_id")), _text(health.get("last_check_at")))
                add_node(
                    health_id,
                    "SOURCE_HEALTH",
                    _text(health.get("status")) or "UNKNOWN",
                    last_check_at=_text(health.get("last_check_at")) or None,
                    last_success_at=_text(health.get("last_success_at")) or None,
                    consecutive_failures=_text(health.get("consecutive_failures")) or None,
                )
                edges.append({"from": source_id, "to": health_id, "type": "HAS_HEALTH_OBSERVATION"})
        source_hash = _text(row.get("source_html_sha256")).lower()
        if re.fullmatch(r"[0-9a-f]{64}", source_hash):
            snapshot_id = stable_id("SNAPSHOT", source_hash)
            add_node(snapshot_id, "SOURCE_SNAPSHOT", source_hash, sha256=source_hash)
            edges.append({"from": award_id, "to": snapshot_id, "type": "CAPTURED_AS"})
        evidence_id = stable_id(
            "EVD", "production_contracts", *record_key(row),
            source_hash or source_url,
        )
        add_node(evidence_id, "DATABASE_EVIDENCE", "Award row and its provenance fields")
        edges.append({"from": evidence_id, "to": award_id, "type": "DESCRIBES"})
        if source_url:
            edges.append({"from": evidence_id, "to": stable_id("SOURCE", source_url), "type": "POINTS_TO"})
        less = less_percent(row)
        if less is not None:
            calc_id = stable_id("CALC", "LESS_PCT_V1", *record_key(row), str(less))
            add_node(calc_id, "CALCULATION", f"LESS_PCT {less}%", formula_id="LESS_PCT_V1", formula_version=FORMULA_VERSION, result=str(less))
            edges.append({"from": calc_id, "to": award_id, "type": "USES_INPUT_RECORD"})
            edges.append({"from": award_id, "to": calc_id, "type": "HAS_CALCULATION"})
    for event in timeline:
        event_id = _text(event.get("event_id"))
        if event_id:
            add_node(event_id, "HISTORY_EVENT", _text(event.get("event_type")), at=_text(event.get("at")))
            if _text(event.get("record_id")) in nodes:
                edges.append({"from": event_id, "to": _text(event["record_id"]), "type": "CHANGES"})
    for finding in findings:
        record_id = _text(finding.get("record_id"))
        detector_id = _text(finding.get("detector_id"))
        result_id = stable_id(
            "RESULT", detector_id, _text(finding.get("detector_version")), record_id,
            _text(finding.get("reason")),
        )
        detector_node = stable_id("DETECTOR", detector_id, _text(finding.get("detector_version")))
        add_node(detector_node, "DETECTOR", detector_id, version=_text(finding.get("detector_version")))
        add_node(
            result_id,
            "DETECTOR_RESULT",
            _text(finding.get("reason")),
            status=_text(finding.get("status")),
            severity=_text(finding.get("severity")),
            reason_codes=finding.get("reason_codes", []),
        )
        if record_id in nodes:
            edges.append({"from": record_id, "to": result_id, "type": "HAS_DETECTOR_RESULT"})
        edges.append({"from": result_id, "to": detector_node, "type": "PRODUCED_BY"})
        formula_id = _text(finding.get("formula_id"))
        calc_id = _text(finding.get("calculation_id"))
        if formula_id and calc_id:
            if calc_id not in nodes:
                add_node(
                    calc_id,
                    "CALCULATION",
                    formula_id,
                    formula_id=formula_id,
                    formula_version=_text(finding.get("formula_version")),
                    parameters=finding.get("parameters", {}),
                )
                if record_id in nodes:
                    edges.append({"from": calc_id, "to": record_id, "type": "USES_INPUT_RECORD"})
            edges.append({"from": result_id, "to": calc_id, "type": "BASED_ON_CALCULATION"})
        for evidence_id in finding.get("evidence_ids", []):
            evidence_id = _text(evidence_id)
            if evidence_id and evidence_id not in nodes:
                add_node(evidence_id, "EVIDENCE_REFERENCE", "Referenced database evidence")
            if evidence_id:
                edges.append({"from": result_id, "to": evidence_id, "type": "SUPPORTED_BY"})
    return {
        "nodes": sorted(nodes.values(), key=lambda node: node["id"]),
        "edges": sorted(edges, key=lambda edge: (edge["from"], edge["to"], edge["type"])),
    }


def _finding(
    detector_id: str,
    row: Mapping[str, Any],
    status: str,
    severity: str,
    reason: str,
    evidence_ids: Sequence[str] = (),
    formula_id: str | None = None,
    parameters: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_ref = _text(row.get("source_html_sha256")) or _text(row.get("source_url"))
    evidence_id = stable_id("EVD", "production_contracts", *record_key(row), source_ref)
    record_id = stable_id("AWD", *record_key(row))
    calculation_id = None
    if formula_id == "LESS_PCT_V1":
        value = less_percent(row)
        if value is not None:
            calculation_id = stable_id("CALC", formula_id, *record_key(row), str(value))
    elif formula_id:
        calculation_id = stable_id("CALC", formula_id, *record_key(row))
    return {
        "detector_id": detector_id,
        "detector_version": "1.0.0",
        "record_id": record_id,
        "entity_id": stable_id("FIRM", _text(row.get("firm_tenderer_id"))) if _text(row.get("firm_tenderer_id")) else None,
        "scope": PRIMARY_SCOPE,
        "scope_class": "PRIMARY",
        "status": status,
        "severity": severity,
        "score": None,
        "reason_codes": [detector_id],
        "reason": reason,
        "formula_id": formula_id,
        "formula_version": FORMULA_VERSION if formula_id else None,
        "calculation_id": calculation_id,
        "parameters": dict(parameters or {}),
        "evidence_ids": [evidence_id, *evidence_ids],
        "input_record_ids": [record_id],
    }


def run_detectors(
    rows: Sequence[Mapping[str, Any]],
    upstream_flags: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    counts = Counter(record_key(row) for row in rows)
    firm_names: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        firm_id, name = _text(row.get("firm_tenderer_id")), _text(row.get("firm_name"))
        if firm_id and name:
            firm_names[firm_id].add(name)
    for row in rows:
        if counts[record_key(row)] > 1:
            findings.append(_finding("D016", row, "FLAG", "REVIEW", "Duplicate primary award key in the extracted view."))
        less = less_percent(row)
        if less is not None and (less < EXTREME_LESS_LOW or less > EXTREME_LESS_HIGH):
            findings.append(_finding(
                "D001", row, "FLAG", "REVIEW",
                f"Confirmed APP Less% is {less}%; review the underlying package and unit evidence.",
                formula_id="LESS_PCT_V1",
                parameters={"low_exclusive": str(EXTREME_LESS_LOW), "high_exclusive": str(EXTREME_LESS_HIGH)},
            ))
        if _is_true(row.get("app_match_confirmed")) and not app_match_is_confirmed(row):
            findings.append(_finding(
                "D019", row, "FLAG", "REVIEW",
                "APP match is marked confirmed but its positive estimate or exact package key is not usable.",
                formula_id="APP_GATE_V1",
            ))
        signed = _text(row.get("contract_signing_date"))
        completed = _text(row.get("expected_completion_date"))
        if signed and completed and completed < signed:
            findings.append(_finding(
                "D018", row, "FLAG", "REVIEW",
                "Expected completion date precedes contract signing date.",
                formula_id="DATE_ORDER_V1",
            ))
        if not _text(row.get("firm_tenderer_id")):
            findings.append(_finding("D026", row, "WATCH", "REVIEW", "Firm Tenderer ID is missing; the firm identity is unresolved."))
        firm_id = _text(row.get("firm_tenderer_id"))
        if firm_id and len(firm_names[firm_id]) > 1:
            findings.append(_finding(
                "D015", row, "WATCH", "REVIEW",
                "One exact Tenderer ID has multiple source-reported display names; retain as variants and review, not an automatic identity collision.",
                parameters={"name_variant_count": len(firm_names[firm_id])},
            ))
        missing_fields = [
            field for field in ("firm_name", "district", "procuring_entity_code", "contract_price_unit")
            if not _text(row.get(field))
        ]
        if missing_fields:
            findings.append(_finding(
                "D020", row, "WATCH", "REVIEW",
                "Critical analytical context fields are missing; calculations remain limited to supported fields.",
                parameters={"missing_fields": missing_fields},
            ))
        if not _text(row.get("source_html_sha256")) or not _text(row.get("source_snapshot_path")):
            findings.append(_finding(
                "D022", row, "WATCH", "REVIEW",
                "The database row lacks a complete source-snapshot hash/path pair; the source URL alone is not a stored snapshot.",
            ))
    for flag in upstream_flags:
        key = record_key(flag)
        if key not in counts:
            continue
        row = next(record for record in rows if record_key(record) == key)
        flag_id = stable_id("DBFLAG", flag.get("id"), flag.get("flag_type"), *key)
        findings.append({
            "detector_id": _text(flag.get("detector")) or _text(flag.get("flag_type")) or "UPSTREAM_AUDIT_FLAG",
            "detector_version": "DATABASE",
            "record_id": stable_id("AWD", *key),
            "entity_id": stable_id("FIRM", _text(row.get("firm_tenderer_id"))) if _text(row.get("firm_tenderer_id")) else None,
            "scope": PRIMARY_SCOPE,
            "scope_class": "PRIMARY",
            "status": _upper(flag.get("state")) or "OPEN",
            "severity": _upper(flag.get("severity")) or "REVIEW",
            "score": None,
            "reason_codes": [_text(flag.get("flag_type")) or "UPSTREAM_AUDIT_FLAG"],
            "reason": _text(flag.get("reason")),
            "formula_id": None,
            "formula_version": None,
            "parameters": {"field": _text(flag.get("field")) or None, "state": _text(flag.get("state")) or None},
            "evidence_ids": [flag_id],
            "input_record_ids": [stable_id("AWD", *key)],
        })
    return sorted(findings, key=lambda item: (item["detector_id"], item["record_id"], item["reason"]))


def self_audit(rows: Sequence[Mapping[str, Any]], since: str = DEFAULT_SINCE) -> dict[str, Any]:
    keys = [record_key(row) for row in rows]
    duplicate_keys = [key for key, count in Counter(keys).items() if count > 1]
    app_confirmed = [row for row in rows if app_match_is_confirmed(row)]
    source_confirmed = sum(_is_true(row.get("source_confirmed")) for row in rows)
    bdt_values = sum(_bdt_price(row) is not None for row in rows)
    unknown_currency = sum(_upper(row.get("contract_price_unit")) != "BDT" for row in rows)
    return {
        "audit_version": "1.0.0",
        "scope": PRIMARY_SCOPE,
        "scope_class": "PRIMARY",
        "noa_date_from_inclusive": since,
        "population": "production_contracts view; not a completeness audit of raw contracts or out-of-view records",
        "records_in_scope_view": len(rows),
        "completeness_claim": "NOT_MADE: the view is not an independent expected-record denominator",
        "verified_source_records": source_confirmed,
        "app_match_confirmed_records": len(app_confirmed),
        "records_with_bdt_unit_for_value_analysis": bdt_values,
        "records_with_blank_or_non_bdt_unit_excluded_from_bdt_math": unknown_currency,
        "duplicate_primary_keys": len(duplicate_keys),
        "duplicate_keys_sample": [list(key) for key in duplicate_keys[:10]],
        "missing_firm_tenderer_id": sum(not _text(row.get("firm_tenderer_id")) for row in rows),
        "missing_district": sum(not _text(row.get("district")) for row in rows),
        "missing_source_html_sha256": sum(not _text(row.get("source_html_sha256")) for row in rows),
        "missing_source_snapshot_path": sum(not _text(row.get("source_snapshot_path")) for row in rows),
        "app_search_status_counts": dict(sorted(Counter(_upper(row.get("app_search_status")) or "NOT_RECORDED" for row in rows).items())),
        "app_match_status_counts": dict(sorted(Counter(_upper(row.get("app_match_status")) or "NOT_RECORDED" for row in rows).items())),
        "source_status_counts": dict(sorted(Counter(_upper(row.get("source_status")) or "NOT_RECORDED" for row in rows).items())),
        "freshest_scrape_date": max((_text(row.get("scrape_date")) for row in rows if _text(row.get("scrape_date"))), default=None),
        "oldest_scrape_date": min((_text(row.get("scrape_date")) for row in rows if _text(row.get("scrape_date"))), default=None),
        "limitations": [
            "Records excluded by production_contracts are outside this report's completeness denominator.",
            "Blank contract_price_unit is not assumed to mean BDT.",
            "A source URL is not treated as a retained source snapshot.",
            "A missing value is not interpreted as NOT_FOUND versus NOT_ATTEMPTED unless a source status field distinguishes it.",
        ],
    }


def build_report(
    rows: Sequence[Mapping[str, Any]],
    audit_log: Sequence[Mapping[str, Any]] = (),
    revisions: Sequence[Mapping[str, Any]] = (),
    recoveries: Sequence[Mapping[str, Any]] = (),
    upstream_flags: Sequence[Mapping[str, Any]] = (),
    quality_records: Sequence[Mapping[str, Any]] = (),
    source_health: Sequence[Mapping[str, Any]] = (),
    tender_id: str | None = None,
    package_no: str | None = None,
    firm_id: str | None = None,
    since: str = DEFAULT_SINCE,
) -> dict[str, Any]:
    scoped = primary_rows(rows, since)
    keys = {record_key(row) for row in scoped}
    timeline = build_timeline(keys, audit_log, revisions, recoveries)
    has_selector = tender_id is not None or package_no is not None or firm_id is not None
    selected = [
        row for row in scoped
        if has_selector
        and (tender_id is None or _text(row.get("tender_id")) == tender_id)
        and (package_no is None or _text(row.get("exact_package_no")) == package_no)
        and (firm_id is None or _text(row.get("firm_tenderer_id")) == firm_id)
    ]
    less = [value for row in scoped if (value := less_percent(row)) is not None]
    all_findings = run_detectors(scoped, upstream_flags)
    selected_ids = {stable_id("AWD", *record_key(row)) for row in selected}
    selected_findings = [item for item in all_findings if item["record_id"] in selected_ids]
    selected_firm_ids = {
        _text(row.get("firm_tenderer_id")) for row in selected if _text(row.get("firm_tenderer_id"))
    }
    firm_history_rows = [row for row in scoped if _text(row.get("firm_tenderer_id")) in selected_firm_ids]
    report: dict[str, Any] = {
        "report_version": "1.0.0",
        "scope": PRIMARY_SCOPE,
        "scope_class": "PRIMARY",
        "filters": {"method": "OTM", "nature": "Works", "noa_date_from_inclusive": since},
        "population": {
            "award_records": len(scoped),
            "tender_ids": len({_text(row.get("tender_id")) for row in scoped if _text(row.get("tender_id"))}),
            "confirmed_less_pct_records": len(less),
        },
        "less_pct_distribution": distribution(less),
        "contract_value_bdt": _value_summary(scoped),
        "procuring_entity_concentration": concentration_index(scoped, "procuring_entity"),
        "firm_award_concentration": concentration_index(scoped, "firm_tenderer_id"),
        "firm_bdt_value_concentration": concentration_index(scoped, "firm_tenderer_id", value_based=True),
        "procuring_entities": _group_summaries(scoped, "procuring_entity"),
        "districts": _group_summaries(scoped, "district"),
        "self_audit": self_audit(scoped, since),
        "detector_summary": dict(sorted(Counter(item["detector_id"] for item in all_findings).items())),
        "detectors": selected_findings,
        "analysis_subset": {
            "tender_id": tender_id,
            "package_no": package_no,
            "firm_tenderer_id": firm_id,
            "award_records": len(selected),
        },
        "tender_passports": build_tender_passports(selected, quality_records=quality_records),
        "firm_passports": build_firm_passports(firm_history_rows),
        "peer_comparisons": peer_comparisons(selected, scoped),
        "history_timeline": [
            event for event in timeline
            if any(event["record_id"] == stable_id("AWD", *record_key(row)) for row in selected)
        ],
        "evidence_graph": build_evidence_graph(selected, timeline, selected_findings, source_health),
        "data_quality": {
            "records_assessed": len(quality_records),
            "grades": dict(sorted(Counter(_upper(row.get("grade")) or "NOT_RECORDED" for row in quality_records).items())),
            "source_health_observations": len(source_health),
            "source_health_states": dict(sorted(Counter(_upper(row.get("status")) or "UNKNOWN" for row in source_health).items())),
            "latest_source_check": max((_text(row.get("last_check_at")) for row in source_health if _text(row.get("last_check_at"))), default=None),
            "latest_source_success": max((_text(row.get("last_success_at")) for row in source_health if _text(row.get("last_success_at"))), default=None),
            "staleness_policy": "No stale-age threshold configured; timestamps are reported without pass/fail inference.",
        },
        "formula_registry": {
            "LESS_PCT_V1": {
                "formula": "(contract_price - app_estimated_cost) / app_estimated_cost * 100",
                "rounding": "Decimal ROUND_HALF_UP to 0.01 percentage point",
                "required": ["app_match_confirmed=TRUE", "positive APP estimate", "exact APP package match", "contract_price_unit=BDT"],
                "scope": PRIMARY_SCOPE,
                "minimum_sample_size": 1,
                "status": "per-record calculation; no peer outlier score",
            },
            "BDT_SUM_V1": {
                "formula": "sum(contract_price) where contract_price_unit is explicitly BDT and price is positive",
                "scope": PRIMARY_SCOPE,
                "minimum_sample_size": 1,
            },
            "CONCENTRATION_HHI_V1": {
                "formula": "sum((group_amount / total_amount) ** 2)",
                "scope": PRIMARY_SCOPE,
                "minimum_sample_size": 1,
                "status": "descriptive only; no alert threshold configured",
            },
            "DISTRIBUTION_V1": {
                "formula": "linear-interpolated quantiles; MAD is median absolute deviation from median",
                "scope": PRIMARY_SCOPE,
                "minimum_sample_size": 1,
                "status": "descriptive only; every result carries n",
            },
            "FIRM_HISTORY_DEVIATION_V1": {
                "formula": "selected award Less% minus median of other exact-ID awards",
                "scope": PRIMARY_SCOPE,
                "minimum_peer_count": 1,
                "status": "descriptive percentage-point comparison only; no threshold or score",
            },
            "PE_HISTORY_DEVIATION_V1": {
                "formula": "selected award Less% minus median of other same-name procuring-entity awards",
                "scope": PRIMARY_SCOPE,
                "minimum_peer_count": 1,
                "status": "descriptive percentage-point comparison only; entity name key is not a verified entity ID",
            },
            "DISTRICT_DEVIATION_V1": {
                "formula": "selected award Less% minus median of other awards in the same district",
                "scope": PRIMARY_SCOPE,
                "minimum_peer_count": 1,
                "status": "descriptive percentage-point comparison only; no threshold or score",
            },
            "APP_GATE_V1": {
                "formula": "confirmed match AND positive estimate AND exact APP package number",
                "scope": PRIMARY_SCOPE,
                "status": "eligibility gate; not a finding of wrongdoing",
            },
            "DATE_ORDER_V1": {
                "formula": "expected_completion_date < contract_signing_date",
                "scope": PRIMARY_SCOPE,
                "status": "data consistency review only",
            },
            "D001": {
                "condition": "LESS_PCT_V1 < -40 OR LESS_PCT_V1 > +10",
                "source": "TSBD e-GP analysis guidance",
                "status": "review alert only; thresholds are exclusive boundaries",
            },
        },
        "data_limitations": [
            "The primary population comes only from production_contracts, which applies its own collection and exclusion rules.",
            "Only firm_tenderer_id is used to group firms; missing IDs remain unresolved and name similarity never merges entities.",
            "Award records do not establish bidder participation, losses, responsiveness, or rank.",
            "The inspected schema has beneficial-owner rows but no licence/credential history table; no credential status is inferred.",
            "No weighted anomaly score is emitted because no approved weights or thresholds were supplied.",
        ],
    }
    return report
