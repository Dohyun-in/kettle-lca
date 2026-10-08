"""Suh & Heijungs 행렬식. A s = f, g = B s, h = C g."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


class SingularTechnologyMatrixError(RuntimeError):
    """기술행렬이 해를 갖지 않을 때. 결과를 0으로 바꾸지 않는다."""


@dataclass(frozen=True)
class InventorySolution:
    scaling_vector: np.ndarray
    elementary_flows: np.ndarray
    impact: np.ndarray


def solve_scaling_vector(technology_matrix: np.ndarray, final_demand: np.ndarray) -> np.ndarray:
    """A s = f 를 역행렬 없이 푼다."""
    if technology_matrix.ndim != 2 or technology_matrix.shape[0] != technology_matrix.shape[1]:
        raise SingularTechnologyMatrixError(
            f"기술행렬이 정사각이 아니다: {technology_matrix.shape}"
        )
    if technology_matrix.shape[0] == 0:
        raise SingularTechnologyMatrixError("기술행렬이 비어 있다.")
    try:
        return np.linalg.solve(technology_matrix, final_demand)
    except np.linalg.LinAlgError as error:
        raise SingularTechnologyMatrixError("기술행렬의 해를 구할 수 없다.") from error


def aggregate_elementary_flows(
    intervention_matrix: np.ndarray, scaling_vector: np.ndarray
) -> np.ndarray:
    """g = B s."""
    return intervention_matrix @ scaling_vector


def characterize_impacts(
    characterization_matrix: np.ndarray, elementary_flows: np.ndarray
) -> np.ndarray:
    """h = C g."""
    return characterization_matrix @ elementary_flows


def solve_inventory(
    technology_matrix: np.ndarray,
    intervention_matrix: np.ndarray,
    characterization_matrix: np.ndarray,
    final_demand: np.ndarray,
) -> InventorySolution:
    scaling_vector = solve_scaling_vector(technology_matrix, final_demand)
    elementary_flows = aggregate_elementary_flows(intervention_matrix, scaling_vector)
    impact = characterize_impacts(characterization_matrix, elementary_flows)
    return InventorySolution(scaling_vector, elementary_flows, impact)
