"""수업 예시와 단위 환산이 깨지지 않는지 확인한다."""

import numpy as np

from kettle_lca.bom import bom_mass_totals, load_bom
from kettle_lca.matrix_model import solve_inventory
from kettle_lca.units import convert_amount
from pathlib import Path


def test_suh_heijungs_electricity_example() -> None:
    technology_matrix = np.array([[1500.0, -3000.0], [-0.01, 0.1]])
    intervention_matrix = np.array([[20.0, 10.0]])
    characterization = np.array([[1.0]])
    final_demand = np.array([1.0, 0.0])
    solution = solve_inventory(
        technology_matrix, intervention_matrix, characterization, final_demand
    )
    assert abs(float(solution.elementary_flows[0]) - 0.0175) < 1e-12


def test_pound_to_kilogram() -> None:
    assert abs(convert_amount(1, "lb av", "kg") - 0.45359237) < 1e-12


def test_megawatt_hour_to_megajoule() -> None:
    assert abs(convert_amount(1, "MWh", "MJ") - 3600.0) < 1e-9


def test_bom_totals() -> None:
    bom = load_bom(Path(__file__).resolve().parents[1] / "data" / "bom.csv")
    totals = bom_mass_totals(bom)
    assert abs(totals["kettle_g"] - 723.0) < 1e-9
    assert abs(totals["packaging_g"] - 137.8) < 1e-9
    assert abs(totals["total_g"] - 860.8) < 1e-9
