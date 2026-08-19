select order_id, product_id
from {{ ref('fct_order_items') }}
group by 1, 2
having count(*) > 1
