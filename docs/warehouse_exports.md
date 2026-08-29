# Warehouse Exports

## Purpose
The pipeline writes trusted sales records into partitioned CSV files that mimic a simple warehouse or data lake layout.

## Layout
Default output path:

```text
artifacts/warehouse/sales/
|-- _manifest.json
`-- order_month=YYYY-MM/
    `-- part-000.csv
```

## Partitioning
Records are partitioned by `order_month`, derived from `order_date`.
This keeps the export easy to inspect locally while showing a common pattern used in warehouse and lakehouse systems.

## Manifest
`_manifest.json` contains:

- run id
- output path
- partition column
- partition count
- exported record count
- partition paths and row counts

## Runtime Behavior
- Normal runs write partition files and a manifest
- `--dry-run` skips partition file generation while still writing run, analytics, and profile reports
- failed quality gates skip partition file generation while still writing diagnostics
