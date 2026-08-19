from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from minio import Minio


@dataclass(frozen=True)
class MinioSettings:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool = False
    prefix: str = "fictional"

    @classmethod
    def from_env(cls) -> "MinioSettings":
        return cls(
            endpoint=os.environ.get("MINIO_ENDPOINT", "127.0.0.1:9013"),
            access_key=os.environ.get("MINIO_ROOT_USER", "pfdata"),
            secret_key=os.environ.get("MINIO_ROOT_PASSWORD", "pfdata-dev-not-for-prod"),
            bucket=os.environ.get("MINIO_BUCKET", "raw-sales"),
            secure=os.environ.get("MINIO_SECURE", "false").lower() == "true",
            prefix=os.environ.get("MINIO_PREFIX", "fictional").strip("/"),
        )


def client(settings: MinioSettings | None = None) -> Minio:
    settings = settings or MinioSettings.from_env()
    return Minio(
        settings.endpoint,
        access_key=settings.access_key,
        secret_key=settings.secret_key,
        secure=settings.secure,
    )


def ensure_bucket(settings: MinioSettings | None = None, *, attempts: int = 30) -> None:
    settings = settings or MinioSettings.from_env()
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            api = client(settings)
            if not api.bucket_exists(settings.bucket):
                api.make_bucket(settings.bucket)
            return
        except Exception as exc:  # MinIO may still be booting in Compose.
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"MinIO not reachable at {settings.endpoint}") from last_error


def seed_fictional_csv(
    seeds_dir: Path,
    *,
    orders_name: str = "orders.csv",
    settings: MinioSettings | None = None,
) -> None:
    """Upload the local fictional files into the lake. Not a P06/P10 pull."""
    settings = settings or MinioSettings.from_env()
    ensure_bucket(settings)
    api = client(settings)
    products = seeds_dir / "products.csv"
    orders = seeds_dir / orders_name
    if not products.is_file() or not orders.is_file():
        raise FileNotFoundError(f"missing seed CSV under {seeds_dir}")
    api.fput_object(settings.bucket, f"{settings.prefix}/products.csv", str(products))
    api.fput_object(settings.bucket, f"{settings.prefix}/orders.csv", str(orders))


def extract_to_dir(dest: Path, settings: MinioSettings | None = None) -> Path:
    settings = settings or MinioSettings.from_env()
    dest.mkdir(parents=True, exist_ok=True)
    api = client(settings)
    for name in ("products.csv", "orders.csv"):
        object_name = f"{settings.prefix}/{name}"
        api.fget_object(settings.bucket, object_name, str(dest / name))
    return dest
