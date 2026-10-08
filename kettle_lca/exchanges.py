"""openLCA JSON-LD 교환을 부호 있는 수량으로 읽는다."""

from __future__ import annotations

from dataclasses import dataclass

from kettle_lca.units import UnitConversionError, convert_amount


@dataclass(frozen=True)
class SignedExchange:
    flow_id: str
    flow_name: str
    flow_type: str
    category: str
    unit: str
    signed_amount: float
    provider_id: str | None
    provider_name: str | None
    is_reference: bool
    is_input: bool


@dataclass(frozen=True)
class SkippedExchange:
    process_id: str
    flow_name: str
    reason: str


def read_exchanges(
    process: dict,
) -> tuple[list[SignedExchange], list[SkippedExchange]]:
    """산출은 양수, 투입은 음수로 읽는다. 기준 흐름 단위로 환산한다."""
    process_id = str(process.get("@id") or "")
    accepted: list[SignedExchange] = []
    skipped: list[SkippedExchange] = []
    for exchange in process.get("exchanges") or []:
        if not isinstance(exchange, dict):
            skipped.append(SkippedExchange(process_id, "", "교환이 객체가 아니다."))
            continue
        parsed, skip = _parse_one_exchange(process_id, exchange)
        if skip is not None:
            skipped.append(skip)
        if parsed is not None:
            accepted.append(parsed)
    return accepted, skipped


def reference_exchange(exchanges: list[SignedExchange]) -> SignedExchange | None:
    references = [item for item in exchanges if item.is_reference]
    if len(references) != 1:
        return None
    return references[0]


def _parse_one_exchange(
    process_id: str, exchange: dict
) -> tuple[SignedExchange | None, SkippedExchange | None]:
    flow = exchange.get("flow")
    if not isinstance(flow, dict):
        return None, SkippedExchange(process_id, "", "흐름 객체가 없다.")
    flow_name = str(flow.get("name") or "")
    flow_id = flow.get("@id")
    if not isinstance(flow_id, str) or not flow_id:
        return None, SkippedExchange(process_id, flow_name, "흐름 UUID가 없다.")
    raw_amount = exchange.get("amount")
    if isinstance(raw_amount, bool) or not isinstance(raw_amount, (int, float)):
        return None, SkippedExchange(process_id, flow_name, "수량이 숫자가 아니다.")
    unit_name = _unit_name(exchange.get("unit"))
    reference_unit = flow.get("refUnit") or unit_name
    if not isinstance(reference_unit, str) or not unit_name:
        return None, SkippedExchange(process_id, flow_name, "단위가 없다.")
    try:
        amount_in_reference_unit = convert_amount(float(raw_amount), unit_name, reference_unit)
    except UnitConversionError as error:
        return None, SkippedExchange(process_id, flow_name, str(error))
    is_input = bool(exchange.get("isInput"))
    signed_amount = -amount_in_reference_unit if is_input else amount_in_reference_unit
    provider = exchange.get("defaultProvider")
    provider_id = None
    provider_name = None
    if isinstance(provider, dict) and isinstance(provider.get("@id"), str):
        provider_id = provider["@id"]
        provider_name = str(provider.get("name") or "")
    return (
        SignedExchange(
            flow_id=flow_id,
            flow_name=flow_name,
            flow_type=str(flow.get("flowType") or ""),
            category=str(flow.get("category") or ""),
            unit=reference_unit,
            signed_amount=signed_amount,
            provider_id=provider_id,
            provider_name=provider_name,
            is_reference=bool(exchange.get("isQuantitativeReference")),
            is_input=is_input,
        ),
        None,
    )


def _unit_name(unit: object) -> str | None:
    if isinstance(unit, dict) and isinstance(unit.get("name"), str):
        return unit["name"]
    return None
