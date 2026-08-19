select 1
where (select count(*) from {{ ref('daily_sales') }}) = 0
