select *
from {{ ref('sales_by_product') }}
where revenue_yen < 0
   or quantity < 0
   or order_count < 0
