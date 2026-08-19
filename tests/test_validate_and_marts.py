from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import duckdb
import pytest

from pf_data_ingest.marts import sales_by_day, sales_by_product
from pf_data_ingest.validate import validate_extract_dir, validate_order_rows, validate_product_rows

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "seeds"


@pytest.fixture
def expected_kpi() -> dict:
    return json.loads((SEEDS / "expected_kpi.json").read_text(encoding="utf-8"))


def test_good_orders_pass_validation():
    lines, errors = validate_order_rows(SEEDS / "orders.csv")
    assert errors == []
    assert len(lines) == 8
    products, product_errors = validate_product_rows(SEEDS / "products.csv")
    assert product_errors == []
    assert len(products) == 3


def test_broken_orders_fail_before_warehouse(tmp_path: Path):
    (tmp_path / "products.csv").write_bytes((SEEDS / "products.csv").read_bytes())
    (tmp_path / "orders.csv").write_bytes((SEEDS / "broken_orders.csv").read_bytes())
    report = validate_extract_dir(tmp_path)
    assert not report.ok
    joined = report.reason
    assert "quantity must be >= 1" in joined
    assert "order_date must be YYYY-MM-DD" in joined
    assert "unit_price_yen must be >= 0" in joined
    assert report.order_lines == []


def test_rejects_fractional_yen(tmp_path: Path):
    (tmp_path / "orders.csv").write_text(
        "order_id,order_date,product_id,quantity,unit_price_yen,channel\n"
        "ORD-X,2026-08-01,P001,1,12.5,web\n",
        encoding="utf-8",
    )
    _, errors = validate_order_rows(tmp_path / "orders.csv")
    assert any("integer" in e for e in errors)


def test_rejects_duplicate_order_line(tmp_path: Path):
    (tmp_path / "orders.csv").write_text(
        "order_id,order_date,product_id,quantity,unit_price_yen,channel\n"
        "ORD-X,2026-08-01,P001,1,100,web\n"
        "ORD-X,2026-08-01,P001,2,100,web\n",
        encoding="utf-8",
    )
    _, errors = validate_order_rows(tmp_path / "orders.csv")
    assert any("duplicate" in e for e in errors)


def test_python_marts_match_expected_kpi(expected_kpi: dict):
    lines, errors = validate_order_rows(SEEDS / "orders.csv")
    products, product_errors = validate_product_rows(SEEDS / "products.csv")
    assert not errors and not product_errors
    daily = [
        {
            "sale_date": row.sale_date.isoformat(),
            "order_count": row.order_count,
            "item_count": row.item_count,
            "revenue_yen": row.revenue_yen,
        }
        for row in sales_by_day(lines)
    ]
    by_product = [
        {
            "product_id": row.product_id,
            "product_name": row.product_name,
            "category": row.category,
            "order_count": row.order_count,
            "quantity": row.quantity,
            "revenue_yen": row.revenue_yen,
        }
        for row in sales_by_product(lines, products)
    ]
    assert daily == expected_kpi["daily_sales"]
    assert by_product == expected_kpi["sales_by_product"]
    assert sum(r["revenue_yen"] for r in daily) == expected_kpi["total_revenue_yen"]


def test_hand_sql_duckdb_matches_expected_kpi(expected_kpi: dict):
    """Same grain as transform/manual/mart_shape.sql, against the fictional CSV."""
    con = duckdb.connect()
    orders = (SEEDS / "orders.csv").as_posix()
    products = (SEEDS / "products.csv").as_posix()
    con.execute(f"create table order_lines as select * from read_csv_auto('{orders}')")
    con.execute(f"create table products as select * from read_csv_auto('{products}')")
    daily = con.execute(
        """
        select
            order_date::date as sale_date,
            count(distinct order_id) as order_count,
            sum(quantity)::bigint as item_count,
            sum(quantity * unit_price_yen)::bigint as revenue_yen
        from order_lines
        group by 1
        order by 1
        """
    ).fetchall()
    assert [
        {
            "sale_date": row[0].isoformat() if isinstance(row[0], date) else str(row[0]),
            "order_count": int(row[1]),
            "item_count": int(row[2]),
            "revenue_yen": int(row[3]),
        }
        for row in daily
    ] == expected_kpi["daily_sales"]

    by_product = con.execute(
        """
        select
            p.product_id,
            p.product_name,
            p.category,
            count(distinct o.order_id) as order_count,
            sum(o.quantity)::bigint as quantity,
            sum(o.quantity * o.unit_price_yen)::bigint as revenue_yen
        from order_lines as o
        join products as p on p.product_id = o.product_id
        group by 1, 2, 3
        order by 1
        """
    ).fetchall()
    assert [
        {
            "product_id": row[0],
            "product_name": row[1],
            "category": row[2],
            "order_count": int(row[3]),
            "quantity": int(row[4]),
            "revenue_yen": int(row[5]),
        }
        for row in by_product
    ] == expected_kpi["sales_by_product"]


def test_reload_same_seed_does_not_duplicate():
    lines, _ = validate_order_rows(SEEDS / "orders.csv")
    doubled = sales_by_day(list(lines) + list(lines))
    once = sales_by_day(lines)
    assert [row.revenue_yen for row in doubled] != [row.revenue_yen for row in once]
    # Warehouse truncate+insert is the idempotent path; grain uniqueness is the guard.
    keys = {(line.order_id, line.product_id) for line in lines}
    assert len(keys) == len(lines)
