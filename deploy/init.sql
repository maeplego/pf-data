CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS ops;

CREATE TABLE IF NOT EXISTS raw.products (
    product_id text PRIMARY KEY,
    product_name text NOT NULL,
    category text NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw.order_lines (
    order_id text NOT NULL,
    order_date date NOT NULL,
    product_id text NOT NULL,
    quantity integer NOT NULL,
    unit_price_yen integer NOT NULL,
    channel text NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE IF NOT EXISTS ops.job_runs (
    run_id text PRIMARY KEY,
    job_name text NOT NULL,
    started_at timestamptz NOT NULL,
    finished_at timestamptz,
    status text NOT NULL,
    row_count integer,
    failure_reason text,
    source_object text
);
