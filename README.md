# pf-data

P13 data-platform. **Learning project — not a production DWH and not a live pipeline from P06 commerce or P10 talent.** The first DAG reads a **fictional** store-sales CSV. P06 `orders_YYYY-MM-DD.json` and P10 aggregate exports are not wired.

If volume grows past a laptop Postgres, consider Spark then; it is not used here.

## Layout

| Path | Role |
| --- | --- |
| `seeds/` | Fictional `orders.csv` / `products.csv`, broken CSV, expected KPI |
| `ingest/` | MinIO extract, CSV quality gate, Postgres `raw` load, `ops.job_runs` |
| `transform/` | dbt-core: staging views, `marts.daily_sales`, `marts.sales_by_product` |
| `orchestrate/` | Dagster job `fictional_csv_sales` (extract → validate → load → dbt) |
| `bi/` | Optional Metabase profile + mart KPI SQL |

BI / Metabase is **optional** (`docker compose --profile bi`). The smallest path is `bi/dashboards/marts_kpis.sql` against `marts`. P06 export is not wired.

## Compose demo

```powershell
cd deploy
copy .env.example .env
docker compose --env-file .env up --build
```

| URL | Role |
| --- | --- |
| http://localhost:3013 | Dagster UI (job graph after the first pipeline exit 0) |
| http://localhost:9113 | MinIO console (`pfdata` / `pfdata-dev-not-for-prod`) |
| localhost:5413 | Postgres (`data` / `data`, database `data`) |
| localhost:9013 | MinIO S3 API |
| http://localhost:3313 | Metabase（`--profile bi` のときだけ） |

The `pipeline` service uploads the fictional CSV to MinIO, validates, loads `raw`, then `dbt build` (staging tests **before** marts). Re-running the same seed truncates `raw` first, so KPIs do not double.

Expected seed KPI (also `seeds/expected_kpi.json`):

| sale_date | orders | items | revenue_yen |
| --- | --- | --- | --- |
| 2026-08-01 | 3 | 6 | 11500 |
| 2026-08-02 | 2 | 3 | 7100 |
| 2026-08-03 | 2 | 3 | 6200 |

Product totals: P001 14000, P002 7200, P003 3600 (24800 yen).

```sql
select * from marts.daily_sales order by sale_date;
select * from marts.sales_by_product order by product_id;
select run_id, status, row_count, failure_reason from ops.job_runs;
```

### Broken CSV (marts stay on the last good run)

After a successful `up`, in another shell:

```powershell
cd deploy
$env:PIPELINE_SOURCE="broken"
docker compose --env-file .env run --rm -e PIPELINE_SOURCE=broken pipeline
```

Validate fails (negative quantity/price, bad date). Staging/marts are not loaded. `ops.job_runs` gets `status=failed` and a reason.

## Tests (host, no Docker)

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

Covers CSV rules, integer yen, the mart grain (Python + DuckDB SQL matching `transform/manual/mart_shape.sql`). dbt tests run inside Compose/`dbt build`.

## Backfill

This slice is a full refresh of the fictional files. To “backfill”, put the desired CSV in `seeds/`, `docker compose run --rm pipeline`. Date-partitioned P06 objects are a later connector.

## Limits

- Metabase is opt-in (`--profile bi`); P06/P10 source connectors are not wired
- Table-swap on **dbt mart test** failure is not implemented; the CSV gate is what keeps yesterday’s marts
- Spark / CDC / real PII sources are non-goals

Design: `project/portfolio-plan/data-platform/DESIGN.md` and `docs/`.
