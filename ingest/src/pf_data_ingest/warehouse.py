from __future__ import annotations

import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import psycopg
from ulid import ULID

from pf_data_ingest.marts import OrderLine, Product


def dsn() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://data:data@127.0.0.1:5413/data",
    )


@contextmanager
def connect(*, attempts: int = 30) -> Iterator[psycopg.Connection]:
    last_error: Exception | None = None
    conn = None
    for _ in range(attempts):
        try:
            conn = psycopg.connect(dsn())
            break
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    if conn is None:
        raise RuntimeError("Postgres not reachable") from last_error
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def replace_staging(orders: list[OrderLine], products: list[Product]) -> int:
    """Full refresh of the fictional seed. Same files twice must not duplicate."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("truncate table raw.order_lines, raw.products")
            for product in products:
                cur.execute(
                    """
                    insert into raw.products (product_id, product_name, category)
                    values (%s, %s, %s)
                    """,
                    (product.product_id, product.product_name, product.category),
                )
            for line in orders:
                cur.execute(
                    """
                    insert into raw.order_lines (
                        order_id, order_date, product_id, quantity, unit_price_yen, channel
                    )
                    values (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        line.order_id,
                        line.order_date,
                        line.product_id,
                        line.quantity,
                        line.unit_price_yen,
                        line.channel,
                    ),
                )
    return len(orders)


def start_job_run(*, job_name: str, source_object: str) -> str:
    run_id = str(ULID())
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into ops.job_runs (
                    run_id, job_name, started_at, status, source_object
                )
                values (%s, %s, %s, 'running', %s)
                """,
                (run_id, job_name, datetime.now(timezone.utc), source_object),
            )
    return run_id


def finish_job_run(
    run_id: str,
    *,
    status: str,
    row_count: int | None = None,
    failure_reason: str | None = None,
) -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                update ops.job_runs
                set finished_at = %s,
                    status = %s,
                    row_count = %s,
                    failure_reason = %s
                where run_id = %s
                """,
                (
                    datetime.now(timezone.utc),
                    status,
                    row_count,
                    failure_reason,
                    run_id,
                ),
            )


def repo_root() -> Path:
    env = os.environ.get("PF_DATA_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3]
