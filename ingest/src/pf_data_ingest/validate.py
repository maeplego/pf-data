"""CSV quality gate. Fail before staging/marts so a bad file cannot rewrite yesterday."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from pf_data_ingest.marts import OrderLine, Product

ORDER_COLUMNS = (
    "order_id",
    "order_date",
    "product_id",
    "quantity",
    "unit_price_yen",
    "channel",
)
PRODUCT_COLUMNS = ("product_id", "product_name", "category")
ALLOWED_CHANNELS = frozenset({"web", "store"})


class ValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass
class ValidationReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    order_lines: list[OrderLine] = field(default_factory=list)
    products: list[Product] = field(default_factory=list)

    @property
    def reason(self) -> str:
        return "; ".join(self.errors)

    def raise_if_failed(self) -> None:
        if not self.ok:
            raise ValidationError(self.errors)


def _require_columns(fieldnames: list[str] | None, required: tuple[str, ...], label: str) -> list[str]:
    errors: list[str] = []
    have = set(fieldnames or [])
    missing = [c for c in required if c not in have]
    if missing:
        errors.append(f"{label} missing columns: {', '.join(missing)}")
    return errors


def _parse_int(raw: str, field: str, row_num: int, *, min_value: int) -> tuple[int | None, str | None]:
    try:
        if raw.strip() == "" or "." in raw:
            raise ValueError
        value = int(raw)
    except ValueError:
        return None, f"{field} must be an integer yen/count at row {row_num}"
    if value < min_value:
        return None, f"{field} must be >= {min_value} at row {row_num}"
    return value, None


def _parse_date(raw: str, row_num: int) -> tuple[date | None, str | None]:
    try:
        return date.fromisoformat(raw.strip()), None
    except ValueError:
        return None, f"order_date must be YYYY-MM-DD at row {row_num}"


def validate_product_rows(path: Path) -> tuple[list[Product], list[str]]:
    errors: list[str] = []
    products: list[Product] = []
    seen: set[str] = set()
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        errors.extend(_require_columns(reader.fieldnames, PRODUCT_COLUMNS, "products"))
        if errors:
            return [], errors
        for i, row in enumerate(reader, start=2):
            pid = (row.get("product_id") or "").strip()
            name = (row.get("product_name") or "").strip()
            category = (row.get("category") or "").strip()
            if not pid or not name or not category:
                errors.append(f"products empty required field at row {i}")
                continue
            if pid in seen:
                errors.append(f"duplicate product_id {pid}")
                continue
            seen.add(pid)
            products.append(Product(product_id=pid, product_name=name, category=category))
    if not products and not errors:
        errors.append("products file has no data rows")
    return products, errors


def validate_order_rows(path: Path) -> tuple[list[OrderLine], list[str]]:
    errors: list[str] = []
    lines: list[OrderLine] = []
    seen: set[tuple[str, str]] = set()
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        errors.extend(_require_columns(reader.fieldnames, ORDER_COLUMNS, "orders"))
        if errors:
            return [], errors
        for i, row in enumerate(reader, start=2):
            order_id = (row.get("order_id") or "").strip()
            product_id = (row.get("product_id") or "").strip()
            channel = (row.get("channel") or "").strip()
            if not order_id or not product_id:
                errors.append(f"orders empty order_id/product_id at row {i}")
                continue
            order_date, date_err = _parse_date(row.get("order_date") or "", i)
            if date_err:
                errors.append(date_err)
            qty, qty_err = _parse_int(row.get("quantity") or "", "quantity", i, min_value=1)
            if qty_err:
                errors.append(qty_err)
            price, price_err = _parse_int(
                row.get("unit_price_yen") or "", "unit_price_yen", i, min_value=0
            )
            if price_err:
                errors.append(price_err)
            if channel not in ALLOWED_CHANNELS:
                errors.append(f"channel must be web or store at row {i}")
            key = (order_id, product_id)
            if key in seen:
                errors.append(f"duplicate order line {order_id}/{product_id}")
                continue
            if order_date is None or qty is None or price is None or channel not in ALLOWED_CHANNELS:
                continue
            seen.add(key)
            lines.append(
                OrderLine(
                    order_id=order_id,
                    order_date=order_date,
                    product_id=product_id,
                    quantity=qty,
                    unit_price_yen=price,
                    channel=channel,
                )
            )
    if not lines and not errors:
        errors.append("orders file has no data rows")
    return lines, errors


def validate_extract_dir(extract_dir: Path) -> ValidationReport:
    orders_path = extract_dir / "orders.csv"
    products_path = extract_dir / "products.csv"
    errors: list[str] = []
    if not orders_path.is_file():
        errors.append("orders.csv not found in extract")
    if not products_path.is_file():
        errors.append("products.csv not found in extract")
    if errors:
        return ValidationReport(ok=False, errors=errors)

    products, product_errors = validate_product_rows(products_path)
    lines, order_errors = validate_order_rows(orders_path)
    errors.extend(product_errors)
    errors.extend(order_errors)

    product_ids = {p.product_id for p in products}
    for line in lines:
        if line.product_id not in product_ids:
            errors.append(f"unknown product_id {line.product_id} on {line.order_id}")

    return ValidationReport(
        ok=not errors,
        errors=errors,
        order_lines=lines if not errors else [],
        products=products if not errors else [],
    )
