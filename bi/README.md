# P13 BI path

Marts are the contract. Dashboards read **`marts` only** (plus `ops.job_runs` for pipeline health). P06 / P10 connectors are not in this slice.

## Without Metabase (smallest path)

After Compose pipeline succeeds, run the queries in `dashboards/marts_kpis.sql` against Postgres `localhost:5413` (user/password/db `data`). Expected numbers are `seeds/expected_kpi.json`.

```sql
select * from marts.daily_sales order by sale_date;
select * from marts.sales_by_product order by product_id;
```

## Optional Metabase

Default `docker compose up` does **not** start Metabase (image pull and first-run wizard would slow the DAG demo). Opt in:

```powershell
cd deploy
docker compose --env-file .env --profile bi up -d metabase
```

| URL | Role |
| --- | --- |
| http://localhost:3313 | Metabase UI (first visit creates a local admin; do not commit credentials) |

Add a Postgres database:

- Host: `postgres` (from the Compose network) or `host.docker.internal` if you attach Metabase differently
- Port: `5432`
- Database / user / password: `data` / `data` / `data` (from `.env.example`)
- Schema to browse: `marts`

Create three questions from `dashboards/marts_kpis.sql` (daily sales table, product bar, job_runs table). This product does not ship a Metabase application database dump.
