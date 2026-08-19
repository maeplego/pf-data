-- Smallest mart dashboard path (schema marts only).
-- Point Metabase (or psql) at these queries after a successful pipeline run.
-- Fictional seed KPI; not a live P06 export.

-- 1) Daily sales
select sale_date, order_count, item_count, revenue_yen
from marts.daily_sales
order by sale_date;

-- Expected for seeds/orders.csv:
-- 2026-08-01 | 3 | 6 | 11500
-- 2026-08-02 | 2 | 3 | 7100
-- 2026-08-03 | 2 | 3 | 6200

-- 2) Product revenue
select product_id, product_name, category, order_count, quantity, revenue_yen
from marts.sales_by_product
order by product_id;

-- Expected: P001 14000, P002 7200, P003 3600 (24800 yen).

-- 3) Pipeline health (ops, not a KPI chart)
select run_id, status, row_count, failure_reason
from ops.job_runs
order by started_at desc
limit 20;
