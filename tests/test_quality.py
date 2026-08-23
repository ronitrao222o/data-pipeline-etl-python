from src.models import DataQualityThresholds
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
