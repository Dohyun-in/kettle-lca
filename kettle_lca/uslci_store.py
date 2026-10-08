"""Commons Merged JSON-LD 압축파일을 읽어 공정 색인을 만든다."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path


class UslciStoreError(RuntimeError):
    """로컬 데이터베이스를 열거나 해석하지 못했을 때."""


@dataclass(frozen=True)
class ProcessSummary:
    process_id: str
    name: str
    version: str
    category: str
    location: str
    process_type: str
    zip_path: str


class UslciStore:
    """zip 안의 Process JSON만 색인한다."""

    def __init__(self, zip_path: Path) -> None:
        if not zip_path.is_file():
            raise UslciStoreError(f"데이터베이스 파일이 없다: {zip_path}")
        self.zip_path = zip_path
        self._archive = zipfile.ZipFile(zip_path)
        self._summaries: dict[str, ProcessSummary] | None = None
        self._path_by_id: dict[str, str] | None = None

    def close(self) -> None:
        self._archive.close()

    def summaries(self) -> dict[str, ProcessSummary]:
        if self._summaries is None:
            self._load_index()
        assert self._summaries is not None
        return self._summaries

    def load_process(self, process_id: str) -> dict | None:
        if self._path_by_id is None:
            self._load_index()
        assert self._path_by_id is not None
        zip_path = self._path_by_id.get(process_id)
        if zip_path is None:
            return None
        try:
            payload = json.loads(self._archive.read(zip_path))
        except (KeyError, json.JSONDecodeError) as error:
            raise UslciStoreError(f"공정 JSON을 읽지 못했다: {process_id}") from error
        if not isinstance(payload, dict):
            raise UslciStoreError(f"공정 JSON 형식이 객체가 아니다: {process_id}")
        return payload

    def _load_index(self) -> None:
        summaries: dict[str, ProcessSummary] = {}
        path_by_id: dict[str, str] = {}
        for info in self._archive.infolist():
            if info.is_dir() or not info.filename.endswith(".json"):
                continue
            if "process" not in info.filename.lower():
                continue
            try:
                payload = json.loads(self._archive.read(info))
            except json.JSONDecodeError:
                continue
            records = payload if isinstance(payload, list) else [payload]
            for record in records:
                summary = _summary_from_record(record, info.filename)
                if summary is None:
                    continue
                summaries[summary.process_id] = summary
                path_by_id[summary.process_id] = info.filename
        if not summaries:
            raise UslciStoreError("압축파일에서 Process 레코드를 찾지 못했다.")
        self._summaries = summaries
        self._path_by_id = path_by_id


def _summary_from_record(record: object, zip_path: str) -> ProcessSummary | None:
    if not isinstance(record, dict):
        return None
    if record.get("@type") != "Process":
        return None
    process_id = record.get("@id")
    name = record.get("name")
    if not isinstance(process_id, str) or not isinstance(name, str):
        return None
    location = record.get("location")
    location_name = location.get("name") if isinstance(location, dict) else ""
    return ProcessSummary(
        process_id=process_id,
        name=name,
        version=str(record.get("version") or ""),
        category=str(record.get("category") or ""),
        location=str(location_name or ""),
        process_type=str(record.get("processType") or ""),
        zip_path=zip_path,
    )
