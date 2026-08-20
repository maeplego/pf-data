"""Pull fictional order lines from P06 commerce export (opaque buyer id, no email)."""

from __future__ import annotations

import csv
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path


def export_url(day: date | None = None) -> str:
    base = os.environ.get("COMMERCE_EXPORT_URL", "http://localhost:8103/v1/ops/exports/orders").rstrip("/")
    if day is None:
        return base
    return f"{base}?date={urllib.parse.quote(day.isoformat())}"


def fetch_orders_csv(dest: Path, *, day: date | None = None, token_sub: str = "ops-demo") -> Path:
    req = urllib.request.Request(
        export_url(day),
        headers={"X-Dev-User-Sub": token_sub, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            payload = res.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"commerce export failed: {exc.code}") from exc
    import json

    body = json.loads(payload.decode("utf-8"))
    lines = body.get("lines") or []
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["order_id", "order_date", "product_id", "quantity", "unit_price_yen", "channel"])
        for row in lines:
            writer.writerow(
                [
                    row["orderId"],
                    row["orderDate"],
                    row["productId"],
                    row["quantity"],
                    row["unitPriceYen"],
                    row.get("channel", "web"),
                ]
            )
    return dest
