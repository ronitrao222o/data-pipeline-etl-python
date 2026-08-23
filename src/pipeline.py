from __future__ import annotations

import argparse
import json
import logging
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

try:
    from .configuration import load_config
    from .extract import extract_data
    from .load import load_data
    from .models import PipelineRunSummary
    from .quality import DataQualityError, evaluate_data_quality
    from .transform import transform_data
except ImportError:  # pragma: no cover - fallback for direct script execution
    from configuration import load_config
    from extract import extract_data
    from load import load_data
    from models import PipelineRunSummary
    from quality import DataQualityError, evaluate_data_quality
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


def build_run_summary(
    *,
    status: str,
    started_at: datetime,
    completed_at: datetime,
    config,
    transformation_result,
    loaded_count: int,
    quality_summary,
) -> PipelineRunSummary:
    return PipelineRunSummary(
        status=status,
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
        quality_summary=quality_summary,
    )


def run_pipeline(
    config_path: str = "config.yaml",
    fail_on_quality_gate: bool = False,
    report_output_path: str | None = None,
    log_level: str | None = None,
) -> PipelineRunSummary:
    config = load_config(config_path)
    if report_output_path:
        config = replace(config, report_output_path=Path(report_output_path).resolve())
    if log_level:
        config = replace(config, log_level=log_level.upper())

    configure_logging(config.log_level)

    started_at = datetime.now(timezone.utc)
    logging.info("ETL pipeline started")

    logging.info("Starting extract step")
    raw_data = extract_data(config.raw_data_path)
    logging.info("Extract step completed")

    logging.info("Starting transform step")
    transformation_result = transform_data(raw_data)
    logging.info("Transform step completed")

    quality_summary = evaluate_data_quality(
        transformation_result,
        config.quality_thresholds,
    )
    logging.info(
        "Quality evaluation completed with status=%s and rejection_rate=%s",
        quality_summary.passed,
        quality_summary.rejection_rate,
    )

    if fail_on_quality_gate and not quality_summary.passed:
        completed_at = datetime.now(timezone.utc)
        summary = build_run_summary(
            status="quality_gate_failed",
            started_at=started_at,
            completed_at=completed_at,
            config=config,
            transformation_result=transformation_result,
            loaded_count=0,
            quality_summary=quality_summary,
        )
        write_run_report(summary)
        logging.error("Data quality gate failed. Load step skipped.")
        raise DataQualityError(summary)

    logging.info("Starting load step")
    loaded_count = load_data(
        transformation_result.valid_records,
        db_path=config.database_path,
        schema_path=config.schema_path,
    )
    logging.info("Load step completed")

    completed_at = datetime.now(timezone.utc)
    status = "success" if quality_summary.passed else "completed_with_quality_warnings"
    summary = build_run_summary(
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        config=config,
        transformation_result=transformation_result,
        loaded_count=loaded_count,
        quality_summary=quality_summary,
    )
    write_run_report(summary)

    logging.info(
        "ETL pipeline executed with %s loaded rows and %s rejected rows",
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
    parser.add_argument(
        "--fail-on-quality-gate",
        action="store_true",
        help="Return a non-zero exit code when data quality checks fail",
    )
    parser.add_argument(
        "--report-path",
        help="Override the JSON report output path for this run",
    )
    parser.add_argument(
        "--log-level",
        help="Override the configured log level for this run",
    )
    args = parser.parse_args()

    try:
        summary = run_pipeline(
            config_path=args.config,
            fail_on_quality_gate=args.fail_on_quality_gate,
            report_output_path=args.report_path,
            log_level=args.log_level,
        )
    except DataQualityError as error:
        print(json.dumps(error.summary.to_dict(), indent=2))
        return 1

    print(json.dumps(summary.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
