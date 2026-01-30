import logging
from datetime import datetime

REQUIRED_FIELDS = [
    "order_id",
    "customer_id",
    "order_date",
    "product",
    "quantity",
    "price"
]

def transform_data(raw_data):
    transformed = []

    for row in raw_data:
        # Validate required fields
        if not all(field in row and row[field] for field in REQUIRED_FIELDS):
            logging.warning(f"Skipping invalid row: {row}")
            continue

        try:
            transformed.append({
                "order_id": int(row["order_id"]),
                "customer_id": row["customer_id"],
                "order_date": datetime.strptime(row["order_date"], "%Y-%m-%d").date(),
                "product": row["product"],
                "quantity": int(row["quantity"]),
                "price": float(row["price"]),
                "total_amount": int(row["quantity"]) * float(row["price"])
            })
        except (ValueError, TypeError) as e:
            logging.warning(f"Skipping row due to type error: {row} | Error: {e}")
            continue

    return transformed
