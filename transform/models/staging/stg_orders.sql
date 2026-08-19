select
    order_id,
    order_date,
    product_id,
    quantity,
    unit_price_yen,
    (quantity * unit_price_yen)::bigint as line_revenue_yen,
    channel
from {{ source('raw', 'order_lines') }}
