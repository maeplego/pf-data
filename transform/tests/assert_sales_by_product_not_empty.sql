select 1
where (select count(*) from {{ ref('sales_by_product') }}) = 0
