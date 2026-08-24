from pathlib import Path

from src.configuration import load_config


def test_load_config_applies_environment_profile(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "raw_data_path: data/source.csv",
                "database_path: artifacts/default.db",
                "schema_path: schema.sql",
                "report_output_path: artifacts/default-report.json",
                "analytics_output_path: artifacts/default-analytics.json",
                "analytics_top_n: 3",
                "runtime:",
                "  environment: dev",
                "  owner: data-team",
                "  default_trigger_mode: manual",
                "  schedule_name: adhoc",
                "environments:",
                "  prod:",
                "    database_path: artifacts/prod.db",
                "    report_output_path: artifacts/prod-report.json",
                "    analytics_output_path: artifacts/prod-analytics.json",
                "    analytics_top_n: 7",
                "    log_level: WARNING",
                "    runtime:",
                "      environment: prod",
                "      schedule_name: daily-sales-refresh",
                "      schedule_cron: '0 2 * * *'",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(str(config_path), environment="prod")

    assert config.database_path == (tmp_path / "artifacts/prod.db").resolve()
    assert config.report_output_path == (tmp_path / "artifacts/prod-report.json").resolve()
    assert config.analytics_output_path == (tmp_path / "artifacts/prod-analytics.json").resolve()
    assert config.analytics_top_n == 7
    assert config.log_level == "WARNING"
    assert config.runtime.environment == "prod"
    assert config.runtime.schedule_name == "daily-sales-refresh"
    assert config.runtime.schedule_cron == "0 2 * * *"


def test_load_config_applies_env_var_overrides(tmp_path):
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "raw_data_path: data/source.csv",
                "database_path: artifacts/default.db",
                f"schema_path: {schema_path}",
                "report_output_path: artifacts/default-report.json",
                "analytics_output_path: artifacts/default-analytics.json",
                "runtime:",
                "  environment: dev",
                "  owner: data-team",
                "  default_trigger_mode: manual",
                "  schedule_name: adhoc",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(
        str(config_path),
        env={
            "ETL_ENVIRONMENT": "staging",
            "ETL_DATABASE_PATH": "artifacts/override.db",
            "ETL_ANALYTICS_OUTPUT_PATH": "artifacts/override-analytics.json",
            "ETL_OWNER": "platform-team",
            "ETL_SCHEDULE_NAME": "hourly-validation",
            "ETL_MAX_REJECTION_RATE": "0.05",
        },
    )

    assert config.database_path == (tmp_path / "artifacts/override.db").resolve()
    assert config.analytics_output_path == (tmp_path / "artifacts/override-analytics.json").resolve()
    assert config.runtime.environment == "staging"
    assert config.runtime.owner == "platform-team"
    assert config.runtime.schedule_name == "hourly-validation"
    assert config.quality_thresholds.max_rejection_rate == 0.05
