"""Extract → validate → staging → dbt. Staging is not updated when validation fails."""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pf_data_ingest.minio_io import MinioSettings, extract_to_dir, seed_fictional_csv
from pf_data_ingest.validate import ValidationError, validate_extract_dir
from pf_data_ingest.warehouse import (
    finish_job_run,
    replace_staging,
    repo_root,
    start_job_run,
)


@dataclass
class PipelineResult:
    ok: bool
    row_count: int = 0
    failure_reason: str | None = None
    run_id: str | None = None


def _orders_seed_name() -> str:
    mode = os.environ.get("PIPELINE_SOURCE", "good").strip().lower()
    if mode == "broken":
        return "broken_orders.csv"
    return "orders.csv"


def _dbt_project() -> Path:
    return Path(os.environ.get("DBT_PROJECT_DIR", str(repo_root() / "transform")))


def run_dbt_build(project_dir: Path | None = None) -> None:
    project_dir = project_dir or _dbt_project()
    profiles = os.environ.get("DBT_PROFILES_DIR", str(project_dir))
    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = profiles
    # Staging tests first so a bad load cannot publish marts mid-flight.
    # Staging models+tests first so a failed quality gate never rebuilds marts.
    staging = subprocess.run(
        ["dbt", "build", "--select", "staging", "--project-dir", str(project_dir)],
        cwd=project_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    if staging.returncode != 0:
        raise RuntimeError(staging.stdout + "\n" + staging.stderr)
    marts = subprocess.run(
        ["dbt", "build", "--select", "marts", "--project-dir", str(project_dir)],
        cwd=project_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    if marts.returncode != 0:
        raise RuntimeError(marts.stdout + "\n" + marts.stderr)
    singular = subprocess.run(
        ["dbt", "test", "--select", "test_type:singular", "--project-dir", str(project_dir)],
        cwd=project_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    if singular.returncode != 0:
        raise RuntimeError(singular.stdout + "\n" + singular.stderr)


def run(*, skip_seed: bool = False) -> PipelineResult:
    settings = MinioSettings.from_env()
    source = _orders_seed_name()
    object_name = f"{settings.prefix}/orders.csv"
    run_id = start_job_run(job_name="fictional_csv_sales", source_object=object_name)
    try:
        if not skip_seed:
            seed_fictional_csv(repo_root() / "seeds", orders_name=source, settings=settings)
        with tempfile.TemporaryDirectory(prefix="pf-data-extract-") as tmp:
            extract_dir = extract_to_dir(Path(tmp), settings)
            report = validate_extract_dir(extract_dir)
            report.raise_if_failed()
            row_count = replace_staging(report.order_lines, report.products)
        run_dbt_build()
        finish_job_run(run_id, status="success", row_count=row_count)
        return PipelineResult(ok=True, row_count=row_count, run_id=run_id)
    except ValidationError as exc:
        finish_job_run(run_id, status="failed", failure_reason=str(exc))
        return PipelineResult(ok=False, failure_reason=str(exc), run_id=run_id)
    except Exception as exc:
        finish_job_run(run_id, status="failed", failure_reason=str(exc))
        return PipelineResult(ok=False, failure_reason=str(exc), run_id=run_id)
