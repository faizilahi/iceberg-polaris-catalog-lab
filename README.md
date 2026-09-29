# Polaris-Style Catalog Stand-In: Snapshot Log, Time Travel, and a Non-Breaking Schema Evolve

Faiz Elahi — [LinkedIn](https://www.linkedin.com/in/faizilahi) — [pendataco.com](https://pendataco.com) — [GitHub](https://github.com/faizilahi)

Facility census facts in the warehouse tree are generated.

## What this simulates

Apache Iceberg tables registered in a REST catalog (Polaris / AWS Glue Iceberg / Tabular-style). Locally, `catalog/rest_standin/` holds JSON table metadata and snapshot logs — labeled as a **stand-in for the REST catalog**, not a live Polaris server. Data files live under `warehouse/hf/census_fact/`.

## Snapshot log

Each write appends to `catalog/rest_standin/hf/census_fact/snapshots.jsonl`:

```
{"snapshot_id": 1, "operation": "append", "summary": {"added-records": 200}, "parent_id": null}
{"snapshot_id": 2, "operation": "overwrite", ...}
{"snapshot_id": 3, "operation": "schema-evolve-add-column", ...}
```

## Time travel query

`sql/time_travel_as_of_snapshot_1.sql` reads census totals **as of snapshot 1** after snapshot 2 has already landed more days — proving readers can pin a historical snapshot.

## Schema change that did not break old snapshots

Snapshot 3 adds `acuity_band` via a metadata-only evolve. Snapshot 1 and 2 readers still project the old schema (null-filled for the new column when forced to current schema, or exact old parquet files when reading snapshot-scoped manifests). The runner prints both.

## Run

```powershell
cd iceberg-polaris-catalog-lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/bootstrap_table.py
python src/run_snapshots.py
python src/time_travel_demo.py
```
