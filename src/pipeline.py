from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

try:
    from .configuration import load_config
    from .extract import extract_data
    from .load import load_data
    from .models import PipelineRunSummary
    from .transform import transform_data
except ImportError:  # pragma: no cover - fallback for direct script execution
    from configuration import load_config
    from extract import extract_data
    from load import load_data
    from models import PipelineRunSummary
    from transform import transform_data


LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=getattr(logging, level, logging.INFO), format=LOG_FORMAT)


def write_run_report(summary: PipelineRunSummary) -> None:
    report_path = Path(summary.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(summary.to_dict(), indent=2),
        encoding="utf-8",
    )


def run_pipeline(config_path: str = "config.yaml") -> PipelineRunSummary:
    config = load_config(config_path)
    configure_logging(config.log_level)

    started_at = datetime.now(timezone.utc)
    logging.info("ETL pipeline started")

    logging.info("Starting extract step")
    raw_data = extract_data(config.raw_data_path)
    logging.info("Extract step completed")

    logging.info("Starting transform step")
    transformation_result = transform_data(raw_data)
    logging.info("Transform step completed")

    logging.info("Starting load step")
    loaded_count = load_data(
        transformation_result.valid_records,
        db_path=config.database_path,
        schema_path=config.schema_path,
    )
    logging.info("Load step completed")

    completed_at = datetime.now(timezone.utc)
    summary = PipelineRunSummary(
        status="success",
        started_at=started_at,
        completed_at=completed_at,
        source_path=config.raw_data_path,
        database_path=config.database_path,
        report_path=config.report_output_path,
        extracted_count=transformation_result.extracted_count,
        valid_record_count=transformation_result.valid_record_count,
        loaded_count=loaded_count,
        rejected_record_count=transformation_result.rejected_record_count,
        duplicate_order_ids=transformation_result.duplicate_order_ids,
        total_revenue=transformation_result.total_revenue,
        rejected_records=transformation_result.rejected_records,
    )
    write_run_report(summary)

    logging.info(
        "ETL pipeline executed successfully with %s loaded rows and %s rejected rows",
        summary.loaded_count,
        summary.rejected_record_count,
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ETL pipeline")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to the pipeline configuration file",
    )
    args = parser.parse_args()

    summary = run_pipeline(config_path=args.config)
    print(json.dumps(summary.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
