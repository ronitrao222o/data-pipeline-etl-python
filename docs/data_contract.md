# Data Contract

## Dataset
`sales_orders` contains raw sales order records read from `data/raw_sales_data.csv`.

## Ownership
- Owner: `analytics-engineering`
- Primary key: `order_id`
- Contract source: `contracts/sales_orders_contract.yaml`

## Required Columns
| Column | Type | Description |
| --- | --- | --- |
| `order_id` | integer | Unique order identifier from the source sales system. |
| `customer_id` | string | Customer identifier attached to the order. |
| `order_date` | date | Order date in `YYYY-MM-DD` format. |
| `product` | string | Product name sold in the order. |
| `quantity` | integer | Number of units sold. |
| `price` | number | Unit price for the product. |

## Runtime Validation
The pipeline validates the raw CSV against this contract immediately after extraction.
The run report includes:

- expected columns
- missing required columns
- unexpected columns
- duplicate primary keys
- pass or fail status
