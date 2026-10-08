"""IPCC AR6 100년 지구온난화지수. 표에 없는 흐름은 0으로 넣지 않고 미특성으로 남긴다."""

from __future__ import annotations

from dataclasses import dataclass

# IPCC AR6 WGI, GWP100. 화석 메탄 29.8, 비화석 메탄 27.2, 아산화질소 273.
FOSSIL_METHANE_GWP100 = 29.8
NONFOSSIL_METHANE_GWP100 = 27.2
NITROUS_OXIDE_GWP100 = 273.0
CARBON_DIOXIDE_GWP100 = 1.0


@dataclass(frozen=True)
class CharacterizedFlow:
    flow_id: str
    flow_name: str
    category: str
    amount: float
    unit: str
    factor_kg_co2eq_per_unit: float | None
    impact_kg_co2eq: float | None
    treatment: str


def _normalized(text: str) -> str:
    return " ".join(text.lower().replace("_", " ").replace("-", " ").split())


def gwp100_factor(flow_name: str, category: str) -> tuple[float | None, str]:
    """흐름 이름과 분류로 GWP100 계수를 고른다. 모르면 (None, 이유)."""
    name = _normalized(flow_name)
    compartment = _normalized(category)
    biogenic = "biogenic" in name or "non fossil" in name or "non-fossil" in compartment
    fossil_marker = "fossil" in name or "fossil" in compartment

    if "carbon dioxide" in name or name in {"co2", "carbon dioxide, fossil"}:
        if biogenic or "from soil or biomass" in name:
            return 0.0, "biogenic_co2_reported_separately"
        return CARBON_DIOXIDE_GWP100, "fossil_co2"

    if name in {"methane", "ch4"} or name.startswith("methane "):
        if biogenic and not fossil_marker:
            return NONFOSSIL_METHANE_GWP100, "nonfossil_methane"
        return FOSSIL_METHANE_GWP100, "fossil_methane"

    if name in {"dinitrogen monoxide", "nitrous oxide", "n2o"} or "dinitrogen monoxide" in name:
        return NITROUS_OXIDE_GWP100, "nitrous_oxide"

    return None, "no_gwp100_factor_in_the_project_table"
