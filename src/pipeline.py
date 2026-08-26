from __future__ import annotations

import argparse
import json
import logging
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

try:
    from .analytics import build_sales_analytics, write_analytics_report
    from .configuration import load_config
    from .contracts import load_data_contract, validate_raw_contract
    from .extract import extract_data
    from .load import load_data
    from .models import PipelineRunSummary, RuntimeSummary
    from .quality import DataQualityError, evaluate_data_quality
    from .transform import transform_data
except ImportError:  # pragma: no cover - fallback for direct script execution
    from analytics import build_sales_analytics, write_analytics_report
    from configuration import load_config
    from contracts import load_data_contract, validate_raw_contract
    from extract import extract_data
    from load import load_data
    from models import PipelineRunSummary, RuntimeSummary
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
    contract_summary,
    quality_summary,
    runtime_summary: RuntimeSummary,
    analytics_summary,
) -> PipelineRunSummary:
    return PipelineRunSummary(
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        source_path=config.raw_data_path,
        database_path=config.database_path,
        report_path=config.report_output_path,
        analytics_report_path=config.analytics_output_path,
        extracted_count=transformation_result.extracted_count,
        valid_record_count=transformation_result.valid_record_count,
        loaded_count=loaded_count,
        rejected_record_count=transformation_result.rejected_record_count,
        duplicate_order_ids=transformation_result.duplicate_order_ids,
        total_revenue=transformation_result.total_revenue,
        rejected_records=transformation_result.rejected_records,
        contract_summary=contract_summary,
        quality_summary=quality_summary,
        runtime_summary=runtime_summary,
        analytics_summary=analytics_summary,
    )


def build_runtime_summary(
    *,
    config,
    run_id: str,
    trigger_mode: str,
    dry_run: bool,
    load_step_skipped: bool,
) -> RuntimeSummary:
    return RuntimeSummary(
        run_id=run_id,
        environment=config.runtime.environment,
        owner=config.runtime.owner,
        trigger_mode=trigger_mode,
        schedule_name=config.runtime.schedule_name,
        schedule_cron=config.runtime.schedule_cron,
        dry_run=dry_run,
        load_step_skipped=load_step_skipped,
    )


def run_pipeline(
    config_path: str = "config.yaml",
    fail_on_quality_gate: bool = False,
    report_output_path: str | None = None,
    analytics_output_path: str | None = None,
    log_level: str | None = None,
    environment: str | None = None,
    run_id: str | None = None,
    trigger_mode: str | None = None,
    dry_run: bool = False,
) -> PipelineRunSummary:
    config = load_config(config_path, environment=environment)
    if report_output_path:
        config = replace(config, report_output_path=Path(report_output_path).resolve())
    if analytics_output_path:
        config = replace(config, analytics_output_path=Path(analytics_output_path).resolve())
    if log_level:
        config = replace(config, log_level=log_level.upper())

    configure_logging(config.log_level)

    started_at = datetime.now(UTC)
    resolved_run_id = run_id or started_at.strftime("etl-run-%Y%m%d%H%M%S")
    resolved_trigger_mode = trigger_mode or config.runtime.default_trigger_mode
    logging.info("ETL pipeline started")
    logging.info(
        "Runtime context run_id=%s environment=%s trigger_mode=%s dry_run=%s",
        resolved_run_id,
        config.runtime.environment,
        resolved_trigger_mode,
        dry_run,
    )

    logging.info("Starting extract step")
    raw_data = extract_data(config.raw_data_path)
    logging.info("Extract step completed")

    data_contract = load_data_contract(config.data_contract_path)
    contract_summary = validate_raw_contract(raw_data, data_contract)
    logging.info(
        "Contract validation completed with status=%s for dataset=%s",
        contract_summary.passed,
        contract_summary.dataset_name,
    )

    logging.info("Starting transform step")
    transformation_result = transform_data(raw_data)
    logging.info("Transform step completed")

    quality_summary = evaluate_data_quality(
        transformation_result,
        config.quality_thresholds,
    )
    analytics_summary = build_sales_analytics(
        transformation_result.valid_records,
        top_n=config.analytics_top_n,
    )
    logging.info(
        "Quality evaluation completed with status=%s and rejection_rate=%s",
        quality_summary.passed,
        quality_summary.rejection_rate,
    )
    logging.info(
        "Analytics summary built with %s orders and total_revenue=%s",
        analytics_summary.order_count,
        analytics_summary.total_revenue,
    )

    if fail_on_quality_gate and not quality_summary.passed:
        completed_at = datetime.now(UTC)
        runtime_summary = build_runtime_summary(
            config=config,
            run_id=resolved_run_id,
            trigger_mode=resolved_trigger_mode,
            dry_run=dry_run,
            load_step_skipped=True,
        )
        summary = build_run_summary(
            status="quality_gate_failed",
            started_at=started_at,
            completed_at=completed_at,
            config=config,
            transformation_result=transformation_result,
            loaded_count=0,
            contract_summary=contract_summary,
            quality_summary=quality_summary,
            runtime_summary=runtime_summary,
            analytics_summary=analytics_summary,
        )
        write_analytics_report(analytics_summary, config.analytics_output_path)
        write_run_report(summary)
        logging.error("Data quality gate failed. Load step skipped.")
        raise DataQualityError(summary)

    loaded_count = 0
    load_step_skipped = dry_run
    if dry_run:
        logging.info("Dry run enabled. Load step skipped.")
    else:
        logging.info("Starting load step")
        loaded_count = load_data(
            transformation_result.valid_records,
            db_path=config.database_path,
            schema_path=config.schema_path,
        )
        logging.info("Load step completed")

    completed_at = datetime.now(UTC)
    status = "dry_run_success" if dry_run and quality_summary.passed else (
        "dry_run_with_quality_warnings" if dry_run else (
            "success" if quality_summary.passed else "completed_with_quality_warnings"
        )
    )
    runtime_summary = build_runtime_summary(
        config=config,
        run_id=resolved_run_id,
        trigger_mode=resolved_trigger_mode,
        dry_run=dry_run,
        load_step_skipped=load_step_skipped,
    )
    summary = build_run_summary(
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        config=config,
        transformation_result=transformation_result,
        loaded_count=loaded_count,
        contract_summary=contract_summary,
        quality_summary=quality_summary,
        runtime_summary=runtime_summary,
        analytics_summary=analytics_summary,
    )
    write_analytics_report(analytics_summary, config.analytics_output_path)
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
        "--analytics-report-path",
        help="Override the sales analytics JSON output path for this run",
    )
    parser.add_argument(
        "--log-level",
        help="Override the configured log level for this run",
    )
    parser.add_argument(
        "--environment",
        help="Select a named environment profile from config.yaml",
    )
    parser.add_argument(
        "--run-id",
        help="Provide an external orchestration run identifier",
    )
    parser.add_argument(
        "--trigger-mode",
        choices=["manual", "scheduled", "backfill"],
        help="Describe how the pipeline was triggered",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute extract, transform, and quality checks without loading to the database",
    )
    args = parser.parse_args()

    try:
        summary = run_pipeline(
            config_path=args.config,
            fail_on_quality_gate=args.fail_on_quality_gate,
            report_output_path=args.report_path,
            analytics_output_path=args.analytics_report_path,
            log_level=args.log_level,
            environment=args.environment,
            run_id=args.run_id,
            trigger_mode=args.trigger_mode,
            dry_run=args.dry_run,
        )
    except DataQualityError as error:
        print(json.dumps(error.summary.to_dict(), indent=2))
        return 1

    print(json.dumps(summary.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
