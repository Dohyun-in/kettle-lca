"""TianGong CLI로 공정을 검색한다. 비밀번호와 토큰은 다루지 않는다."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


CLI_PACKAGE = "@tiangong-lca/cli@0.1.21"


def search_processes(query: str, work_directory: Path) -> dict:
    """로그인된 로컬 세션으로 공정 검색을 시도한다."""
    node = shutil.which("node")
    npx = shutil.which("npx")
    if node is None or npx is None:
        return {"status": "not_available", "reason": "node 또는 npx가 없다.", "query": query}
    request_path = work_directory / "tiangong-search.request.json"
    request_path.write_text(
        json.dumps({"query": query}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    command = [
        npx,
        "--yes",
        CLI_PACKAGE,
        "search",
        "process",
        "--input",
        str(request_path),
        "--json",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=work_directory,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"status": "failed", "reason": str(error), "query": query}
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "").strip()
        status = "login_required" if "login" in message.lower() else "failed"
        return {
            "status": status,
            "reason": message[:2000],
            "query": query,
            "returncode": completed.returncode,
        }
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return {"status": "failed", "reason": f"JSON이 아니다: {error}", "query": query}
    return {"status": "retrieved", "query": query, "payload": payload}
