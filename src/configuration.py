from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

try:
    from .models import DataQualityThresholds, PipelineConfig, RuntimeConfig
except ImportError:  # pragma: no cover - fallback for direct script execution
    from models import DataQualityThresholds, PipelineConfig, RuntimeConfig


DEFAULT_CONFIG = {
    "raw_data_path": "data/raw_sales_data.csv",
    "data_contract_path": "contracts/sales_orders_contract.yaml",
    "database_path": "artifacts/sales.db",
    "schema_path": "schema.sql",
    "report_output_path": "artifacts/pipeline_run_report.json",
    "analytics_output_path": "artifacts/sales_analytics_report.json",
    "log_level": "INFO",
    "analytics_top_n": 5,
    "quality_thresholds": {
        "min_valid_records": 3,
        "max_rejection_rate": 0.2,
        "max_duplicate_records": 0,
    },
    "runtime": {
        "environment": "dev",
        "owner": "analytics-engineering",
        "default_trigger_mode": "manual",
        "schedule_name": "adhoc",
        "schedule_cron": None,
    },
    "environments": {},
}

ENVIRONMENT_OVERRIDE_FIELDS = {
    "raw_data_path": "ETL_RAW_DATA_PATH",
    "data_contract_path": "ETL_DATA_CONTRACT_PATH",
    "database_path": "ETL_DATABASE_PATH",
    "schema_path": "ETL_SCHEMA_PATH",
    "report_output_path": "ETL_REPORT_OUTPUT_PATH",
    "analytics_output_path": "ETL_ANALYTICS_OUTPUT_PATH",
    "log_level": "ETL_LOG_LEVEL",
}

RUNTIME_ENVIRONMENT_FIELDS = {
    "environment": "ETL_ENVIRONMENT",
    "owner": "ETL_OWNER",
    "default_trigger_mode": "ETL_DEFAULT_TRIGGER_MODE",
    "schedule_name": "ETL_SCHEDULE_NAME",
    "schedule_cron": "ETL_SCHEDULE_CRON",
}

QUALITY_ENVIRONMENT_FIELDS = {
    "min_valid_records": "ETL_MIN_VALID_RECORDS",
    "max_rejection_rate": "ETL_MAX_REJECTION_RATE",
    "max_duplicate_records": "ETL_MAX_DUPLICATE_RECORDS",
}


def _resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _merge_nested_config(base: dict[str, Any], override: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def _apply_environment_overrides(config: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    merged = dict(config)

    for field, variable_name in ENVIRONMENT_OVERRIDE_FIELDS.items():
        value = env.get(variable_name)
        if value:
            merged[field] = value

    runtime = {**merged.get("runtime", {})}
    for field, variable_name in RUNTIME_ENVIRONMENT_FIELDS.items():
        if variable_name in env:
            runtime[field] = env[variable_name]
    merged["runtime"] = runtime

    quality_thresholds = {**merged.get("quality_thresholds", {})}
    for field, variable_name in QUALITY_ENVIRONMENT_FIELDS.items():
        if variable_name in env:
            quality_thresholds[field] = env[variable_name]
    merged["quality_thresholds"] = quality_thresholds

    return merged


def load_config(
    path: str = "config.yaml",
    environment: str | None = None,
    env: dict[str, str] | None = None,
) -> PipelineConfig:
    config_path = Path(path).resolve()
    env = env or dict(os.environ)

    with config_path.open("r", encoding="utf-8") as file:
        raw_config: dict[str, Any] = yaml.safe_load(file) or {}

    requested_environment = environment or env.get("ETL_ENVIRONMENT")
    base_config = _merge_nested_config(DEFAULT_CONFIG, raw_config)
    active_environment = requested_environment or base_config["runtime"]["environment"]
    environment_overrides = (raw_config.get("environments") or {}).get(active_environment, {})
    merged_config = _merge_nested_config(base_config, environment_overrides)
    merged_config = _apply_environment_overrides(merged_config, env)
    base_dir = config_path.parent
    quality_thresholds = {
        **DEFAULT_CONFIG["quality_thresholds"],
        **(merged_config.get("quality_thresholds") or {}),
    }
    runtime_config = {
        **DEFAULT_CONFIG["runtime"],
        **(merged_config.get("runtime") or {}),
    }

    return PipelineConfig(
        raw_data_path=_resolve_path(base_dir, str(merged_config["raw_data_path"])),
        data_contract_path=_resolve_path(base_dir, str(merged_config["data_contract_path"])),
        database_path=_resolve_path(base_dir, str(merged_config["database_path"])),
        schema_path=_resolve_path(base_dir, str(merged_config["schema_path"])),
        report_output_path=_resolve_path(base_dir, str(merged_config["report_output_path"])),
        analytics_output_path=_resolve_path(base_dir, str(merged_config["analytics_output_path"])),
        log_level=str(merged_config["log_level"]).upper(),
        analytics_top_n=int(merged_config["analytics_top_n"]),
        quality_thresholds=DataQualityThresholds(
            min_valid_records=int(quality_thresholds["min_valid_records"]),
            max_rejection_rate=float(quality_thresholds["max_rejection_rate"]),
            max_duplicate_records=int(quality_thresholds["max_duplicate_records"]),
        ),
        runtime=RuntimeConfig(
            environment=str(runtime_config["environment"]),
            owner=str(runtime_config["owner"]),
            default_trigger_mode=str(runtime_config["default_trigger_mode"]),
            schedule_name=str(runtime_config["schedule_name"]),
            schedule_cron=(
                str(runtime_config["schedule_cron"])
                if runtime_config.get("schedule_cron")
                else None
            ),
        ),
    )
