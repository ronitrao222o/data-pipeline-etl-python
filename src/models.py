from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any


def _json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


@dataclass(frozen=True)
class PipelineConfig:
    raw_data_path: Path
    data_contract_path: Path
    database_path: Path
    schema_path: Path
    report_output_path: Path
    analytics_output_path: Path
    profile_output_path: Path
    warehouse_output_path: Path
    log_level: str = "INFO"
    analytics_top_n: int = 5
    quality_thresholds: DataQualityThresholds | None = None
    runtime: RuntimeConfig | None = None


@dataclass(frozen=True)
class DataQualityThresholds:
    min_valid_records: int = 1
    max_rejection_rate: float = 0.25
    max_duplicate_records: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_valid_records": self.min_valid_records,
            "max_rejection_rate": self.max_rejection_rate,
            "max_duplicate_records": self.max_duplicate_records,
        }


@dataclass(frozen=True)
class RuntimeConfig:
    environment: str = "dev"
    owner: str = "analytics-engineering"
    default_trigger_mode: str = "manual"
    schedule_name: str = "adhoc"
    schedule_cron: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "owner": self.owner,
            "default_trigger_mode": self.default_trigger_mode,
            "schedule_name": self.schedule_name,
            "schedule_cron": self.schedule_cron,
        }


@dataclass(frozen=True)
class ContractColumn:
    name: str
    type: str
    required: bool
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
        }


@dataclass(frozen=True)
class DataContract:
    dataset_name: str
    version: str
    primary_key: str
    columns: list[ContractColumn]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "version": self.version,
            "primary_key": self.primary_key,
            "columns": _json_ready(self.columns),
        }


@dataclass(frozen=True)
class ContractValidationSummary:
    dataset_name: str
    version: str
    row_count: int
    expected_columns: list[str]
    missing_required_columns: list[str]
    unexpected_columns: list[str]
    duplicate_primary_keys: list[str]
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "version": self.version,
            "row_count": self.row_count,
            "expected_columns": self.expected_columns,
            "missing_required_columns": self.missing_required_columns,
            "unexpected_columns": self.unexpected_columns,
            "duplicate_primary_keys": self.duplicate_primary_keys,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class RejectedRecord:
    row_number: int
    reason: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_number": self.row_number,
            "reason": self.reason,
            "payload": _json_ready(self.payload),
        }


@dataclass
class TransformationResult:
    valid_records: list[dict[str, Any]] = field(default_factory=list)
    rejected_records: list[RejectedRecord] = field(default_factory=list)
    duplicate_order_ids: list[int] = field(default_factory=list)

    @property
    def extracted_count(self) -> int:
        return len(self.valid_records) + len(self.rejected_records)

    @property
    def valid_record_count(self) -> int:
        return len(self.valid_records)

    @property
    def rejected_record_count(self) -> int:
        return len(self.rejected_records)

    @property
    def total_revenue(self) -> float:
        return round(
            sum(float(record["total_amount"]) for record in self.valid_records),
            2,
        )

    def metrics(self) -> dict[str, Any]:
        return {
            "extracted_count": self.extracted_count,
            "valid_record_count": self.valid_record_count,
            "rejected_record_count": self.rejected_record_count,
            "duplicate_order_ids": self.duplicate_order_ids,
            "total_revenue": self.total_revenue,
        }


@dataclass(frozen=True)
class QualityCheckResult:
    name: str
    passed: bool
    actual_value: float | int
    expected_value: float | int
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "message": self.message,
        }


@dataclass(frozen=True)
class DataQualitySummary:
    passed: bool
    rejection_rate: float
    duplicate_record_count: int
    unique_customer_count: int
    unique_product_count: int
    average_order_value: float
    total_revenue: float
    order_date_range: dict[str, date | None]
    thresholds: DataQualityThresholds
    checks: list[QualityCheckResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "rejection_rate": self.rejection_rate,
            "duplicate_record_count": self.duplicate_record_count,
            "unique_customer_count": self.unique_customer_count,
            "unique_product_count": self.unique_product_count,
            "average_order_value": self.average_order_value,
            "total_revenue": self.total_revenue,
            "order_date_range": _json_ready(self.order_date_range),
            "thresholds": self.thresholds.to_dict(),
            "checks": _json_ready(self.checks),
        }


@dataclass(frozen=True)
class AnalyticsDimensionMetric:
    name: str
    order_count: int
    quantity_sold: int
    revenue: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "order_count": self.order_count,
            "quantity_sold": self.quantity_sold,
            "revenue": self.revenue,
        }


@dataclass(frozen=True)
class SalesAnalyticsSummary:
    order_count: int
    total_quantity: int
    total_revenue: float
    average_order_value: float
    top_products: list[AnalyticsDimensionMetric]
    top_customers: list[AnalyticsDimensionMetric]
    daily_revenue: list[AnalyticsDimensionMetric]

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_count": self.order_count,
            "total_quantity": self.total_quantity,
            "total_revenue": self.total_revenue,
            "average_order_value": self.average_order_value,
            "top_products": _json_ready(self.top_products),
            "top_customers": _json_ready(self.top_customers),
            "daily_revenue": _json_ready(self.daily_revenue),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    inferred_type: str
    null_count: int
    null_rate: float
    distinct_count: int
    min_value: Any | None
    max_value: Any | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "inferred_type": self.inferred_type,
            "null_count": self.null_count,
            "null_rate": self.null_rate,
            "distinct_count": self.distinct_count,
            "min_value": _json_ready(self.min_value),
            "max_value": _json_ready(self.max_value),
        }


@dataclass(frozen=True)
class DataProfileSummary:
    dataset_name: str
    row_count: int
    column_count: int
    columns: list[ColumnProfile]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": _json_ready(self.columns),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass(frozen=True)
class WarehouseExportPartition:
    partition_value: str
    path: Path
    record_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "partition_value": self.partition_value,
            "path": _json_ready(self.path),
            "record_count": self.record_count,
        }


@dataclass(frozen=True)
class WarehouseExportSummary:
    output_path: Path
    manifest_path: Path
    partition_column: str
    partition_count: int
    exported_record_count: int
    skipped: bool
    partitions: list[WarehouseExportPartition]

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_path": _json_ready(self.output_path),
            "manifest_path": _json_ready(self.manifest_path),
            "partition_column": self.partition_column,
            "partition_count": self.partition_count,
            "exported_record_count": self.exported_record_count,
            "skipped": self.skipped,
            "partitions": _json_ready(self.partitions),
        }


@dataclass(frozen=True)
class RuntimeSummary:
    run_id: str
    environment: str
    owner: str
    trigger_mode: str
    schedule_name: str
    schedule_cron: str | None
    dry_run: bool
    load_step_skipped: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "environment": self.environment,
            "owner": self.owner,
            "trigger_mode": self.trigger_mode,
            "schedule_name": self.schedule_name,
            "schedule_cron": self.schedule_cron,
            "dry_run": self.dry_run,
            "load_step_skipped": self.load_step_skipped,
        }


@dataclass(frozen=True)
class PipelineRunSummary:
    status: str
    started_at: datetime
    completed_at: datetime
    source_path: Path
    database_path: Path
    report_path: Path
    analytics_report_path: Path
    profile_report_path: Path
    extracted_count: int
    valid_record_count: int
    loaded_count: int
    rejected_record_count: int
    duplicate_order_ids: list[int]
    total_revenue: float
    rejected_records: list[RejectedRecord]
    contract_summary: ContractValidationSummary
    quality_summary: DataQualitySummary
    runtime_summary: RuntimeSummary
    analytics_summary: SalesAnalyticsSummary
    data_profile_summary: DataProfileSummary
    warehouse_export_summary: WarehouseExportSummary

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "started_at": _json_ready(self.started_at),
            "completed_at": _json_ready(self.completed_at),
            "source_path": _json_ready(self.source_path),
            "database_path": _json_ready(self.database_path),
            "report_path": _json_ready(self.report_path),
            "analytics_report_path": _json_ready(self.analytics_report_path),
            "profile_report_path": _json_ready(self.profile_report_path),
            "extracted_count": self.extracted_count,
            "valid_record_count": self.valid_record_count,
            "loaded_count": self.loaded_count,
            "rejected_record_count": self.rejected_record_count,
            "duplicate_order_ids": self.duplicate_order_ids,
            "total_revenue": self.total_revenue,
            "rejected_records": _json_ready(self.rejected_records),
            "contract_summary": self.contract_summary.to_dict(),
            "quality_summary": self.quality_summary.to_dict(),
            "runtime_summary": self.runtime_summary.to_dict(),
            "analytics_summary": self.analytics_summary.to_dict(),
            "data_profile_summary": self.data_profile_summary.to_dict(),
            "warehouse_export_summary": self.warehouse_export_summary.to_dict(),
        }
