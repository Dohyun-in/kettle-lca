"""기초흐름 벡터에 Commons Merged의 IPCC AR6-100 계수를 적용한다."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from kettle_lca.system_builder import BuiltSystem
from kettle_lca.units import UnitConversionError, convert_amount

AR6_100_CATEGORY_ID = "a6206006-65bc-395c-8dc9-f12262f45a04"
AR6_100_ZIP_PATH = f"lcia_categories/{AR6_100_CATEGORY_ID}.json"


@dataclass(frozen=True)
class FlowImpact:
    flow_id: str
    flow_name: str
    category: str
    amount_in_inventory_unit: float
    unit: str
    amount_kg: float | None
    factor: float | None
    impact_kg_co2eq: float | None
    treatment: str


@dataclass(frozen=True)
class ImpactResult:
    characterized_kg_co2eq: float
    biogenic_co2_kg: float
    flows: list[FlowImpact]

    @property
    def uncharacterized_flows(self) -> list[FlowImpact]:
        return [item for item in self.flows if item.impact_kg_co2eq is None and item.amount_in_inventory_unit != 0]


def load_ar6_100_factors(zip_path: Path) -> dict[str, tuple[float, str]]:
    """흐름 UUID별 (계수, 계수 단위). 계수 0도 방법이 준 값이므로 빠뜨리지 않는다."""
    with zipfile.ZipFile(zip_path) as archive:
        category = json.loads(archive.read(AR6_100_ZIP_PATH))
    factors: dict[str, tuple[float, str]] = {}
    for item in category.get("impactFactors") or []:
        flow = item.get("flow") or {}
        flow_id = flow.get("@id")
        unit = (item.get("unit") or {}).get("name")
        value = item.get("value")
        if not isinstance(flow_id, str) or not isinstance(unit, str):
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        previous = factors.get(flow_id)
        if previous is not None and previous != (float(value), unit):
            raise ValueError(f"AR6-100 계수가 한 흐름에 두 값이다: {flow_id}")
        factors[flow_id] = (float(value), unit)
    if not factors:
        raise ValueError("AR6-100 특성화 계수를 찾지 못했다.")
    return factors


def characterize_scaling(
    system: BuiltSystem,
    scaling_vector: np.ndarray,
    factors: dict[str, tuple[float, str]],
) -> ImpactResult:
    inventory = system.intervention_matrix @ scaling_vector
    flows: list[FlowImpact] = []
    total = 0.0
    biogenic_co2_kg = 0.0
    for index, amount in enumerate(inventory):
        if abs(float(amount)) < 1e-18:
            continue
        flow_id = system.elementary_flow_ids[index]
        published = factors.get(flow_id)
        factor = None if published is None else published[0]
        factor_unit = None if published is None else published[1]
        amount_kg, impact, treatment = _impact_or_gap(
            float(amount), system.elementary_units[index], factor, factor_unit
        )
        name = system.elementary_names[index].lower()
        if "carbon dioxide, biogenic" in name and amount_kg is not None:
            biogenic_co2_kg += amount_kg
        if impact is not None:
            total += impact
        flows.append(
            FlowImpact(
                flow_id=flow_id,
                flow_name=system.elementary_names[index],
                category=system.elementary_categories[index],
                amount_in_inventory_unit=float(amount),
                unit=system.elementary_units[index],
                amount_kg=amount_kg,
                factor=factor,
                impact_kg_co2eq=impact,
                treatment=treatment,
            )
        )
    flows.sort(key=lambda item: abs(item.impact_kg_co2eq or 0.0), reverse=True)
    return ImpactResult(total, biogenic_co2_kg, flows)


def _impact_or_gap(
    amount: float,
    inventory_unit: str,
    factor: float | None,
    factor_unit: str | None,
) -> tuple[float | None, float | None, str]:
    if factor is None or factor_unit is None:
        return None, None, "no_factor_in_ipcc_ar6_100"
    try:
        amount_in_factor_unit = convert_amount(amount, inventory_unit, factor_unit)
        amount_kg = convert_amount(amount, inventory_unit, "kg")
    except UnitConversionError:
        return None, None, "unit_conversion_failed"
    treatment = "characterized_as_zero" if factor == 0 else "characterized"
    return amount_kg, factor * amount_in_factor_unit, treatment
