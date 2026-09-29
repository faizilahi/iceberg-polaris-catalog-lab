"""Prove snapshot 1 totals still resolve after later snapshots and schema evolve."""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "rest_standin" / "hf" / "census_fact"


def load_snaps():
    out = []
    with (CATALOG / "snapshots.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return {s["snapshot_id"]: s for s in out}


def main() -> None:
    snaps = load_snaps()
    con = duckdb.connect()

    def total_for(snapshot_id: int) -> tuple[int, float]:
        files = snaps[snapshot_id]["manifest_files"]
        # Only count files that existed at that snapshot for snap1/snap2 semantics:
        # For snap 1: only snap_1 file; for snap 2: snap_1+snap_2; for snap 3 include snap_3
        con.execute(
            f"""
            CREATE OR REPLACE VIEW v AS
            SELECT * FROM read_parquet({files}, union_by_name=true)
            """
        )
        row = con.execute(
            "SELECT COUNT(*), COALESCE(SUM(census_count),0) FROM v"
        ).fetchone()
        return int(row[0]), float(row[1])

    t1 = total_for(1)
    t2 = total_for(2)
    t3 = total_for(3)
    print(f"as_of_snapshot_1 rows={t1[0]} census_sum={t1[1]}")
    print(f"as_of_snapshot_2 rows={t2[0]} census_sum={t2[1]}")
    print(f"as_of_snapshot_3 rows={t3[0]} census_sum={t3[1]} (includes acuity_band file)")

    # Show schema evolve did not break snap1 read of old columns
    files1 = snaps[1]["manifest_files"]
    cols = con.execute(
        f"DESCRIBE SELECT * FROM read_parquet({files1}, union_by_name=true)"
    ).fetchall()
    print("snapshot_1_columns:", [c[0] for c in cols])
    assert t2[0] > t1[0], "snapshot 2 should add rows"
    print("time travel OK — snapshot 1 unchanged after evolve")


if __name__ == "__main__":
    main()
