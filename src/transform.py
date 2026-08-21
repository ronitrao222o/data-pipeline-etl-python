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


def normalize_row(row):
    return {
        key: value.strip() if isinstance(value, str) else value
        for key, value in row.items()
    }


def transform_data(raw_data):
    transformed = []

    for row in raw_data:
        normalized_row = normalize_row(row)

        # Validate required fields
        if not all(field in normalized_row and normalized_row[field] for field in REQUIRED_FIELDS):
            logging.warning(f"Skipping invalid row: {row}")
            continue

        try:
            transformed.append({
                "order_id": int(normalized_row["order_id"]),
                "customer_id": normalized_row["customer_id"],
                "order_date": datetime.strptime(normalized_row["order_date"], "%Y-%m-%d").date(),
                "product": normalized_row["product"],
                "quantity": int(normalized_row["quantity"]),
                "price": float(normalized_row["price"]),
                "total_amount": int(normalized_row["quantity"]) * float(normalized_row["price"])
            })
        except (ValueError, TypeError) as e:
            logging.warning(f"Skipping row due to type error: {row} | Error: {e}")
            continue

    return transformed
