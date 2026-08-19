select
    product_id,
    product_name,
    category,
    count(distinct order_id) as order_count,
    sum(quantity)::bigint as quantity,
    sum(line_revenue_yen)::bigint as revenue_yen
from {{ ref('fct_order_items') }}
group by 1, 2, 3
