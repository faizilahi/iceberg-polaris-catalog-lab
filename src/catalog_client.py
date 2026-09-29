"""Minimal REST-catalog client that reads the local Polaris stand-in JSON tree."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDIN = ROOT / "catalog" / "rest_standin"


@dataclass
class TableHandle:
    namespace: tuple[str, ...]
    name: str
    metadata_path: Path

    def metadata(self) -> dict:
        return json.loads(self.metadata_path.read_text(encoding="utf-8"))

    def snapshots(self) -> list[dict]:
        snap_path = self.metadata_path.parent / "snapshots.jsonl"
        out = []
        for line in snap_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out

    def schemas(self) -> dict:
        return json.loads((self.metadata_path.parent / "schemas.json").read_text(encoding="utf-8"))


class RestCatalogStandin:
    """Stand-in for Iceberg REST / Polaris — file-backed, no HTTP server."""

    def __init__(self, root: Path = STANDIN) -> None:
        self.root = root
        self.config = json.loads((root / "config.json").read_text(encoding="utf-8"))

    def list_namespaces(self) -> list[list[str]]:
        return json.loads((self.root / "namespaces.json").read_text(encoding="utf-8"))["namespaces"]

    def load_table(self, namespace: str, name: str) -> TableHandle:
        meta = self.root / namespace / name / "metadata.json"
        if not meta.exists():
            raise FileNotFoundError(f"table not registered: {namespace}.{name}")
        return TableHandle(namespace=(namespace,), name=name, metadata_path=meta)

    def current_snapshot(self, handle: TableHandle) -> dict:
        meta = handle.metadata()
        sid = meta["current_snapshot_id"]
        for s in handle.snapshots():
            if s["snapshot_id"] == sid:
                return s
        raise KeyError(sid)


def print_catalog_summary() -> None:
    cat = RestCatalogStandin()
    print("config:", cat.config)
    print("namespaces:", cat.list_namespaces())
    t = cat.load_table("hf", "census_fact")
    print("table metadata:", t.metadata())
    print("snapshot_count:", len(t.snapshots()))
    for s in t.snapshots():
        print(" ", s["snapshot_id"], s["operation"], s.get("summary"))
    print("schemas:", t.schemas()["current_schema_id"])


if __name__ == "__main__":
    print_catalog_summary()
