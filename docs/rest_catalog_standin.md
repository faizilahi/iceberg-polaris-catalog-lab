# REST catalog stand-in

Real Polaris speaks Iceberg REST (`/v1/config`, `/v1/{prefix}/namespaces`, `/v1/.../tables`). This lab stores equivalent documents as flat JSON:

| File | Stand-in for |
|------|----------------|
| `catalog/rest_standin/config.json` | `GET /v1/config` |
| `catalog/rest_standin/namespaces.json` | namespace list |
| `catalog/rest_standin/hf/census_fact/metadata.json` | table metadata pointer |
| `catalog/rest_standin/hf/census_fact/snapshots.jsonl` | snapshot log |
| `catalog/rest_standin/hf/census_fact/schemas.json` | schema versions |

No network listener is started — the Python modules read these files the way a catalog client would parse REST payloads.
