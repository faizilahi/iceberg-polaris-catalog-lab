"""Initialize census_fact metadata and snapshot 1 data files."""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "rest_standin" / "hf" / "census_fact"
WH = ROOT / "warehouse" / "hf" / "census_fact"
CATALOG.mkdir(parents=True, exist_ok=True)
WH.mkdir(parents=True, exist_ok=True)
random.seed(3)

con = duckdb.connect()
rows = []
base = date(2025, 8, 1)
for d in range(3):
    for f in range(1, 11):
        rows.append(
            (
                (base + timedelta(days=d)).isoformat(),
                f"F-{f:03d}",
                random.randint(20, 200),
            )
        )

snap_dir = WH / "snap_1"
snap_dir.mkdir(exist_ok=True)
con.execute("CREATE OR REPLACE TABLE census AS SELECT * FROM (SELECT 1) WHERE 0")
con.execute("CREATE OR REPLACE TABLE census (census_date DATE, facility_id VARCHAR, census_count INTEGER)")
con.executemany("INSERT INTO census VALUES (?, ?, ?)", rows)
path = snap_dir / "data.parquet"
con.execute(f"COPY census TO '{path.as_posix()}' (FORMAT PARQUET)")

schema_v1 = {
    "schema-id": 1,
    "fields": [
        {"id": 1, "name": "census_date", "type": "date", "required": True},
        {"id": 2, "name": "facility_id", "type": "string", "required": True},
        {"id": 3, "name": "census_count", "type": "int", "required": True},
    ],
}
(CATALOG / "schemas.json").write_text(
    json.dumps({"current_schema_id": 1, "schemas": [schema_v1]}, indent=2),
    encoding="utf-8",
)

metadata = {
    "table": "hf.census_fact",
    "format": "iceberg-standin",
    "current_snapshot_id": 1,
    "current_schema_id": 1,
    "location": str(WH),
    "catalog_note": "REST catalog stand-in (Polaris-style) — local files only",
}
(CATALOG / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

snap = {
    "snapshot_id": 1,
    "parent_id": None,
    "operation": "append",
    "schema_id": 1,
    "manifest_files": [str(path)],
    "summary": {"added-records": len(rows), "census_dates": 3},
}
with (CATALOG / "snapshots.jsonl").open("w", encoding="utf-8") as fh:
    fh.write(json.dumps(snap) + "\n")

print(f"snapshot_1_records={len(rows)} path={path}")
