"""Append snapshot 2 data, then schema-evolve for snapshot 3."""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "rest_standin" / "hf" / "census_fact"
WH = ROOT / "warehouse" / "hf" / "census_fact"
random.seed(4)
con = duckdb.connect()

# Snapshot 2: two more days
rows = []
base = date(2025, 8, 4)
for d in range(2):
    for f in range(1, 11):
        rows.append(((base + timedelta(days=d)).isoformat(), f"F-{f:03d}", random.randint(20, 200)))

snap2_dir = WH / "snap_2"
snap2_dir.mkdir(exist_ok=True)
con.execute("CREATE OR REPLACE TABLE census (census_date DATE, facility_id VARCHAR, census_count INTEGER)")
con.executemany("INSERT INTO census VALUES (?, ?, ?)", rows)
path2 = snap2_dir / "data.parquet"
con.execute(f"COPY census TO '{path2.as_posix()}' (FORMAT PARQUET)")

# Load existing snapshots
snaps = []
with (CATALOG / "snapshots.jsonl").open(encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            snaps.append(json.loads(line))

# Manifest for snapshot 2 includes snap_1 + snap_2 files (append semantics)
snap1_files = snaps[0]["manifest_files"]
snap2 = {
    "snapshot_id": 2,
    "parent_id": 1,
    "operation": "append",
    "schema_id": 1,
    "manifest_files": snap1_files + [str(path2)],
    "summary": {"added-records": len(rows), "total-manifest-files": 2},
}

# Snapshot 3: schema evolve + rewrite with acuity_band
schemas = json.loads((CATALOG / "schemas.json").read_text(encoding="utf-8"))
schema_v2 = {
    "schema-id": 2,
    "fields": schemas["schemas"][0]["fields"]
    + [{"id": 4, "name": "acuity_band", "type": "string", "required": False}],
}
schemas["current_schema_id"] = 2
schemas["schemas"].append(schema_v2)
(CATALOG / "schemas.json").write_text(json.dumps(schemas, indent=2), encoding="utf-8")

# New data file with the extra column (old files untouched)
con.execute(
    """
    CREATE OR REPLACE TABLE census3 AS
    SELECT census_date, facility_id, census_count,
           CASE WHEN census_count > 150 THEN 'HIGH'
                WHEN census_count > 80 THEN 'MED' ELSE 'LOW' END AS acuity_band
    FROM census
    """
)
snap3_dir = WH / "snap_3"
snap3_dir.mkdir(exist_ok=True)
path3 = snap3_dir / "data.parquet"
con.execute(f"COPY census3 TO '{path3.as_posix()}' (FORMAT PARQUET)")

snap3 = {
    "snapshot_id": 3,
    "parent_id": 2,
    "operation": "schema-evolve-add-column",
    "schema_id": 2,
    "manifest_files": snap1_files + [str(path2), str(path3)],
    "summary": {
        "added-column": "acuity_band",
        "note": "Old parquet files remain readable under schema-id 1 snapshots",
    },
}

with (CATALOG / "snapshots.jsonl").open("w", encoding="utf-8") as fh:
    for s in [snaps[0], snap2, snap3]:
        fh.write(json.dumps(s) + "\n")

meta = json.loads((CATALOG / "metadata.json").read_text(encoding="utf-8"))
meta["current_snapshot_id"] = 3
meta["current_schema_id"] = 2
(CATALOG / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
print("snapshots=1,2,3 written; schema evolved with acuity_band")
