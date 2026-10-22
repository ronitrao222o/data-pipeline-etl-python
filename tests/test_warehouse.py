import json
from datetime import date

from src.warehouse import export_partitioned_sales


def test_export_partitioned_sales_writes_partitions_and_manifest(tmp_path):
    records = [
        {
            "order_id": 1,
            "customer_id": "C001",
            "order_date": date(2024, 1, 10),
            "product": "Laptop",
            "quantity": 1,
            "price": 60000.0,
            "total_amount": 60000.0,
        },
        {
            "order_id": 2,
            "customer_id": "C002",
            "order_date": date(2024, 2, 5),
            "product": "Mouse",
            "quantity": 2,
            "price": 500.0,
            "total_amount": 1000.0,
        },
    ]

    summary = export_partitioned_sales(records, tmp_path / "warehouse", run_id="test-run-001")

    assert summary.partition_count == 2
    assert summary.exported_record_count == 2
    assert summary.skipped is False
    assert (tmp_path / "warehouse/order_month=2024-01/part-000.csv").exists()
    assert (tmp_path / "warehouse/order_month=2024-02/part-000.csv").exists()

    manifest = json.loads((tmp_path / "warehouse/_manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_id"] == "test-run-001"
    assert manifest["partition_column"] == "order_month"
    assert manifest["exported_record_count"] == 2


def test_export_partitioned_sales_removes_stale_generated_partitions(tmp_path):
    january = {
        "order_id": 1,
        "customer_id": "C001",
        "order_date": date(2024, 1, 10),
        "product": "Laptop",
        "quantity": 1,
        "price": 60000.0,
        "total_amount": 60000.0,
    }
    february = {**january, "order_id": 2, "order_date": date(2024, 2, 5)}
    output_path = tmp_path / "warehouse"

    export_partitioned_sales([january, february], output_path, run_id="first-run")
    unrelated_file = output_path / "order_month=2024-01" / "notes.txt"
    unrelated_file.write_text("keep this", encoding="utf-8")

    summary = export_partitioned_sales([february], output_path, run_id="second-run")

    assert not (output_path / "order_month=2024-01" / "part-000.csv").exists()
    assert unrelated_file.read_text(encoding="utf-8") == "keep this"
    assert (output_path / "order_month=2024-02" / "part-000.csv").exists()
    assert summary.partition_count == 1
    manifest = json.loads((output_path / "_manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_id"] == "second-run"
    assert [part["partition_value"] for part in manifest["partitions"]] == ["2024-02"]


def test_export_partitioned_sales_skips_files_for_dry_run(tmp_path):
    summary = export_partitioned_sales(
        records=[],
        output_path=tmp_path / "warehouse",
        run_id="dry-run-001",
        dry_run=True,
    )

    assert summary.skipped is True
    assert summary.exported_record_count == 0
    assert not (tmp_path / "warehouse").exists()
