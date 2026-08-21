import sys
import os
from datetime import date

# Allow import from src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from transform import transform_data


def test_transform_valid_record():
    raw_data = [
        {
            "order_id": "1",
            "customer_id": "C001",
            "order_date": "2024-01-01",
            "product": "Laptop",
            "quantity": "2",
            "price": "500.0"
        }
    ]

    result = transform_data(raw_data)

    assert len(result) == 1
    assert result[0]["order_id"] == 1
    assert result[0]["total_amount"] == 1000.0


def test_transform_trims_whitespace_from_fields():
    raw_data = [
        {
            "order_id": " 2 ",
            "customer_id": " C002 ",
            "order_date": " 2024-01-02 ",
            "product": " Mouse ",
            "quantity": " 3 ",
            "price": " 199.99 "
        }
    ]

    result = transform_data(raw_data)

    assert len(result) == 1
    assert result[0]["order_id"] == 2
    assert result[0]["customer_id"] == "C002"
    assert result[0]["product"] == "Mouse"
    assert result[0]["order_date"] == date(2024, 1, 2)
    assert result[0]["total_amount"] == 599.97


def test_transform_skips_whitespace_only_required_fields():
    raw_data = [
        {
            "order_id": "3",
            "customer_id": "   ",
            "order_date": "2024-01-03",
            "product": "Keyboard",
            "quantity": "1",
            "price": "999.0"
        }
    ]

    result = transform_data(raw_data)

    assert result == []
