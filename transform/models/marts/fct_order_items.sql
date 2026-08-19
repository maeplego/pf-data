select
    o.order_id,
    o.order_date,
    o.product_id,
    p.product_name,
    p.category,
    o.quantity,
    o.unit_price_yen,
    o.line_revenue_yen,
    o.channel
from {{ ref('stg_orders') }} as o
inner join {{ ref('dim_product') }} as p
    on o.product_id = p.product_id
