select *
from {{ ref('daily_sales') }}
where revenue_yen < 0
   or item_count < 0
   or order_count < 0
