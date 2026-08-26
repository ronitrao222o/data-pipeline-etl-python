from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

try:
    from .models import ContractColumn, ContractValidationSummary, DataContract
except ImportError:  # pragma: no cover - fallback for direct script execution
    from models import ContractColumn, ContractValidationSummary, DataContract


def load_data_contract(path: str | Path) -> DataContract:
    contract_path = Path(path)
    raw_contract: dict[str, Any] = yaml.safe_load(contract_path.read_text(encoding="utf-8"))

    return DataContract(
        dataset_name=str(raw_contract["dataset_name"]),
        version=str(raw_contract["version"]),
        primary_key=str(raw_contract["primary_key"]),
        columns=[
            ContractColumn(
                name=str(column["name"]),
                type=str(column["type"]),
                required=bool(column.get("required", False)),
                description=str(column.get("description", "")),
            )
            for column in raw_contract["columns"]
        ],
    )


def validate_raw_contract(
    raw_records: list[dict[str, Any]],
    contract: DataContract,
) -> ContractValidationSummary:
    expected_columns = {column.name for column in contract.columns}
    required_columns = {column.name for column in contract.columns if column.required}
    observed_columns = (
        set().union(*(record.keys() for record in raw_records))
        if raw_records
        else set()
    )

    missing_required_columns = sorted(required_columns - observed_columns)
    unexpected_columns = sorted(observed_columns - expected_columns)
    duplicate_primary_keys = _duplicate_values(raw_records, contract.primary_key)

    return ContractValidationSummary(
        dataset_name=contract.dataset_name,
        version=contract.version,
        row_count=len(raw_records),
        expected_columns=sorted(expected_columns),
        missing_required_columns=missing_required_columns,
        unexpected_columns=unexpected_columns,
        duplicate_primary_keys=duplicate_primary_keys,
        passed=(
            not missing_required_columns
            and not unexpected_columns
            and not duplicate_primary_keys
        ),
    )


def _duplicate_values(records: list[dict[str, Any]], key: str) -> list[str]:
    seen_values: set[str] = set()
    duplicates: set[str] = set()

    for record in records:
        value = str(record.get(key, "")).strip()
        if not value:
            continue
        if value in seen_values:
            duplicates.add(value)
        seen_values.add(value)

    return sorted(duplicates)
