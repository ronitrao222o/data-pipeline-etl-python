import sys
import os
from datetime import datetime

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

