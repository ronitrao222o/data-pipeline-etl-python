from __future__ import annotations

import logging
from datetime import datetime

try:
    from .models import RejectedRecord, TransformationResult
except ImportError:  # pragma: no cover - fallback for direct script execution
    from models import RejectedRecord, TransformationResult

REQUIRED_FIELDS = [
    "order_id",
    "customer_id",
    "order_date",
    "product",
    "quantity",
    "price"
]


def _missing_required_fields(row: dict[str, str]) -> list[str]:
    return [field for field in REQUIRED_FIELDS if not row.get(field)]


def transform_data(raw_data: list[dict[str, str]]) -> TransformationResult:
    transformed: list[dict[str, object]] = []
    rejected_records: list[RejectedRecord] = []
    duplicate_order_ids: list[int] = []
    seen_order_ids: set[int] = set()

    for row_number, row in enumerate(raw_data, start=2):
        missing_fields = _missing_required_fields(row)
        if missing_fields:
            rejected_records.append(
                RejectedRecord(
                    row_number=row_number,
                    reason=f"Missing required fields: {', '.join(missing_fields)}",
                    payload=row,
                )
            )
            continue

        try:
            order_id = int(row["order_id"])
            quantity = int(row["quantity"])
            price = float(row["price"])
            order_date = datetime.strptime(row["order_date"], "%Y-%m-%d").date()
        except (ValueError, TypeError) as error:
            rejected_records.append(
                RejectedRecord(
                    row_number=row_number,
                    reason=f"Type conversion error: {error}",
                    payload=row,
                )
            )
            continue

        if quantity <= 0:
            rejected_records.append(
                RejectedRecord(
                    row_number=row_number,
                    reason="Quantity must be greater than zero",
                    payload=row,
                )
            )
            continue

        if price < 0:
            rejected_records.append(
                RejectedRecord(
                    row_number=row_number,
                    reason="Price cannot be negative",
                    payload=row,
                )
            )
            continue

        if order_id in seen_order_ids:
            duplicate_order_ids.append(order_id)
            rejected_records.append(
                RejectedRecord(
                    row_number=row_number,
                    reason=f"Duplicate order_id detected: {order_id}",
                    payload=row,
                )
            )
            continue

        seen_order_ids.add(order_id)
        transformed.append(
            {
                "order_id": order_id,
                "customer_id": row["customer_id"].strip(),
                "order_date": order_date,
                "product": row["product"].strip(),
                "quantity": quantity,
                "price": price,
                "total_amount": round(quantity * price, 2),
            }
        )

    result = TransformationResult(
        valid_records=transformed,
        rejected_records=rejected_records,
        duplicate_order_ids=duplicate_order_ids,
    )
    logging.info(
        "Transformation completed with %s valid rows and %s rejected rows",
        result.valid_record_count,
        result.rejected_record_count,
    )
    return result
