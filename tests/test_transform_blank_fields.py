import pytest

from src.transform import transform_data


@pytest.mark.parametrize(
    "field", ["order_id", "customer_id", "order_date", "product", "quantity", "price"]
)
@pytest.mark.parametrize("value", ["", "   ", "\t\r\n", None])
def test_transform_rejects_blank_required_values(field, value):
    valid_row = {
        "order_id": "1",
        "customer_id": "C001",
        "order_date": "2024-01-01",
        "product": "Laptop",
        "quantity": "2",
        "price": "500.0",
    }
    invalid_row = {**valid_row, field: value}

    result = transform_data([invalid_row, valid_row])

    assert result.valid_record_count == 1
    assert result.valid_records[0]["total_amount"] == 1000.0
    assert result.duplicate_order_ids == []
    assert result.rejected_record_count == 1
    rejected = result.rejected_records[0]
    assert rejected.reason == f"Missing required fields: {field}"
    assert rejected.row_number == 2
    assert rejected.payload == invalid_row


def test_transform_trims_surrounding_whitespace_from_text_fields():
    result = transform_data([{
        "order_id": "1",
        "customer_id": "  C001\t",
        "order_date": "2024-01-01",
        "product": "\tLaptop  ",
        "quantity": "2",
        "price": "500.0",
    }])

    assert result.rejected_record_count == 0
    assert result.valid_record_count == 1
    assert result.valid_records[0]["customer_id"] == "C001"
    assert result.valid_records[0]["product"] == "Laptop"
