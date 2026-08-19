-- Hand SQL that decided the mart grain before dbt.
-- Fictional order_lines only. Amounts are integer yen.

-- daily sales
select
    order_date as sale_date,
    count(distinct order_id) as order_count,
    sum(quantity) as item_count,
    sum(quantity * unit_price_yen) as revenue_yen
from raw.order_lines
group by 1
order by 1;

-- by product
select
    p.product_id,
    p.product_name,
    p.category,
    count(distinct o.order_id) as order_count,
    sum(o.quantity) as quantity,
    sum(o.quantity * o.unit_price_yen) as revenue_yen
from raw.order_lines as o
join raw.products as p on p.product_id = o.product_id
group by 1, 2, 3
order by 1;
