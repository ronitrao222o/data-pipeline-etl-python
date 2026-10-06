import sqlite3
from datetime import date
from pathlib import Path

import pytest

from src.load import load_data
from src.transform import transform_data


@pytest.mark.parametrize("order_date", ["2024-01-01", " 2024-01-01 ", "\t2024-01-01\r\n"])
def test_transform_trims_date_whitespace(order_date):
    result = transform_data([{
        "order_id": "1",
        "customer_id": "C001",
        "order_date": order_date,
        "product": "Laptop",
        "quantity": "2",
        "price": "500.0",
    }])

    assert result.rejected_record_count == 0
    assert result.valid_records[0]["order_date"] == date(2024, 1, 1)


@pytest.mark.parametrize("order_date", [" 2024-02-30 ", " 01/01/2024 ", 20240101])
def test_transform_rejects_invalid_dates_and_continues(order_date):
    row = {
        "order_id": "1",
        "customer_id": "C001",
        "order_date": order_date,
        "product": "Laptop",
        "quantity": "2",
        "price": "500.0",
    }

    result = transform_data([row, {**row, "order_date": " 2024-01-01 "}])

    assert result.valid_record_count == 1
    assert result.duplicate_order_ids == []
    assert result.rejected_record_count == 1
    rejected = result.rejected_records[0]
    assert rejected.reason.startswith("Type conversion error:")
    assert rejected.row_number == 2
    assert rejected.payload == row


@pytest.mark.parametrize("order_id", [str(-(2**63) - 1), str(2**63), "9" * 100])
def test_transform_rejects_order_id_outside_sqlite_range(order_id):
    row = {
        "order_id": order_id,
        "customer_id": "C001",
        "order_date": "2024-01-01",
        "product": "Laptop",
        "quantity": "2",
        "price": "500.0",
    }

    result = transform_data([row, {**row, "order_id": "1"}])

    assert [record["order_id"] for record in result.valid_records] == [1]
    assert result.rejected_record_count == 1
    assert result.duplicate_order_ids == []
    rejected = result.rejected_records[0]
    assert rejected.reason == "Order ID must fit in a signed 64-bit SQLite integer"
    assert rejected.row_number == 2
    assert rejected.payload == row


@pytest.mark.parametrize("order_id", [-(2**63), 2**63 - 1])
def test_transform_sqlite_order_id_boundaries_can_be_loaded(tmp_path, order_id):
    result = transform_data([{
        "order_id": str(order_id),
        "customer_id": "C001",
        "order_date": "2024-01-01",
        "product": "Laptop",
        "quantity": "2",
        "price": "500.0",
    }])
    database_path = tmp_path / "sales.db"
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"

    assert result.rejected_record_count == 0
    assert load_data(result.valid_records, database_path, schema_path) == 1
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT order_id FROM sales").fetchall() == [(order_id,)]


@pytest.mark.parametrize("quantity", [str(2**63), "1" + "0" * 400])
@pytest.mark.parametrize("price", ["0", "1.0"])
def test_transform_rejects_quantity_outside_sqlite_range(quantity, price):
    row = {
        "order_id": "1",
        "customer_id": "C001",
        "order_date": "2024-01-01",
        "product": "Laptop",
        "quantity": quantity,
        "price": price,
    }

    result = transform_data([row, {**row, "quantity": "2"}])

    assert result.valid_record_count == 1
    assert result.valid_records[0]["quantity"] == 2
    assert result.duplicate_order_ids == []
    assert result.rejected_record_count == 1
    rejected = result.rejected_records[0]
    assert rejected.reason == "Quantity must fit in a signed 64-bit SQLite integer"
    assert rejected.row_number == 2
    assert rejected.payload == row


@pytest.mark.parametrize("quantity", [1, 2**63 - 1])
def test_transform_sqlite_quantity_boundaries_can_be_loaded(tmp_path, quantity):
    result = transform_data([{
        "order_id": "1",
        "customer_id": "C001",
        "order_date": "2024-01-01",
        "product": "Laptop",
        "quantity": str(quantity),
        "price": "1.0",
    }])
    database_path = tmp_path / "sales.db"
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"

    assert result.rejected_record_count == 0
    assert load_data(result.valid_records, database_path, schema_path) == 1
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT quantity FROM sales").fetchall() == [(quantity,)]


def test_transform_rejects_total_overflow_and_continues():
    row = {
        "order_id": "1",
        "customer_id": "C001",
        "order_date": "2024-01-01",
        "product": "Laptop",
        "quantity": "2",
        "price": "1e308",
    }

    result = transform_data([row, {**row, "quantity": "2", "price": "500.0"}])

    assert result.valid_record_count == 1
    assert result.valid_records[0]["total_amount"] == 1000.0
    assert result.duplicate_order_ids == []
    assert result.rejected_record_count == 1
    rejected = result.rejected_records[0]
    assert rejected.reason == "Total amount must be a finite number"
    assert rejected.row_number == 2
    assert rejected.payload == row


@pytest.mark.parametrize("price", ["NaN", "nan", "inf", "-inf", "Infinity", "1e309"])
def test_transform_rejects_non_finite_price_without_reserving_order_id(price):
    row = {
        "order_id": "1",
        "customer_id": "C001",
        "order_date": "2024-01-01",
        "product": "Laptop",
        "quantity": "2",
        "price": price,
    }

    result = transform_data([row, {**row, "price": "500.0"}])

    assert result.valid_record_count == 1
    assert result.valid_records[0]["total_amount"] == 1000.0
    assert result.duplicate_order_ids == []
    assert result.rejected_record_count == 1
    rejected = result.rejected_records[0]
    assert rejected.reason == "Price must be a finite number"
    assert rejected.row_number == 2
    assert rejected.payload == row


def test_transform_accepts_zero_price():
    result = transform_data([
        {
            "order_id": "1",
            "customer_id": "C001",
            "order_date": "2024-01-01",
            "product": "Free sample",
            "quantity": "2",
            "price": "0",
        }
    ])

    assert result.valid_record_count == 1
    assert result.rejected_record_count == 0
    assert result.valid_records[0]["total_amount"] == 0.0


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
