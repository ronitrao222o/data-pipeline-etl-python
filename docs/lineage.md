# Data Lineage

## Flow
`data/raw_sales_data.csv` -> extract -> contract validation -> transform -> profile -> quality checks -> analytics -> warehouse export -> SQLite load -> JSON reports

## Inputs
- `data/raw_sales_data.csv`: source sales orders
- `contracts/sales_orders_contract.yaml`: source schema and primary key expectations
- `config.yaml`: runtime paths, thresholds, analytics settings, and environment profiles

## Transformations
- Parse `order_id`, `quantity`, and `price` into numeric values
- Parse `order_date` into a date
- Reject missing, malformed, duplicate, or invalid records
- Compute `total_amount = quantity * price`

## Outputs
- `artifacts/sales.db`: trusted sales records in SQLite
- `artifacts/pipeline_run_report.json`: run metadata, quality results, contract results, analytics summary, and profile summary
- `artifacts/sales_analytics_report.json`: ranked product, customer, and daily revenue metrics
- `artifacts/data_profile_report.json`: column-level completeness, cardinality, and range metrics
- `artifacts/warehouse/sales`: partitioned CSV files and manifest metadata

## Operational Notes
- `--dry-run` validates extract, contract, transform, profiling, quality, and analytics without loading SQLite or warehouse exports
- `--fail-on-quality-gate` blocks loading and warehouse exports when quality thresholds fail
- Environment profiles and `ETL_*` variables make the same pipeline portable across local and scheduled runs
