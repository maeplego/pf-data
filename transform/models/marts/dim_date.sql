select distinct
    order_date as date_day,
    extract(year from order_date)::int as year,
    extract(month from order_date)::int as month,
    extract(dow from order_date)::int as day_of_week
from {{ ref('stg_orders') }}
