from pathlib import Path

from src.contracts import load_data_contract, validate_raw_contract


def test_load_data_contract_reads_expected_schema():
    contract_path = Path(__file__).resolve().parents[1] / "contracts/sales_orders_contract.yaml"

    contract = load_data_contract(contract_path)

    assert contract.dataset_name == "sales_orders"
    assert contract.primary_key == "order_id"
    assert [column.name for column in contract.columns] == [
        "order_id",
        "customer_id",
        "order_date",
        "product",
        "quantity",
        "price",
    ]


def test_validate_raw_contract_flags_schema_and_key_issues():
    contract_path = Path(__file__).resolve().parents[1] / "contracts/sales_orders_contract.yaml"
    contract = load_data_contract(contract_path)
    raw_records = [
        {
            "order_id": "1",
            "customer_id": "C001",
            "order_date": "2024-01-01",
            "product": "Laptop",
            "quantity": "1",
            "extra_column": "ignored",
        },
        {
            "order_id": "1",
            "customer_id": "C002",
            "order_date": "2024-01-02",
            "product": "Mouse",
            "quantity": "2",
            "extra_column": "ignored",
        },
    ]

    summary = validate_raw_contract(raw_records, contract)

    assert summary.passed is False
    assert summary.missing_required_columns == ["price"]
    assert summary.unexpected_columns == ["extra_column"]
    assert summary.duplicate_primary_keys == ["1"]
