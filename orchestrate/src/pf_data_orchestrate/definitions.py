"""Dagster graph: extract → validate → staging → dbt. Fictional CSV only."""

from pathlib import Path
from typing import NamedTuple

from dagster import Definitions, Failure, job, op

from pf_data_ingest.minio_io import MinioSettings, extract_to_dir, seed_fictional_csv
from pf_data_ingest.pipeline import _orders_seed_name, run_dbt_build
from pf_data_ingest.validate import validate_extract_dir
from pf_data_ingest.warehouse import (
    finish_job_run,
    replace_staging,
    repo_root,
    start_job_run,
)

JOB_NAME = "fictional_csv_sales"


class Extracted(NamedTuple):
    run_id: str
    extract_dir: str


class Loaded(NamedTuple):
    run_id: str
    row_count: int


@op
def extract_fictional_csv(context) -> Extracted:
    settings = MinioSettings.from_env()
    run_id = start_job_run(
        job_name=JOB_NAME,
        source_object=f"{settings.prefix}/orders.csv",
    )
    try:
        seed_fictional_csv(
            repo_root() / "seeds",
            orders_name=_orders_seed_name(),
            settings=settings,
        )
        dest = repo_root() / "transform" / "target" / "extract"
        extract_to_dir(dest, settings)
        context.log.info("extracted s3://%s/%s", settings.bucket, settings.prefix)
        return Extracted(run_id=run_id, extract_dir=str(dest))
    except Exception as exc:
        finish_job_run(run_id, status="failed", failure_reason=str(exc))
        raise


@op
def validate_csv(context, extracted: Extracted) -> Extracted:
    report = validate_extract_dir(Path(extracted.extract_dir))
    if not report.ok:
        finish_job_run(extracted.run_id, status="failed", failure_reason=report.reason)
        raise Failure(description=report.reason)
    context.log.info("validated %s order lines", len(report.order_lines))
    return extracted


@op
def load_staging(context, extracted: Extracted) -> Loaded:
    report = validate_extract_dir(Path(extracted.extract_dir))
    if not report.ok:
        finish_job_run(extracted.run_id, status="failed", failure_reason=report.reason)
        raise Failure(description=report.reason)
    row_count = replace_staging(report.order_lines, report.products)
    context.log.info("loaded %s staging rows", row_count)
    return Loaded(run_id=extracted.run_id, row_count=row_count)


@op
def transform_dbt(context, loaded: Loaded) -> int:
    try:
        run_dbt_build()
    except Exception as exc:
        finish_job_run(loaded.run_id, status="failed", failure_reason=str(exc))
        raise Failure(description=str(exc))
    finish_job_run(loaded.run_id, status="success", row_count=loaded.row_count)
    context.log.info("dbt build ok")
    return loaded.row_count


@job(description="Fictional sales CSV → MinIO → Postgres staging → dbt marts. Not P06/P10.")
def fictional_csv_sales():
    transform_dbt(load_staging(validate_csv(extract_fictional_csv())))


defs = Definitions(jobs=[fictional_csv_sales])
