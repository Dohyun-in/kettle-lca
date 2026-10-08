"""DATA_GOV_API_KEY로 Commons Merged JSON-LD를 data/cache에 받는다."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

BASE_URL = "https://api.nal.usda.gov/FederalLCACommonsapi"
GROUP = "Federal_LCA_Commons"
REPOSITORY = "commons_merged"


def download_commons_merged(destination: Path, api_key: str) -> None:
    if not api_key.strip():
        raise RuntimeError("DATA_GOV_API_KEY가 비어 있다.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    prepared = requests.get(
        f"{BASE_URL}/download/json/prepare/{GROUP}/{REPOSITORY}",
        params={"api_key": api_key},
        timeout=120,
    )
    prepared.raise_for_status()
    token = prepared.text.strip()
    if not token or token.startswith("<"):
        raise RuntimeError("다운로드 토큰을 받지 못했다.")
    response = requests.get(
        f"{BASE_URL}/download/json/{token}",
        params={"api_key": api_key},
        timeout=600,
        stream=True,
    )
    response.raise_for_status()
    temporary = destination.with_suffix(".zip.partial")
    with temporary.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                handle.write(chunk)
    temporary.replace(destination)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    api_key = os.environ.get("DATA_GOV_API_KEY", "")
    destination = project_root / "data" / "cache" / "commons_merged.zip"
    try:
        download_commons_merged(destination, api_key)
    except (OSError, requests.RequestException, RuntimeError) as error:
        print(f"데이터베이스를 받지 못했다: {error}", file=sys.stderr)
        sys.exit(1)
    print(destination)


if __name__ == "__main__":
    main()
