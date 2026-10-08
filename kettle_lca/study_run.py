"""BOM을 Commons Merged 단위공정에 연결하고 GWP100을 계산한다."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import yaml

from kettle_lca.bom import BomLine, bom_mass_totals, load_bom
from kettle_lca.exchanges import reference_exchange, read_exchanges
from kettle_lca.impact import ImpactResult, characterize_scaling, load_ar6_100_factors
from kettle_lca.matching import MATCH_RULES, choose_match, rank_candidates
from kettle_lca.system_builder import BuiltSystem, build_system, scaling_for_demand
from kettle_lca.units import UnitConversionError, convert_amount
from kettle_lca.uslci_store import UslciStore


@dataclass(frozen=True)
class AcceptedMatch:
    material: str
    mass_g: float
    part: str
    process_id: str
    process_name: str
    version: str
    location: str
    reference_unit: str
    demand_in_reference_unit: float
    rationale: str
    database_status: str


def run_study(project_root: Path) -> dict:
    study = _read_yaml(project_root / "config" / "study.yaml")
    assumptions = _read_yaml(project_root / "config" / "assumptions.yaml")
    bom = load_bom(project_root / "data" / "bom.csv")
    zip_path = project_root / "data" / "cache" / "commons_merged.zip"
    store = UslciStore(zip_path)
    try:
        matches, candidate_rows = _match_bom(store, bom)
        demands = {
            match.process_id: match.demand_in_reference_unit
            for match in matches
            if match.database_status == "matched"
        }
        # 같은 공정을 두 항목이 고르면 수요를 더한다.
        combined: dict[str, float] = {}
        for match in matches:
            if match.database_status != "matched":
                continue
            combined[match.process_id] = combined.get(match.process_id, 0.0) + match.demand_in_reference_unit
        system = build_system(store, list(combined))
        factors = load_ar6_100_factors(zip_path)
        scaling = scaling_for_demand(system, combined)
        total = characterize_scaling(system, scaling, factors)
        contributions = _contributions(system, matches, factors)
    finally:
        store.close()

    nested = _nested_match_flags(store_path=zip_path, matches=matches)
    result = {
        "study": study,
        "assumptions": assumptions,
        "bom_check": bom_mass_totals(bom),
        "database_file_sha256": _sha256(zip_path),
        "process_count": len(system.process_ids),
        "characterized_gwp100_kg_co2eq": total.characterized_kg_co2eq,
        "biogenic_co2_kg": total.biogenic_co2_kg,
        "calculation_status": _status(matches, system, total),
        "matches": [asdict(match) for match in matches],
        "contributions": contributions,
        "contribution_sum_kg_co2eq": sum(item["gwp100_kg_co2eq"] or 0.0 for item in contributions),
        "unresolved_link_count": len(system.unresolved_links),
        "missing_provider_count": len(system.missing_provider_ids),
        "uncharacterized_flow_count": len(total.uncharacterized_flows),
        "skipped_exchange_count": len(system.skipped_exchanges),
        "monetary_proxies_not_used": _monetary_proxies(store_path=zip_path),
        "nested_matches": nested,
        "top_characterized_flows": [
            asdict(item) for item in total.flows if item.impact_kg_co2eq is not None
        ][:15],
    }
    output_dir = project_root / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_outputs(output_dir, result, candidate_rows, system, total)
    return result


def _match_bom(store: UslciStore, bom: list[BomLine]) -> tuple[list[AcceptedMatch], list[dict]]:
    summaries = list(store.summaries().values())
    rules = {rule.material: rule for rule in MATCH_RULES}
    matches: list[AcceptedMatch] = []
    candidate_rows: list[dict] = []
    for line in bom:
        rule = rules.get(line.material)
        if rule is None:
            matches.append(_unmatched(line, "이 항목의 검색 규칙이 없다."))
            continue
        ranked = rank_candidates(rule, summaries)
        chosen = choose_match(rule, summaries)
        for candidate in ranked:
            candidate_rows.append(
                {
                    "material": line.material,
                    "process_id": candidate.summary.process_id,
                    "process_name": candidate.summary.name,
                    "version": candidate.summary.version,
                    "location": candidate.summary.location,
                    "score": candidate.score,
                    "rejected": candidate.rejected,
                    "reason": candidate.reason,
                    "selected": chosen is not None
                    and candidate.summary.process_id == chosen.summary.process_id,
                }
            )
        if chosen is None:
            matches.append(_unmatched(line, "이름 규칙에 맞는 공정이 없다."))
            continue
        process = store.load_process(chosen.summary.process_id)
        if process is None:
            matches.append(_unmatched(line, "고른 공정 JSON이 없다."))
            continue
        exchanges, _skipped = read_exchanges(process)
        reference = reference_exchange(exchanges)
        if reference is None or reference.is_input:
            matches.append(_unmatched(line, "기준 산출 흐름이 없다."))
            continue
        try:
            demand = convert_amount(line.mass_kg, "kg", reference.unit)
        except UnitConversionError as error:
            matches.append(_unmatched(line, f"완제품 질량을 기준 단위로 바꾸지 못했다: {error}"))
            continue
        matches.append(
            AcceptedMatch(
                material=line.material,
                mass_g=line.mass_g,
                part=line.part,
                process_id=chosen.summary.process_id,
                process_name=chosen.summary.name,
                version=chosen.summary.version,
                location=chosen.summary.location,
                reference_unit=reference.unit,
                demand_in_reference_unit=demand,
                rationale=rule.rationale + " " + chosen.reason,
                database_status="matched",
            )
        )
    return matches, candidate_rows


def _contributions(
    system: BuiltSystem,
    matches: list[AcceptedMatch],
    factors: dict[str, tuple[float, str]],
) -> list[dict]:
    rows: list[dict] = []
    for match in matches:
        if match.database_status != "matched":
            rows.append(
                {
                    "material": match.material,
                    "mass_g": match.mass_g,
                    "gwp100_kg_co2eq": None,
                    "status": match.database_status,
                    "process_name": "",
                }
            )
            continue
        scaling = scaling_for_demand(
            system, {match.process_id: match.demand_in_reference_unit}
        )
        impact = characterize_scaling(system, scaling, factors)
        rows.append(
            {
                "material": match.material,
                "mass_g": match.mass_g,
                "part": match.part,
                "process_id": match.process_id,
                "process_name": match.process_name,
                "gwp100_kg_co2eq": impact.characterized_kg_co2eq,
                "biogenic_co2_kg": impact.biogenic_co2_kg,
                "status": "characterized_portion_only",
            }
        )
    return rows


def _nested_match_flags(store_path: Path, matches: list[AcceptedMatch]) -> list[dict]:
    """다른 BOM 항목의 공정을 직접 투입하면 그 양을 같이 적는다."""
    store = UslciStore(store_path)
    flags: list[dict] = []
    try:
        matched = [item for item in matches if item.database_status == "matched"]
        by_id = {item.process_id: item for item in matched}
        for outer in matched:
            process = store.load_process(outer.process_id)
            if process is None:
                continue
            exchanges, _skipped = read_exchanges(process)
            for exchange in exchanges:
                inner = by_id.get(exchange.provider_id or "")
                if inner is None or inner.process_id == outer.process_id:
                    continue
                flags.append(
                    {
                        "outer_material": outer.material,
                        "inner_material": inner.material,
                        "inner_process_name": inner.process_name,
                        "direct_signed_amount": exchange.signed_amount,
                        "unit": exchange.unit,
                        "note": "바깥 공정의 기준 수량 1당 안쪽 공정을 이 양만큼 직접 투입한다. 주전자 BOM 수요와 별도이며, 같은 물리 부품을 두 번 넣은 것은 아니다.",
                    }
                )
    finally:
        store.close()
    return flags


def _monetary_proxies(store_path: Path) -> list[dict]:
    """USEEIO 금액 다리는 공급자가 이 저장소에 없으므로 총량에 넣지 않는다."""
    store = UslciStore(store_path)
    proxies: list[dict] = []
    try:
        for summary in store.summaries().values():
            if "useeio" not in summary.name.lower():
                continue
            process = store.load_process(summary.process_id)
            if process is None:
                continue
            exchanges, _skipped = read_exchanges(process)
            for exchange in exchanges:
                if exchange.unit.upper() != "USD":
                    continue
                proxies.append(
                    {
                        "process_id": summary.process_id,
                        "process_name": summary.name,
                        "version": summary.version,
                        "reference_flow": next(
                            (item.flow_name for item in exchanges if item.is_reference), ""
                        ),
                        "sector_flow": exchange.flow_name,
                        "currency": "USD",
                        "amount_usd_per_reference": abs(exchange.signed_amount),
                        "provider_id": exchange.provider_id,
                        "status": "not_calculated",
                        "reason": "금액 투입의 공급 공정이 Commons Merged에 없다. USEEIO는 Commons Merged Hybrid에 있다. 가격 연도와 구매자가격을 확인하기 전에는 영향으로 바꾸지 않는다.",
                    }
                )
    finally:
        store.close()
    return proxies


def _status(matches: list[AcceptedMatch], system: BuiltSystem, total: ImpactResult) -> str:
    unmatched = [item.material for item in matches if item.database_status != "matched"]
    if unmatched or system.unresolved_links or total.uncharacterized_flows:
        return "partial"
    return "complete"


def _unmatched(line: BomLine, reason: str) -> AcceptedMatch:
    return AcceptedMatch(
        material=line.material,
        mass_g=line.mass_g,
        part=line.part,
        process_id="",
        process_name="",
        version="",
        location="",
        reference_unit="",
        demand_in_reference_unit=0.0,
        rationale=reason,
        database_status="not_matched",
    )


def _write_outputs(
    output_dir: Path,
    result: dict,
    candidate_rows: list[dict],
    system: BuiltSystem,
    total: ImpactResult,
) -> None:
    (output_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_csv(output_dir / "contributions.csv", result["contributions"])
    _write_csv(output_dir / "mapping_table.csv", result["matches"])
    _write_csv(output_dir / "candidates.csv", candidate_rows)
    _write_csv(
        output_dir / "unresolved_links.csv",
        [asdict(item) for item in system.unresolved_links],
    )
    _write_csv(
        output_dir / "uncharacterized_flows.csv",
        [asdict(item) for item in total.uncharacterized_flows],
    )
    manifest = {
        "repository": "Federal_LCA_Commons/commons_merged",
        "download": "GET https://api.nal.usda.gov/FederalLCACommonsapi/download/json/prepare/Federal_LCA_Commons/commons_merged",
        "sha256": result["database_file_sha256"],
        "note": "zip 원본은 data/cache에만 두고 Git에는 넣지 않는다. DATA_GOV_API_KEY가 필요하다.",
    }
    (output_dir / "data_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"YAML 객체가 아니다: {path}")
    return loaded


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
