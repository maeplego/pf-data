from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class OrderLine:
    order_id: str
    order_date: date
    product_id: str
    quantity: int
    unit_price_yen: int
    channel: str

    @property
    def line_revenue_yen(self) -> int:
        return self.quantity * self.unit_price_yen


@dataclass(frozen=True)
class Product:
    product_id: str
    product_name: str
    category: str


@dataclass(frozen=True)
class DailySales:
    sale_date: date
    order_count: int
    item_count: int
    revenue_yen: int


@dataclass(frozen=True)
class ProductSales:
    product_id: str
    product_name: str
    category: str
    order_count: int
    quantity: int
    revenue_yen: int


def sales_by_day(lines: Iterable[OrderLine]) -> list[DailySales]:
    """Mart grain: one row per sale_date. Amounts stay integer yen."""
    buckets: dict[date, dict[str, object]] = {}
    for line in lines:
        bucket = buckets.setdefault(
            line.order_date,
            {"orders": set(), "item_count": 0, "revenue_yen": 0},
        )
        bucket["orders"].add(line.order_id)  # type: ignore[union-attr]
        bucket["item_count"] += line.quantity  # type: ignore[operator]
        bucket["revenue_yen"] += line.line_revenue_yen  # type: ignore[operator]
    return [
        DailySales(
            sale_date=day,
            order_count=len(bucket["orders"]),  # type: ignore[arg-type]
            item_count=int(bucket["item_count"]),
            revenue_yen=int(bucket["revenue_yen"]),
        )
        for day, bucket in sorted(buckets.items())
    ]


def sales_by_product(
    lines: Iterable[OrderLine], products: Iterable[Product]
) -> list[ProductSales]:
    """Mart grain: one row per product_id after joining the product dimension."""
    dim = {p.product_id: p for p in products}
    buckets: dict[str, dict[str, object]] = {}
    for line in lines:
        product = dim.get(line.product_id)
        if product is None:
            continue
        bucket = buckets.setdefault(
            line.product_id,
            {
                "product": product,
                "orders": set(),
                "quantity": 0,
                "revenue_yen": 0,
            },
        )
        bucket["orders"].add(line.order_id)  # type: ignore[union-attr]
        bucket["quantity"] += line.quantity  # type: ignore[operator]
        bucket["revenue_yen"] += line.line_revenue_yen  # type: ignore[operator]
    out: list[ProductSales] = []
    for product_id, bucket in sorted(buckets.items()):
        product = bucket["product"]
        assert isinstance(product, Product)
        out.append(
            ProductSales(
                product_id=product_id,
                product_name=product.product_name,
                category=product.category,
                order_count=len(bucket["orders"]),  # type: ignore[arg-type]
                quantity=int(bucket["quantity"]),
                revenue_yen=int(bucket["revenue_yen"]),
            )
        )
    return out
