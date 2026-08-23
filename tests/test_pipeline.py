import json
import sqlite3
from pathlib import Path

from src.pipeline import run_pipeline


def test_run_pipeline_writes_database_and_report(tmp_path):
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
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
                f"database_path: {tmp_path / 'sales.db'}",
                f"schema_path: {schema_path}",
                f"report_output_path: {tmp_path / 'report.json'}",
                "log_level: INFO",
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
    assert report["status"] == "success"
    assert report["loaded_count"] == 2
