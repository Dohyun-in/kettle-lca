"""맞춘 공정에서 상류 공급자를 따라 기술행렬과 개입행렬을 만든다."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from kettle_lca.exchanges import SignedExchange, SkippedExchange, read_exchanges, reference_exchange
from kettle_lca.matrix_model import SingularTechnologyMatrixError, solve_scaling_vector
from kettle_lca.units import UnitConversionError, convert_amount
from kettle_lca.uslci_store import UslciStore


@dataclass
class UnresolvedLink:
    process_id: str
    process_name: str
    flow_id: str
    flow_name: str
    flow_type: str
    signed_amount: float
    unit: str
    provider_id: str | None
    provider_name: str | None
    reason: str


@dataclass
class ElementaryContribution:
    flow_id: str
    flow_name: str
    category: str
    unit: str
    amount: float


@dataclass
class BuiltSystem:
    process_ids: list[str]
    process_names: list[str]
    row_flow_ids: list[str]
    row_flow_names: list[str]
    row_units: list[str]
    technology_matrix: np.ndarray
    elementary_flow_ids: list[str]
    elementary_names: list[str]
    elementary_categories: list[str]
    elementary_units: list[str]
    intervention_matrix: np.ndarray
    unresolved_links: list[UnresolvedLink] = field(default_factory=list)
    skipped_exchanges: list[SkippedExchange] = field(default_factory=list)
    missing_provider_ids: list[str] = field(default_factory=list)


def collect_supply_chain(
    store: UslciStore, root_process_ids: list[str]
) -> tuple[dict[str, dict], list[str]]:
    """기본 공급자가 이 압축파일 안에 있는 동안 상류를 따라간다."""
    loaded: dict[str, dict] = {}
    missing: list[str] = []
    queue = list(dict.fromkeys(root_process_ids))
    while queue:
        process_id = queue.pop()
        if process_id in loaded or process_id in missing:
            continue
        process = store.load_process(process_id)
        if process is None:
            missing.append(process_id)
            continue
        loaded[process_id] = process
        exchanges, _skipped = read_exchanges(process)
        for exchange in exchanges:
            provider_id = exchange.provider_id
            if provider_id and provider_id not in loaded:
                queue.append(provider_id)
    return loaded, missing


def build_system(store: UslciStore, root_process_ids: list[str]) -> BuiltSystem:
    loaded, missing_provider_ids = collect_supply_chain(store, root_process_ids)
    if not loaded:
        raise SingularTechnologyMatrixError("포함한 공정이 없다.")

    process_ids = sorted(loaded)
    columns: list[list[SignedExchange]] = []
    skipped_all: list[SkippedExchange] = []
    reference_by_process: dict[str, SignedExchange] = {}
    readable_ids: list[str] = []
    for process_id in process_ids:
        exchanges, skipped = read_exchanges(loaded[process_id])
        skipped_all.extend(skipped)
        reference = reference_exchange(exchanges)
        if reference is None:
            missing_provider_ids.append(process_id)
            skipped_all.append(
                SkippedExchange(process_id, str(loaded[process_id].get("name") or ""), "기준 흐름을 읽지 못했다.")
            )
            continue
        readable_ids.append(process_id)
        reference_by_process[process_id] = reference
        columns.append(exchanges)
    process_ids = readable_ids
    if not process_ids:
        raise SingularTechnologyMatrixError("기준 흐름을 읽은 공정이 없다.")

    # 행은 흐름이 아니라 공급 공정이다. 같은 제품을 만드는 공정이 여러 개여도 기본 공급자만 연결한다.
    process_index = {process_id: position for position, process_id in enumerate(process_ids)}
    technology_matrix = np.zeros((len(process_ids), len(process_ids)), dtype=float)
    elementary_rows: dict[str, int] = {}
    elementary_flow_ids: list[str] = []
    elementary_names: list[str] = []
    elementary_categories: list[str] = []
    elementary_units: list[str] = []
    intervention_columns: list[dict[int, float]] = []
    unresolved: list[UnresolvedLink] = []

    for column, process_id in enumerate(process_ids):
        process_name = str(loaded[process_id].get("name") or process_id)
        elementary_column: dict[int, float] = {}
        reference = reference_by_process[process_id]
        technology_matrix[column, column] += reference.signed_amount
        for exchange in columns[column]:
            if exchange.is_reference:
                continue
            if exchange.flow_type == "ELEMENTARY_FLOW":
                _add_elementary(
                    exchange,
                    elementary_rows,
                    elementary_flow_ids,
                    elementary_names,
                    elementary_categories,
                    elementary_units,
                    elementary_column,
                )
                continue
            if exchange.flow_type not in {"PRODUCT_FLOW", "WASTE_FLOW"}:
                unresolved.append(
                    _unresolved(process_id, process_name, exchange, "알 수 없는 흐름 유형")
                )
                continue
            provider_id = exchange.provider_id
            provider_row = None if provider_id is None else process_index.get(provider_id)
            if provider_row is None:
                unresolved.append(
                    _unresolved(
                        process_id,
                        process_name,
                        exchange,
                        "기본 공급자가 없거나 그 공정의 기준 흐름을 읽지 못했다.",
                    )
                )
                continue
            provider_unit = reference_by_process[provider_id].unit
            try:
                amount_in_provider_unit = convert_amount(
                    exchange.signed_amount, exchange.unit, provider_unit
                )
            except UnitConversionError as error:
                unresolved.append(
                    _unresolved(process_id, process_name, exchange, str(error))
                )
                continue
            technology_matrix[provider_row, column] += amount_in_provider_unit
        intervention_columns.append(elementary_column)

    intervention_matrix = np.zeros((len(elementary_rows), len(process_ids)), dtype=float)
    for column, values in enumerate(intervention_columns):
        for row, amount in values.items():
            intervention_matrix[row, column] = amount

    return BuiltSystem(
        process_ids=process_ids,
        process_names=[str(loaded[process_id].get("name") or process_id) for process_id in process_ids],
        row_flow_ids=[reference_by_process[process_id].flow_id for process_id in process_ids],
        row_flow_names=[reference_by_process[process_id].flow_name for process_id in process_ids],
        row_units=[reference_by_process[process_id].unit for process_id in process_ids],
        technology_matrix=technology_matrix,
        elementary_flow_ids=elementary_flow_ids,
        elementary_names=elementary_names,
        elementary_categories=elementary_categories,
        elementary_units=elementary_units,
        intervention_matrix=intervention_matrix,
        unresolved_links=unresolved,
        skipped_exchanges=skipped_all,
        missing_provider_ids=missing_provider_ids,
    )


def final_demand_vector(
    system: BuiltSystem, demand_by_process_id: dict[str, float]
) -> np.ndarray:
    """공정 활동이 아니라, 그 공정의 기준 흐름 수량으로 최종 수요를 만든다."""
    demand = np.zeros(len(system.process_ids), dtype=float)
    index = {process_id: position for position, process_id in enumerate(system.process_ids)}
    for process_id, amount in demand_by_process_id.items():
        position = index.get(process_id)
        if position is None:
            raise SingularTechnologyMatrixError(f"수요 공정이 시스템에 없다: {process_id}")
        demand[position] += amount
    return demand


def scaling_for_demand(system: BuiltSystem, demand_by_process_id: dict[str, float]) -> np.ndarray:
    return solve_scaling_vector(
        system.technology_matrix, final_demand_vector(system, demand_by_process_id)
    )


def _add_elementary(
    exchange: SignedExchange,
    elementary_rows: dict[str, int],
    flow_ids: list[str],
    names: list[str],
    categories: list[str],
    units: list[str],
    column: dict[int, float],
) -> None:
    key = f"{exchange.flow_id}|{exchange.unit}"
    row = elementary_rows.get(key)
    if row is None:
        row = len(elementary_rows)
        elementary_rows[key] = row
        flow_ids.append(exchange.flow_id)
        names.append(exchange.flow_name)
        categories.append(exchange.category)
        units.append(exchange.unit)
    column[row] = column.get(row, 0.0) + exchange.signed_amount


def _unresolved(
    process_id: str, process_name: str, exchange: SignedExchange, reason: str
) -> UnresolvedLink:
    return UnresolvedLink(
        process_id=process_id,
        process_name=process_name,
        flow_id=exchange.flow_id,
        flow_name=exchange.flow_name,
        flow_type=exchange.flow_type,
        signed_amount=exchange.signed_amount,
        unit=exchange.unit,
        provider_id=exchange.provider_id,
        provider_name=exchange.provider_name,
        reason=reason,
    )


