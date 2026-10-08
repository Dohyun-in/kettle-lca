"""python -m kettle_lca 로 독립 실행 결과를 results/에 쓴다."""

from __future__ import annotations

import json
from pathlib import Path

from kettle_lca.study_run import run_study


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    result = run_study(project_root)
    summary = {
        "calculation_status": result["calculation_status"],
        "characterized_gwp100_kg_co2eq": result["characterized_gwp100_kg_co2eq"],
        "process_count": result["process_count"],
        "unresolved_link_count": result["unresolved_link_count"],
        "uncharacterized_flow_count": result["uncharacterized_flow_count"],
        "bom_check": result["bom_check"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
