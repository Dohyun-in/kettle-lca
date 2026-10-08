"""주전자 BOM을 읽는다."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BomLine:
    material: str
    mass_g: float
    part: str

    @property
    def mass_kg(self) -> float:
        return self.mass_g / 1000.0


def load_bom(path: Path) -> list[BomLine]:
    lines: list[BomLine] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"material", "mass_g", "part"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"BOM 열이 부족하다: {path}")
        for row in reader:
            material = (row.get("material") or "").strip()
            if not material:
                continue
            try:
                mass_g = float(row["mass_g"])
            except (TypeError, ValueError) as error:
                raise ValueError(f"질량이 숫자가 아니다: {material}") from error
            if mass_g < 0:
                raise ValueError(f"질량이 음수다: {material}")
            lines.append(BomLine(material, mass_g, (row.get("part") or "").strip()))
    if not lines:
        raise ValueError(f"BOM이 비어 있다: {path}")
    return lines


def bom_mass_totals(lines: list[BomLine]) -> dict[str, float]:
    kettle_g = sum(line.mass_g for line in lines if line.part == "Kettle")
    packaging_g = sum(line.mass_g for line in lines if line.part == "Packaging")
    return {
        "kettle_g": kettle_g,
        "packaging_g": packaging_g,
        "total_g": kettle_g + packaging_g,
    }
