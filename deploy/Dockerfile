FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY ingest ./ingest
COPY orchestrate ./orchestrate
COPY transform ./transform
COPY seeds ./seeds

RUN pip install --no-cache-dir -e ".[pipeline]"

ENV PYTHONUNBUFFERED=1 \
    PF_DATA_ROOT=/app \
    DBT_PROJECT_DIR=/app/transform \
    DBT_PROFILES_DIR=/app/transform \
    DAGSTER_HOME=/opt/dagster/dagster_home \
    PYTHONPATH=/app/ingest/src:/app/orchestrate/src

RUN mkdir -p /opt/dagster/dagster_home \
    && cp /app/orchestrate/dagster.yaml /opt/dagster/dagster_home/dagster.yaml

CMD ["python", "-m", "pf_data_ingest"]
