from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from .models import (
        ContractValidationSummary,
        DataProfileSummary,
        DataQualitySummary,
        MonitoringAlert,
        MonitoringSummary,
        WarehouseExportSummary,
    )
except ImportError:  # pragma: no cover - fallback for direct script execution
    from models import (
        ContractValidationSummary,
        DataProfileSummary,
        DataQualitySummary,
        MonitoringAlert,
        MonitoringSummary,
        WarehouseExportSummary,
    )


def build_monitoring_summary(
    *,
    run_status: str,
    valid_record_count: int,
    rejected_record_count: int,
    contract_summary: ContractValidationSummary,
    quality_summary: DataQualitySummary,
    data_profile_summary: DataProfileSummary,
    warehouse_export_summary: WarehouseExportSummary,
    dry_run: bool,
    fail_on_quality_gate: bool,
) -> MonitoringSummary:
    alerts: list[MonitoringAlert] = []

    if run_status == "quality_gate_failed":
        alerts.append(
            _alert(
                rule="quality_gate_status",
                severity="critical",
                message="Quality gate failed and load step was skipped",
                actual_value=run_status,
                expected_value="success",
            )
        )
    elif run_status not in {"success", "dry_run_success"}:
        alerts.append(
            _alert(
                rule="run_status",
                severity="warning",
                message="Pipeline completed with warnings",
                actual_value=run_status,
                expected_value="success",
            )
        )

    if not contract_summary.passed:
        alerts.append(
            _alert(
                rule="contract_validation",
                severity="warning",
                message="Source data did not fully match the data contract",
                actual_value={
                    "missing_required_columns": contract_summary.missing_required_columns,
                    "unexpected_columns": contract_summary.unexpected_columns,
                    "duplicate_primary_keys": contract_summary.duplicate_primary_keys,
                },
                expected_value="contract passed",
            )
        )

    if not quality_summary.passed and not fail_on_quality_gate:
        alerts.append(
            _alert(
                rule="quality_thresholds",
                severity="warning",
                message="One or more quality thresholds failed",
                actual_value={
                    "rejection_rate": quality_summary.rejection_rate,
                    "duplicate_record_count": quality_summary.duplicate_record_count,
                },
                expected_value=quality_summary.thresholds.to_dict(),
            )
        )

    if rejected_record_count:
        alerts.append(
            _alert(
                rule="rejected_records",
                severity="warning",
                message="Transformation rejected one or more source rows",
                actual_value=rejected_record_count,
                expected_value=0,
            )
        )

    if data_profile_summary.row_count == 0:
        alerts.append(
            _alert(
                rule="empty_profile",
                severity="critical",
                message="No valid rows are available for profiling",
                actual_value=data_profile_summary.row_count,
                expected_value="at least 1 row",
            )
        )

    if _warehouse_export_mismatch(
        valid_record_count=valid_record_count,
        warehouse_export_summary=warehouse_export_summary,
        dry_run=dry_run,
        quality_summary=quality_summary,
    ):
        alerts.append(
            _alert(
                rule="warehouse_export_count",
                severity="warning",
                message="Warehouse export row count does not match valid transformed rows",
                actual_value=warehouse_export_summary.exported_record_count,
                expected_value=valid_record_count,
            )
        )

    critical_alert_count = sum(alert.severity == "critical" for alert in alerts)
    warning_alert_count = sum(alert.severity == "warning" for alert in alerts)
    status = "critical" if critical_alert_count else ("warning" if alerts else "healthy")

    return MonitoringSummary(
        status=status,
        alert_count=len(alerts),
        critical_alert_count=critical_alert_count,
        warning_alert_count=warning_alert_count,
        alerts=alerts,
    )


def write_monitoring_report(
    monitoring_summary: MonitoringSummary,
    output_path: str | Path,
) -> None:
    report_path = Path(output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(monitoring_summary.to_json(), encoding="utf-8")


def _alert(
    *,
    rule: str,
    severity: str,
    message: str,
    actual_value: Any,
    expected_value: Any,
) -> MonitoringAlert:
    return MonitoringAlert(
        rule=rule,
        severity=severity,
        message=message,
        actual_value=actual_value,
        expected_value=expected_value,
    )


def _warehouse_export_mismatch(
    *,
    valid_record_count: int,
    warehouse_export_summary: WarehouseExportSummary,
    dry_run: bool,
    quality_summary: DataQualitySummary,
) -> bool:
    if dry_run or not quality_summary.passed:
        return False
    return warehouse_export_summary.exported_record_count != valid_record_count
