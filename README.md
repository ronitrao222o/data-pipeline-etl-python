# Placement-Ready ETL Pipeline (Python)

## Overview
This repository is evolving from a starter ETL assignment into a stronger portfolio project that demonstrates:

- modular ETL design in Python
- configuration-driven execution
- data-quality validation and rejection handling
- SQLite-based analytical loading
- automated testing and CI
- run-level observability through JSON execution reports
- configurable data-quality gates for production-style pipeline control
- environment-aware runtime configuration for scheduler-friendly execution
- business analytics summaries for product, customer, and daily revenue insights
- monitoring reports with alert severity for operational readiness
- source data contract and lineage documentation for governance-style clarity

The current implementation processes sales CSV data, applies validation and enrichment rules, loads trusted records into SQLite, writes warehouse-style exports, and publishes multiple JSON artifacts for analytics, profiling, monitoring, and orchestration.

## What Makes This Better Than a Basic ETL Script
- Configurable input, schema, database, report, and logging paths through `config.yaml`
- Reusable transformation result model with valid-record, rejected-record, and duplicate tracking
- Safer database loading with schema bootstrapping and transactional inserts
- JSON run report containing row counts, duplicates, rejected records, and total revenue
- Data-quality profiling with rejection-rate, duplicate-count, and minimum-volume checks
- CLI support for report overrides, log-level overrides, and quality-gate enforcement
- Environment profiles and `ETL_*` overrides for deployment flexibility
- Runtime metadata such as `run_id`, trigger mode, owner, and schedule details in every run report
- Dry-run support for orchestration validation without writing to the database
- Separate sales analytics report with ranked products, ranked customers, daily revenue, and average order value
- Column-level data profile report with type inference, null rates, distinct counts, and min/max values
- Partitioned warehouse-style CSV exports with manifest metadata
- Monitoring report with `healthy`, `warning`, and `critical` statuses for runbook-style operations
- Dockerfile, Makefile, Ruff linting, and CI checks for production-style developer workflows
- Data contract validation for required columns, unexpected columns, and duplicate primary keys
- Pytest coverage for transformation rules and end-to-end pipeline execution
- GitHub Actions workflow for automated validation on pull requests and pushes

## Project Structure
```text
.
├── .github/workflows/ci.yml
├── Dockerfile
├── Makefile
├── config.yaml
├── contracts/
├── data/
├── docs/
├── schema.sql
├── src/
│   ├── configuration.py
│   ├── analytics.py
│   ├── extract.py
│   ├── load.py
│   ├── models.py
│   ├── monitoring.py
│   ├── pipeline.py
│   ├── profiling.py
│   ├── quality.py
│   ├── transform.py
│   └── warehouse.py
└── tests/
```

## Configuration
The pipeline reads runtime settings from `config.yaml`.

```yaml
raw_data_path: data/raw_sales_data.csv
data_contract_path: contracts/sales_orders_contract.yaml
database_path: artifacts/sales.db
schema_path: schema.sql
report_output_path: artifacts/pipeline_run_report.json
analytics_output_path: artifacts/sales_analytics_report.json
profile_output_path: artifacts/data_profile_report.json
monitoring_output_path: artifacts/monitoring_report.json
warehouse_output_path: artifacts/warehouse/sales
log_level: INFO
analytics_top_n: 5
runtime:
  environment: dev
  owner: analytics-engineering
  default_trigger_mode: manual
  schedule_name: adhoc
  schedule_cron:
quality_thresholds:
  min_valid_records: 5
  max_rejection_rate: 0.1
  max_duplicate_records: 0
environments:
  prod:
    database_path: artifacts/prod/sales.db
    report_output_path: artifacts/prod/pipeline_run_report.json
    analytics_output_path: artifacts/prod/sales_analytics_report.json
    profile_output_path: artifacts/prod/data_profile_report.json
    monitoring_output_path: artifacts/prod/monitoring_report.json
    warehouse_output_path: artifacts/prod/warehouse/sales
    log_level: INFO
    runtime:
      environment: prod
      schedule_name: nightly-sales-etl
      schedule_cron: "0 1 * * *"
```

## How to Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m src.pipeline --config config.yaml
```

## Quick Demo
Run the project in the production profile with scheduler-style metadata:

```bash
python3 -m src.pipeline --config config.yaml --environment prod --trigger-mode manual --run-id demo-run-001
```

A successful demo loads 10 trusted rows, writes analytics/profile/monitoring reports, and exports warehouse-style CSV files under `artifacts/prod/`.

After the run, verify `pipeline_run_report.json`, `monitoring_report.json`, `sales.db`, and the warehouse `_manifest.json` to confirm the pipeline worked end to end.

To enforce the quality gate and fail the run when configured thresholds are violated:

```bash
python3 -m src.pipeline --config config.yaml --fail-on-quality-gate
```

You can also override runtime settings without editing the YAML file:

```bash
python3 -m src.pipeline --config config.yaml --report-path /tmp/pipeline-report.json --log-level DEBUG
```

To override the analytics report path for a single run:

```bash
python3 -m src.pipeline --config config.yaml --analytics-report-path /tmp/sales-analytics.json
```

To override the data profile path for a single run:

```bash
python3 -m src.pipeline --config config.yaml --profile-report-path /tmp/sales-profile.json
```

To override the monitoring report path for a single run:

```bash
python3 -m src.pipeline --config config.yaml --monitoring-report-path /tmp/sales-monitoring.json
```

To override the warehouse export path for a single run:

```bash
python3 -m src.pipeline --config config.yaml --warehouse-output-path /tmp/sales-warehouse
```

For scheduler-friendly validation, run the pipeline without loading the database:

```bash
python3 -m src.pipeline --config config.yaml --environment prod --trigger-mode scheduled --run-id airflow-run-001 --dry-run
```

You can also switch environments or override settings with environment variables:

```bash
ETL_ENVIRONMENT=prod ETL_OWNER=data-platform python3 -m src.pipeline --config config.yaml --dry-run
```

The command prints a JSON summary and writes:

- SQLite output to `artifacts/sales.db`
- execution metadata to `artifacts/pipeline_run_report.json`
- contract validation status inside the run report
- quality metrics and gate results inside the JSON report
- runtime metadata that makes scheduled or backfill runs easier to trace
- sales analytics output to `artifacts/sales_analytics_report.json`
- data profiling output to `artifacts/data_profile_report.json`
- monitoring output to `artifacts/monitoring_report.json`
- partitioned warehouse CSV output to `artifacts/warehouse/sales`

## Inspect Loaded Data
After running the pipeline, inspect the SQLite output with:

```bash
sqlite3 artifacts/prod/sales.db "SELECT product, ROUND(SUM(total_amount), 2) AS revenue FROM sales GROUP BY product ORDER BY revenue DESC;"
```

More useful validation queries are documented in `docs/sql_queries.md`.

## Test
```bash
pytest -q
```

## Developer Workflow
Use the Makefile for repeatable local commands:

```bash
make setup
make lint
make test
make dry-run
```

Run the pipeline in Docker:

```bash
make docker-run
```

## Data Governance
The source contract lives in `contracts/sales_orders_contract.yaml`.
The documentation in `docs/data_contract.md`, `docs/data_profile.md`, `docs/lineage.md`, `docs/operations.md`, and `docs/warehouse_exports.md` explains the expected source schema, primary key, transformations, generated artifacts, profiling output, operational checks, and partitioned export layout.

## Portfolio Talking Points
- Reliability: quality gates, contract validation, transactional loading, and rejected-record tracking
- Observability: run reports, analytics summaries, data profiles, monitoring alerts, and lineage docs
- Operability: environment profiles, dry runs, CLI overrides, Docker support, Makefile commands, and a runbook
- Testing: unit and end-to-end tests around transformation, quality, contracts, analytics, profiling, warehouse exports, and pipeline execution

## Interview Summary
This project demonstrates how raw CSV sales data can be converted into trusted, validated, report-ready data using a maintainable Python ETL workflow with database loading, quality checks, analytics, profiling, monitoring, and automated tests.

## Resume Alignment
This project supports resume claims around Python ETL development, CSV ingestion, malformed-record validation, derived feature creation, SQLite loading, YAML configuration, standardized logging, exception handling, and Pytest-based verification.

Use the quick demo command above to show the complete flow from raw sales data to database rows, JSON reports, monitoring output, and warehouse-style exports.

## Why This Helps In Placements
This repo now signals more than just "I can read a CSV." It shows engineering judgment around reliability, maintainability, observability, testing, and clean project structure, which are the things interviewers usually look for when they ask about projects.
