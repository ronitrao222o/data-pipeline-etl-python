# Operations Runbook

## Purpose
This runbook explains how to operate, validate, and troubleshoot the ETL pipeline like a small production data job.

## Standard Run
```bash
python3 -m src.pipeline --config config.yaml
```

## Production-Style Run
```bash
python3 -m src.pipeline \
  --config config.yaml \
  --environment prod \
  --trigger-mode scheduled \
  --run-id nightly-sales-etl-001
```

## Pre-Deployment Validation
Use dry-run mode before a scheduler or config change:

```bash
python3 -m src.pipeline --config config.yaml --environment prod --dry-run
```

Dry runs still generate analytics, data profile, monitoring, and run reports, but skip SQLite loading and warehouse exports.

## Monitoring Report
The monitoring report is written to:

```text
artifacts/monitoring_report.json
```

Production runs write to:

```text
artifacts/prod/monitoring_report.json
```

Monitoring status values:

- `healthy`: no alerts
- `warning`: non-blocking issues were detected
- `critical`: a blocking issue such as a failed quality gate or empty trusted dataset was detected

## Common Alerts
- `contract_validation`: source columns, unexpected fields, or primary key checks need review
- `quality_thresholds`: rejection rate, duplicate count, or row volume crossed configured thresholds
- `rejected_records`: one or more raw rows failed transformation rules
- `empty_profile`: no trusted rows were available for downstream use
- `warehouse_export_count`: exported warehouse rows did not match trusted transformed rows

## Troubleshooting Checklist
- Confirm `config.yaml` points to the expected source file and contract.
- Open `artifacts/pipeline_run_report.json` for row counts, rejected records, and quality checks.
- Open `artifacts/data_profile_report.json` to inspect null rates, distinct counts, and min/max values.
- Open `artifacts/monitoring_report.json` to see alert severity and remediation hints.
- Run `pytest -q` and `ruff check src tests` before pushing operational changes.
