from src.transform import transform_data


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

    assert result.valid_record_count == 1
    assert result.rejected_record_count == 0
    assert result.valid_records[0]["order_id"] == 1
    assert result.valid_records[0]["total_amount"] == 1000.0


def test_transform_rejects_missing_required_field():
    raw_data = [
        {
            "order_id": "2",
            "customer_id": "",
            "order_date": "2024-01-01",
            "product": "Laptop",
            "quantity": "1",
            "price": "999.0",
        }
    ]

    result = transform_data(raw_data)

    assert result.valid_record_count == 0
    assert result.rejected_record_count == 1
    assert "Missing required fields" in result.rejected_records[0].reason


def test_transform_rejects_negative_price():
    raw_data = [
        {
            "order_id": "3",
            "customer_id": "C003",
            "order_date": "2024-01-01",
            "product": "Keyboard",
            "quantity": "1",
            "price": "-99.0",
        }
    ]

    result = transform_data(raw_data)

    assert result.valid_record_count == 0
    assert result.rejected_record_count == 1
    assert result.rejected_records[0].reason == "Price cannot be negative"


def test_transform_rejects_duplicate_order_id():
    raw_data = [
        {
            "order_id": "4",
            "customer_id": "C004",
            "order_date": "2024-01-01",
            "product": "Monitor",
            "quantity": "1",
            "price": "450.0",
        },
        {
            "order_id": "4",
            "customer_id": "C005",
            "order_date": "2024-01-02",
            "product": "Mouse",
            "quantity": "2",
            "price": "50.0",
        },
    ]

    result = transform_data(raw_data)

    assert result.valid_record_count == 1
    assert result.rejected_record_count == 1
    assert result.duplicate_order_ids == [4]
