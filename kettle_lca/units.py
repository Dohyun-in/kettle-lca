"""교환 단위를 흐름의 기준 단위로 바꾼다."""

from __future__ import annotations

# 같은 차원 안에서 kg, MJ, m, m3, unit 기준으로 나눈 환산 계수.
_TO_BASE: dict[str, tuple[str, float]] = {
    "kg": ("mass", 1.0),
    "g": ("mass", 0.001),
    "mg": ("mass", 1e-6),
    "t": ("mass", 1000.0),
    "ton": ("mass", 1000.0),
    "tonne": ("mass", 1000.0),
    "metric ton": ("mass", 1000.0),
    "short ton": ("mass", 907.18474),
    "sh tn": ("mass", 907.18474),
    "lb": ("mass", 0.45359237),
    "lb av": ("mass", 0.45359237),
    "lbs": ("mass", 0.45359237),
    "pound": ("mass", 0.45359237),
    "oz": ("mass", 0.028349523125),
    "mj": ("energy", 1.0),
    "kj": ("energy", 0.001),
    "j": ("energy", 1e-6),
    "kwh": ("energy", 3.6),
    "mwh": ("energy", 3600.0),
    "wh": ("energy", 0.0036),
    "kcal": ("energy", 0.004184),
    "btu": ("energy", 0.00105505585262),
    "mmbtu": ("energy", 1055.05585262),
    "m": ("length", 1.0),
    "km": ("length", 1000.0),
    "ft": ("length", 0.3048),
    "mm": ("length", 0.001),
    "m3": ("volume", 1.0),
    "l": ("volume", 0.001),
    "cu ft": ("volume", 0.028316846592),
    "gal(usliq)": ("volume", 0.003785411784),
    "gal(usfl)": ("volume", 0.003785411784),
    "gal(imp)": ("volume", 0.00454609),
    "liter": ("volume", 0.001),
    "litre": ("volume", 0.001),
    "gal": ("volume", 0.003785411784),
    "gallon": ("volume", 0.003785411784),
    "t*km": ("transport", 1.0),
    "tkm": ("transport", 1.0),
    "ton*km": ("transport", 1.0),
    "kg*km": ("transport", 0.001),
    "t*mi": ("transport", 1.609344),
    "m2": ("area", 1.0),
    "ha": ("area", 10000.0),
    "ft2": ("area", 0.09290304),
    "m2*a": ("area_time", 1.0),
    "ha*a": ("area_time", 10000.0),
    "bq": ("activity", 1.0),
    "kbq": ("activity", 1000.0),
    "item": ("count", 1.0),
    "unit": ("count", 1.0),
    "p": ("count", 1.0),
}


class UnitConversionError(ValueError):
    """단위를 공통 기준으로 맞출 수 없을 때."""


def normalize_unit_name(unit_name: str | None) -> str:
    if unit_name is None:
        raise UnitConversionError("단위 이름이 비어 있다.")
    cleaned = unit_name.strip().lower().replace(" ", "")
    aliases = {
        "lbav": "lb av",
        "lbs.": "lb",
        "kilogram": "kg",
        "kilograms": "kg",
        "gram": "g",
        "grams": "g",
        "shortton": "short ton",
        "metricton": "metric ton",
        "kwh": "kwh",
        "kw*h": "kwh",
        "m^3": "m3",
        "m³": "m3",
        "t.km": "t*km",
        "ton.km": "ton*km",
    }
    compact = cleaned.replace("*", "")
    compacted_aliases = {
        "mwh": "mwh",
        "cuft": "cu ft",
        "shtn": "sh tn",
        "gal(usliq)": "gal(usliq)",
        "gal(usfl)": "gal(usfl)",
        "gal(imp)": "gal(imp)",
        "kgkm": "kg*km",
        "tmi": "t*mi",
        "ft2": "ft2",
        "haa": "ha*a",
        "m2a": "m2*a",
    }
    if cleaned in aliases:
        return aliases[cleaned]
    if cleaned in compacted_aliases:
        return compacted_aliases[cleaned]
    if compact in {"tkm", "tonkm"}:
        return "t*km" if compact == "tkm" else "ton*km"
    return cleaned


def convert_amount(amount: float, from_unit: str | None, to_unit: str | None) -> float:
    """from_unit 수량을 to_unit 수량으로 바꾼다."""
    source = normalize_unit_name(from_unit)
    target = normalize_unit_name(to_unit)
    if source == target:
        return float(amount)
    if source not in _TO_BASE or target not in _TO_BASE:
        raise UnitConversionError(f"알 수 없는 단위 변환: {from_unit} -> {to_unit}")
    source_dimension, source_factor = _TO_BASE[source]
    target_dimension, target_factor = _TO_BASE[target]
    if source_dimension != target_dimension:
        raise UnitConversionError(
            f"차원이 다르다: {from_unit}({source_dimension}) -> {to_unit}({target_dimension})"
        )
    if target_factor == 0:
        raise UnitConversionError(f"기준 계수가 0이다: {to_unit}")
    return float(amount) * source_factor / target_factor
