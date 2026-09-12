# SQLite Validation Queries

## Purpose
Use these queries after a pipeline run to verify the loaded SQLite data and explain the project during interviews.

## Open The Database
```bash
sqlite3 artifacts/prod/sales.db
```

## Row Count And Revenue
```sql
SELECT
  COUNT(*) AS loaded_orders,
  ROUND(SUM(total_amount), 2) AS total_revenue
FROM sales;
```

## Revenue By Product
```sql
SELECT
  product,
  COUNT(*) AS order_count,
  SUM(quantity) AS quantity_sold,
  ROUND(SUM(total_amount), 2) AS revenue
FROM sales
GROUP BY product
ORDER BY revenue DESC;
```

## Top Customers
```sql
SELECT
  customer_id,
  COUNT(*) AS order_count,
  ROUND(SUM(total_amount), 2) AS revenue
FROM sales
GROUP BY customer_id
ORDER BY revenue DESC;
```

## Daily Revenue
```sql
SELECT
  order_date,
  ROUND(SUM(total_amount), 2) AS revenue
FROM sales
GROUP BY order_date
ORDER BY order_date;
```
