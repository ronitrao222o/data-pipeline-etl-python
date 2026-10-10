import json
from datetime import date

import pytest

from src.profiling import build_data_profile, write_profile_report


@pytest.mark.parametrize(
    ("value", "inferred_type"),
    [(0, "integer"), (False, "boolean"), (" Mouse ", "string")],
)
def test_profile_counts_blank_text_as_missing(tmp_path, value, inferred_type):
    records = [{"value": item} for item in (None, "", " ", "\t\n", value)]
    records.append({})

    summary = build_data_profile(records, dataset_name="blank_values")
    column = summary.columns[0]

    assert column.null_count == 5
    assert column.null_rate == 0.8333
    assert column.distinct_count == 1
    assert column.inferred_type == inferred_type
    expected_bound = None if isinstance(value, bool) else value
    assert column.min_value == expected_bound
    assert column.max_value == expected_bound

    output_path = tmp_path / "profile.json"
    write_profile_report(summary, output_path)
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["columns"][0]["null_count"] == 5


def test_build_data_profile_summarises_column_shape(tmp_path):
    records = [
        {
            "order_id": 1,
            "customer_id": "C001",
            "order_date": date(2024, 1, 1),
            "product": "Laptop",
            "quantity": 1,
            "price": 60000.0,
        },
        {
            "order_id": 2,
            "customer_id": "C002",
            "order_date": date(2024, 1, 2),
            "product": "Mouse",
            "quantity": 2,
            "price": 500.0,
        },
        {
            "order_id": 3,
            "customer_id": "C002",
            "order_date": date(2024, 1, 3),
            "product": "",
            "quantity": 1,
            "price": 450.0,
        },
    ]

    summary = build_data_profile(records, dataset_name="sales_orders")

    columns_by_name = {column.name: column for column in summary.columns}
    assert summary.dataset_name == "sales_orders"
    assert summary.row_count == 3
    assert summary.column_count == 6
    assert columns_by_name["order_id"].inferred_type == "integer"
    assert columns_by_name["customer_id"].distinct_count == 2
    assert columns_by_name["order_date"].min_value == date(2024, 1, 1)
    assert columns_by_name["price"].max_value == 60000.0
    assert columns_by_name["product"].null_count == 1
    assert columns_by_name["product"].null_rate == 0.3333

    output_path = tmp_path / "profile.json"
    write_profile_report(summary, output_path)
    profile_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert profile_report["row_count"] == 3
    assert profile_report["columns"][0]["name"] == "customer_id"
