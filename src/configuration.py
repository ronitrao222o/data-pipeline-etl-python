from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

try:
    from .models import DataQualityThresholds, PipelineConfig
except ImportError:  # pragma: no cover - fallback for direct script execution
    from models import DataQualityThresholds, PipelineConfig


DEFAULT_CONFIG = {
    "raw_data_path": "data/raw_sales_data.csv",
    "database_path": "artifacts/sales.db",
    "schema_path": "schema.sql",
    "report_output_path": "artifacts/pipeline_run_report.json",
    "log_level": "INFO",
    "quality_thresholds": {
        "min_valid_records": 3,
        "max_rejection_rate": 0.2,
        "max_duplicate_records": 0,
    },
}


def _resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def load_config(path: str = "config.yaml") -> PipelineConfig:
    config_path = Path(path).resolve()

    with config_path.open("r", encoding="utf-8") as file:
        raw_config: dict[str, Any] = yaml.safe_load(file) or {}

    merged_config = {**DEFAULT_CONFIG, **raw_config}
    base_dir = config_path.parent
    quality_thresholds = {
        **DEFAULT_CONFIG["quality_thresholds"],
        **(raw_config.get("quality_thresholds") or {}),
    }

    return PipelineConfig(
        raw_data_path=_resolve_path(base_dir, str(merged_config["raw_data_path"])),
        database_path=_resolve_path(base_dir, str(merged_config["database_path"])),
        schema_path=_resolve_path(base_dir, str(merged_config["schema_path"])),
        report_output_path=_resolve_path(base_dir, str(merged_config["report_output_path"])),
        log_level=str(merged_config["log_level"]).upper(),
        quality_thresholds=DataQualityThresholds(
            min_valid_records=int(quality_thresholds["min_valid_records"]),
            max_rejection_rate=float(quality_thresholds["max_rejection_rate"]),
            max_duplicate_records=int(quality_thresholds["max_duplicate_records"]),
        ),
    )
