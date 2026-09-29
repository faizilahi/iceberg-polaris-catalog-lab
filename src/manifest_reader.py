"""Read snapshot manifests and project columns for a pinned schema-id."""
from __future__ import annotations

import duckdb

from src.catalog_client import RestCatalogStandin


def read_snapshot(snapshot_id: int):
    cat = RestCatalogStandin()
    handle = cat.load_table("hf", "census_fact")
    snaps = {s["snapshot_id"]: s for s in handle.snapshots()}
    if snapshot_id not in snaps:
        raise KeyError(f"unknown snapshot {snapshot_id}")
    files = snaps[snapshot_id]["manifest_files"]
    con = duckdb.connect()
    con.execute(
        f"CREATE OR REPLACE VIEW census_as_of AS SELECT * FROM read_parquet({files}, union_by_name=true)"
    )
    return con


def compare_schemas() -> None:
    cat = RestCatalogStandin()
    handle = cat.load_table("hf", "census_fact")
    schemas = handle.schemas()
    for s in schemas["schemas"]:
        names = [f["name"] for f in s["fields"]]
        print(f"schema-id={s['schema-id']} fields={names}")


if __name__ == "__main__":
    compare_schemas()
    con = read_snapshot(1)
    print(con.execute("SELECT COUNT(*), SUM(census_count) FROM census_as_of").fetchone())
