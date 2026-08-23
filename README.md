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

The current implementation processes sales CSV data, applies validation and enrichment rules, loads trusted records into SQLite, and writes an execution report that can be used for monitoring or downstream orchestration.

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
- Pytest coverage for transformation rules and end-to-end pipeline execution
- GitHub Actions workflow for automated validation on pull requests and pushes

## Project Structure
```text
.
├── .github/workflows/ci.yml
├── config.yaml
├── data/
├── schema.sql
├── src/
│   ├── configuration.py
│   ├── extract.py
│   ├── load.py
│   ├── models.py
│   ├── pipeline.py
│   ├── quality.py
│   └── transform.py
└── tests/
```

## Configuration
The pipeline reads runtime settings from `config.yaml`.

```yaml
raw_data_path: data/raw_sales_data.csv
database_path: artifacts/sales.db
schema_path: schema.sql
report_output_path: artifacts/pipeline_run_report.json
log_level: INFO
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

To enforce the quality gate and fail the run when configured thresholds are violated:

```bash
python3 -m src.pipeline --config config.yaml --fail-on-quality-gate
```

You can also override runtime settings without editing the YAML file:

```bash
python3 -m src.pipeline --config config.yaml --report-path /tmp/pipeline-report.json --log-level DEBUG
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
- quality metrics and gate results inside the JSON report
- runtime metadata that makes scheduled or backfill runs easier to trace

## Test
```bash
pytest -q
```

## 15-Day Upgrade Roadmap
To keep changes incremental and interview-friendly, this project can be upgraded in small phases:

1. Phase 1: strengthen architecture, validation, tests, and reporting
2. Phase 2: introduce analytics queries, dashboards, or warehouse-oriented outputs
3. Phase 3: add containerization, linting, and more production-style developer tooling
4. Phase 4: add warehouse targets, partitioned datasets, and broader monitoring hooks
5. Phase 5: add alerting, lineage notes, and broader monitoring integrations

## Why This Helps In Placements
This repo now signals more than just "I can read a CSV." It starts to show engineering judgment around reliability, maintainability, observability, testing, and clean project structure, which are the things interviewers usually look for when they ask about projects.
