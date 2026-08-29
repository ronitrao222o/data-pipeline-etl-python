from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    from .models import ColumnProfile, DataProfileSummary
except ImportError:  # pragma: no cover - fallback for direct script execution
    from models import ColumnProfile, DataProfileSummary


def build_data_profile(
    records: list[dict[str, Any]],
    dataset_name: str,
) -> DataProfileSummary:
    column_names = _collect_column_names(records)
    column_profiles = [
        _profile_column(column_name, [record.get(column_name) for record in records], len(records))
        for column_name in column_names
    ]
    return DataProfileSummary(
        dataset_name=dataset_name,
        row_count=len(records),
        column_count=len(column_names),
        columns=column_profiles,
    )


def write_profile_report(
    profile_summary: DataProfileSummary,
    output_path: str | Path,
) -> None:
    report_path = Path(output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(profile_summary.to_dict(), indent=2),
        encoding="utf-8",
    )


def _collect_column_names(records: list[dict[str, Any]]) -> list[str]:
    column_names: set[str] = set()
    for record in records:
        column_names.update(record.keys())
    return sorted(column_names)


def _profile_column(
    name: str,
    values: list[Any],
    row_count: int,
) -> ColumnProfile:
    non_null_values = [value for value in values if value not in (None, "")]
    null_count = row_count - len(non_null_values)
    inferred_type = _infer_type(non_null_values)
    min_value, max_value = _min_max_values(non_null_values)

    return ColumnProfile(
        name=name,
        inferred_type=inferred_type,
        null_count=null_count,
        null_rate=round(null_count / row_count, 4) if row_count else 0.0,
        distinct_count=len({_normalise_distinct_value(value) for value in non_null_values}),
        min_value=min_value,
        max_value=max_value,
    )


def _infer_type(values: list[Any]) -> str:
    if not values:
        return "empty"
    if all(isinstance(value, bool) for value in values):
        return "boolean"
    if all(isinstance(value, int) and not isinstance(value, bool) for value in values):
        return "integer"
    if all(isinstance(value, int | float) and not isinstance(value, bool) for value in values):
        return "number"
    if all(isinstance(value, datetime | date) for value in values):
        return "date"
    return "string"


def _min_max_values(values: list[Any]) -> tuple[Any | None, Any | None]:
    if not values:
        return None, None
    if all(isinstance(value, int | float) and not isinstance(value, bool) for value in values):
        return min(values), max(values)
    if all(isinstance(value, datetime | date) for value in values):
        return (
            min(values, key=lambda value: value.isoformat()),
            max(values, key=lambda value: value.isoformat()),
        )
    if all(isinstance(value, str) for value in values):
        return min(values), max(values)
    return None, None


def _normalise_distinct_value(value: Any) -> str:
    if isinstance(value, datetime | date):
        return value.isoformat()
    return str(value)
