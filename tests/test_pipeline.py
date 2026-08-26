import json
import sqlite3
from pathlib import Path

import pytest

from src.pipeline import run_pipeline
from src.quality import DataQualityError


def test_run_pipeline_writes_database_and_report(tmp_path):
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    contract_path = Path(__file__).resolve().parents[1] / "contracts/sales_orders_contract.yaml"
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_id,customer_id,order_date,product,quantity,price",
                "201,C010,2024-02-01,Laptop,1,65000",
                "202,C011,2024-02-02,Mouse,2,500",
                "202,C011,2024-02-03,Mouse,1,500",
            ]
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                f"raw_data_path: {csv_path}",
                f"data_contract_path: {contract_path}",
                f"database_path: {tmp_path / 'sales.db'}",
                f"schema_path: {schema_path}",
                f"report_output_path: {tmp_path / 'report.json'}",
                f"analytics_output_path: {tmp_path / 'analytics.json'}",
                "log_level: INFO",
                "quality_thresholds:",
                "  min_valid_records: 2",
                "  max_rejection_rate: 0.5",
                "  max_duplicate_records: 1",
            ]
        ),
        encoding="utf-8",
    )

    summary = run_pipeline(str(config_path))

    assert summary.loaded_count == 2
    assert summary.rejected_record_count == 1
    assert summary.duplicate_order_ids == [202]

    with sqlite3.connect(tmp_path / "sales.db") as conn:
        rows = conn.execute("SELECT order_id, total_amount FROM sales ORDER BY order_id").fetchall()

    assert rows == [(201, 65000.0), (202, 1000.0)]

    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    analytics_report = json.loads((tmp_path / "analytics.json").read_text(encoding="utf-8"))
    assert report["status"] == "success"
    assert report["loaded_count"] == 2
    assert report["contract_summary"]["passed"] is False
    assert report["contract_summary"]["dataset_name"] == "sales_orders"
    assert report["contract_summary"]["duplicate_primary_keys"] == ["202"]
    assert report["quality_summary"]["passed"] is True
    assert report["analytics_summary"]["total_revenue"] == 66000.0
    assert analytics_report["top_products"][0]["name"] == "Laptop"


def test_run_pipeline_returns_warning_status_when_quality_fails(tmp_path):
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    contract_path = Path(__file__).resolve().parents[1] / "contracts/sales_orders_contract.yaml"
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_id,customer_id,order_date,product,quantity,price",
                "301,C010,2024-02-01,Laptop,1,65000",
                "301,C011,2024-02-02,Mouse,2,500",
            ]
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                f"raw_data_path: {csv_path}",
                f"data_contract_path: {contract_path}",
                f"database_path: {tmp_path / 'sales.db'}",
                f"schema_path: {schema_path}",
                f"report_output_path: {tmp_path / 'report.json'}",
                f"analytics_output_path: {tmp_path / 'analytics.json'}",
                "log_level: INFO",
                "quality_thresholds:",
                "  min_valid_records: 2",
                "  max_rejection_rate: 0.0",
                "  max_duplicate_records: 0",
            ]
        ),
        encoding="utf-8",
    )

    summary = run_pipeline(str(config_path))

    assert summary.status == "completed_with_quality_warnings"
    assert summary.quality_summary.passed is False
    assert summary.loaded_count == 1


def test_run_pipeline_can_fail_on_quality_gate(tmp_path):
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    contract_path = Path(__file__).resolve().parents[1] / "contracts/sales_orders_contract.yaml"
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_id,customer_id,order_date,product,quantity,price",
                "401,C010,2024-02-01,Laptop,1,65000",
                "401,C011,2024-02-02,Mouse,2,500",
            ]
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                f"raw_data_path: {csv_path}",
                f"data_contract_path: {contract_path}",
                f"database_path: {tmp_path / 'sales.db'}",
                f"schema_path: {schema_path}",
                f"report_output_path: {tmp_path / 'report.json'}",
                f"analytics_output_path: {tmp_path / 'analytics.json'}",
                "log_level: INFO",
                "quality_thresholds:",
                "  min_valid_records: 2",
                "  max_rejection_rate: 0.0",
                "  max_duplicate_records: 0",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(DataQualityError) as error:
        run_pipeline(str(config_path), fail_on_quality_gate=True)

    assert error.value.summary.status == "quality_gate_failed"
    assert error.value.summary.quality_summary.passed is False
    assert error.value.summary.loaded_count == 0
    assert (tmp_path / "analytics.json").exists()


def test_run_pipeline_supports_dry_run_and_runtime_metadata(tmp_path):
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    contract_path = Path(__file__).resolve().parents[1] / "contracts/sales_orders_contract.yaml"
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(
        "\n".join(
            [
                "order_id,customer_id,order_date,product,quantity,price",
                "501,C010,2024-02-01,Laptop,1,65000",
                "502,C011,2024-02-02,Mouse,2,500",
            ]
        ),
        encoding="utf-8",
    )

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                f"raw_data_path: {csv_path}",
                f"data_contract_path: {contract_path}",
                f"database_path: {tmp_path / 'sales.db'}",
                f"schema_path: {schema_path}",
                f"report_output_path: {tmp_path / 'report.json'}",
                f"analytics_output_path: {tmp_path / 'analytics.json'}",
                "log_level: INFO",
                "runtime:",
                "  environment: prod",
                "  owner: data-platform",
                "  default_trigger_mode: scheduled",
                "  schedule_name: nightly-sales-etl",
                "  schedule_cron: '0 1 * * *'",
                "quality_thresholds:",
                "  min_valid_records: 2",
                "  max_rejection_rate: 0.0",
                "  max_duplicate_records: 0",
            ]
        ),
        encoding="utf-8",
    )

    summary = run_pipeline(
        str(config_path),
        dry_run=True,
        run_id="airflow-run-001",
        trigger_mode="scheduled",
    )

    assert summary.status == "dry_run_success"
    assert summary.loaded_count == 0
    assert summary.runtime_summary.run_id == "airflow-run-001"
    assert summary.runtime_summary.environment == "prod"
    assert summary.runtime_summary.trigger_mode == "scheduled"
    assert summary.runtime_summary.dry_run is True
    assert summary.runtime_summary.load_step_skipped is True
    assert summary.analytics_summary.total_revenue == 66000.0
    assert not (tmp_path / "sales.db").exists()
