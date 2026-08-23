from __future__ import annotations

from datetime import date

try:
    from .models import (
        DataQualitySummary,
        DataQualityThresholds,
        PipelineRunSummary,
        QualityCheckResult,
        TransformationResult,
    )
except ImportError:  # pragma: no cover - fallback for direct script execution
    from models import (
        DataQualitySummary,
        DataQualityThresholds,
        PipelineRunSummary,
        QualityCheckResult,
        TransformationResult,
    )


class DataQualityError(Exception):
    def __init__(self, summary: PipelineRunSummary):
        super().__init__("Data quality gate failed")
        self.summary = summary


def _build_check(
    name: str,
    passed: bool,
    actual_value: float | int,
    expected_value: float | int,
    comparator_text: str,
) -> QualityCheckResult:
    return QualityCheckResult(
        name=name,
        passed=passed,
        actual_value=actual_value,
        expected_value=expected_value,
        message=f"{name} {comparator_text} threshold",
    )


def _order_date_range(valid_records: list[dict[str, object]]) -> dict[str, date | None]:
    order_dates = [record["order_date"] for record in valid_records]
    if not order_dates:
        return {"start": None, "end": None}
    return {"start": min(order_dates), "end": max(order_dates)}


def evaluate_data_quality(
    transformation_result: TransformationResult,
    thresholds: DataQualityThresholds,
) -> DataQualitySummary:
    valid_records = transformation_result.valid_records
    extracted_count = max(transformation_result.extracted_count, 1)
    rejection_rate = round(
        transformation_result.rejected_record_count / extracted_count,
        4,
    )
    duplicate_record_count = len(transformation_result.duplicate_order_ids)
    unique_customer_count = len({record["customer_id"] for record in valid_records})
    unique_product_count = len({record["product"] for record in valid_records})
    total_revenue = round(
        sum(float(record["total_amount"]) for record in valid_records),
        2,
    )
    average_order_value = round(total_revenue / len(valid_records), 2) if valid_records else 0.0

    checks = [
        _build_check(
            name="min_valid_records",
            passed=transformation_result.valid_record_count >= thresholds.min_valid_records,
            actual_value=transformation_result.valid_record_count,
            expected_value=thresholds.min_valid_records,
            comparator_text="meets or exceeds",
        ),
        _build_check(
            name="max_rejection_rate",
            passed=rejection_rate <= thresholds.max_rejection_rate,
            actual_value=rejection_rate,
            expected_value=thresholds.max_rejection_rate,
            comparator_text="is less than or equal to",
        ),
        _build_check(
            name="max_duplicate_records",
            passed=duplicate_record_count <= thresholds.max_duplicate_records,
            actual_value=duplicate_record_count,
            expected_value=thresholds.max_duplicate_records,
            comparator_text="is less than or equal to",
        ),
    ]

    return DataQualitySummary(
        passed=all(check.passed for check in checks),
        rejection_rate=rejection_rate,
        duplicate_record_count=duplicate_record_count,
        unique_customer_count=unique_customer_count,
        unique_product_count=unique_product_count,
        average_order_value=average_order_value,
        total_revenue=total_revenue,
        order_date_range=_order_date_range(valid_records),
        thresholds=thresholds,
        checks=checks,
    )
