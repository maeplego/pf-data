select
    order_date as sale_date,
    count(distinct order_id) as order_count,
    sum(quantity)::bigint as item_count,
    sum(line_revenue_yen)::bigint as revenue_yen
from {{ ref('fct_order_items') }}
group by 1
