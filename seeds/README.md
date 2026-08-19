# Fictional seeds

These CSVs are invented store sales. They are **not** exports from P06 commerce or P10 talent.

`orders.csv` + `products.csv` are the happy-path lake objects. `broken_orders.csv` is only for the quality-gate demo (negative quantity / price, unparseable date). `expected_kpi.json` is the mart grain we check in pytest and after a successful `dbt build`.
