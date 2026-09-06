import json
from datetime import date
from pathlib import Path

from src.models import (
    ContractValidationSummary,
    DataProfileSummary,
    DataQualitySummary,
    DataQualityThresholds,
    QualityCheckResult,
    WarehouseExportSummary,
)
from src.monitoring import build_monitoring_summary, write_monitoring_report


def test_build_monitoring_summary_reports_healthy_run(tmp_path):
    summary = build_monitoring_summary(
        run_status="success",
        valid_record_count=2,
        rejected_record_count=0,
        contract_summary=_contract_summary(passed=True),
        quality_summary=_quality_summary(passed=True),
        data_profile_summary=_profile_summary(row_count=2),
        warehouse_export_summary=_warehouse_summary(tmp_path, exported_record_count=2),
        dry_run=False,
        fail_on_quality_gate=False,
    )

    assert summary.status == "healthy"
    assert summary.alert_count == 0


def test_build_monitoring_summary_reports_quality_gate_failure(tmp_path):
    summary = build_monitoring_summary(
        run_status="quality_gate_failed",
        valid_record_count=0,
        rejected_record_count=2,
        contract_summary=_contract_summary(passed=False),
        quality_summary=_quality_summary(passed=False),
        data_profile_summary=_profile_summary(row_count=0),
        warehouse_export_summary=_warehouse_summary(tmp_path, exported_record_count=0),
        dry_run=False,
        fail_on_quality_gate=True,
    )

    alert_rules = {alert.rule for alert in summary.alerts}
    assert summary.status == "critical"
    assert summary.critical_alert_count == 2
    assert "quality_gate_status" in alert_rules
    assert "contract_validation" in alert_rules
    assert "empty_profile" in alert_rules

    output_path = tmp_path / "monitoring.json"
    write_monitoring_report(summary, output_path)
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["status"] == "critical"
    assert report["alert_count"] == 4


def _contract_summary(passed: bool) -> ContractValidationSummary:
    return ContractValidationSummary(
        dataset_name="sales_orders",
        version="1.0",
        row_count=2,
        expected_columns=["order_id"],
        missing_required_columns=[] if passed else ["order_id"],
        unexpected_columns=[],
        duplicate_primary_keys=[],
        passed=passed,
    )


def _quality_summary(passed: bool) -> DataQualitySummary:
    thresholds = DataQualityThresholds(
        min_valid_records=1,
        max_rejection_rate=0.1,
        max_duplicate_records=0,
    )
    return DataQualitySummary(
        passed=passed,
        rejection_rate=0.0 if passed else 1.0,
        duplicate_record_count=0,
        unique_customer_count=1,
        unique_product_count=1,
        average_order_value=100.0,
        total_revenue=100.0,
        order_date_range={"start": date(2024, 1, 1), "end": date(2024, 1, 1)},
        thresholds=thresholds,
        checks=[
            QualityCheckResult(
                name="max_rejection_rate",
                passed=passed,
                actual_value=0.0 if passed else 1.0,
                expected_value=thresholds.max_rejection_rate,
                message="quality check result",
            )
        ],
    )


def _profile_summary(row_count: int) -> DataProfileSummary:
    return DataProfileSummary(
        dataset_name="sales_orders",
        row_count=row_count,
        column_count=0,
        columns=[],
    )


def _warehouse_summary(
    tmp_path: Path,
    exported_record_count: int,
) -> WarehouseExportSummary:
    return WarehouseExportSummary(
        output_path=tmp_path / "warehouse",
        manifest_path=tmp_path / "warehouse/_manifest.json",
        partition_column="order_month",
        partition_count=1 if exported_record_count else 0,
        exported_record_count=exported_record_count,
        skipped=False,
        partitions=[],
    )
