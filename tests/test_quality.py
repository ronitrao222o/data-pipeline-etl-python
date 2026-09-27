from datetime import date

import pytest

from src.models import DataQualityThresholds, RejectedRecord, TransformationResult
from src.quality import evaluate_data_quality
from src.transform import transform_data


def test_evaluate_data_quality_calculates_profile_metrics():
    raw_data = [
        {
            "order_id": "1",
            "customer_id": "C001",
            "order_date": "2024-01-01",
            "product": "Laptop",
            "quantity": "1",
            "price": "50000",
        },
        {
            "order_id": "2",
            "customer_id": "C002",
            "order_date": "2024-01-02",
            "product": "Mouse",
            "quantity": "2",
            "price": "500",
        },
    ]

    transformation_result = transform_data(raw_data)
    summary = evaluate_data_quality(
        transformation_result,
        DataQualityThresholds(
            min_valid_records=2,
            max_rejection_rate=0.0,
            max_duplicate_records=0,
        ),
    )

    assert summary.passed is True
    assert summary.unique_customer_count == 2
    assert summary.unique_product_count == 2
    assert summary.average_order_value == 25500.0
    assert summary.order_date_range["start"].isoformat() == "2024-01-01"
    assert summary.order_date_range["end"].isoformat() == "2024-01-02"


@pytest.mark.parametrize(
    ("valid_count", "rejected_count", "limit", "passed"),
    [
        (2, 1, 0.3333, False),
        (1, 2, 0.66668, True),
        (3, 1, 0.25, True),
        (20000, 1, 0.0, False),
        (1, 0, 0.0, True),
        (0, 0, 0.0, True),
    ],
)
def test_rejection_rate_gate_uses_unrounded_ratio(valid_count, rejected_count, limit, passed):
    record = {
        "customer_id": "C001",
        "product": "Mouse",
        "order_date": date(2024, 1, 1),
        "total_amount": 1.0,
    }
    result = TransformationResult(
        valid_records=[record] * valid_count,
        rejected_records=[RejectedRecord(row_number=2, reason="Invalid row", payload={})]
        * rejected_count,
    )

    summary = evaluate_data_quality(
        result,
        DataQualityThresholds(min_valid_records=0, max_rejection_rate=limit),
    )

    check = next(check for check in summary.checks if check.name == "max_rejection_rate")
    expected_rate = rejected_count / max(valid_count + rejected_count, 1)
    assert check.passed is passed
    assert summary.passed is passed
    assert summary.rejection_rate == expected_rate
    assert check.actual_value == expected_rate
    assert summary.to_dict()["rejection_rate"] == expected_rate
