from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any


def _json_ready(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (datetime, date)):
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
    database_path: Path
    schema_path: Path
    report_output_path: Path
    log_level: str = "INFO"
    quality_thresholds: "DataQualityThresholds" | None = None


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
class PipelineRunSummary:
    status: str
    started_at: datetime
    completed_at: datetime
    source_path: Path
    database_path: Path
    report_path: Path
    extracted_count: int
    valid_record_count: int
    loaded_count: int
    rejected_record_count: int
    duplicate_order_ids: list[int]
    total_revenue: float
    rejected_records: list[RejectedRecord]
    quality_summary: DataQualitySummary

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "started_at": _json_ready(self.started_at),
            "completed_at": _json_ready(self.completed_at),
            "source_path": _json_ready(self.source_path),
            "database_path": _json_ready(self.database_path),
            "report_path": _json_ready(self.report_path),
            "extracted_count": self.extracted_count,
            "valid_record_count": self.valid_record_count,
            "loaded_count": self.loaded_count,
            "rejected_record_count": self.rejected_record_count,
            "duplicate_order_ids": self.duplicate_order_ids,
            "total_revenue": self.total_revenue,
            "rejected_records": _json_ready(self.rejected_records),
            "quality_summary": self.quality_summary.to_dict(),
        }
