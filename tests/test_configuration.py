from pathlib import Path

import pytest

from src.configuration import load_config


@pytest.mark.parametrize("contents", ["[]", "[dev, prod]", "false", "0", "settings"])
def test_load_config_rejects_non_mapping_yaml(tmp_path, contents):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a YAML mapping") as error:
        load_config(str(config_path), env={})

    assert str(config_path) in str(error.value)


@pytest.mark.parametrize("contents", ["", "# No overrides\n", "null", "{}"])
def test_load_config_empty_yaml_uses_defaults(tmp_path, contents):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(contents, encoding="utf-8")

    config = load_config(str(config_path), env={})

    assert config.database_path == (tmp_path / "artifacts/sales.db").resolve()
    assert config.runtime.environment == "dev"
    assert config.quality_thresholds.min_valid_records == 3
    assert config.quality_thresholds.max_rejection_rate == 0.2
    assert config.quality_thresholds.max_duplicate_records == 0
    assert config.analytics_top_n == 5


@pytest.mark.parametrize(
    ("environment", "env"),
    [("prod", {}), ("prod", {"ETL_ENVIRONMENT": "staging"}), (None, {"ETL_ENVIRONMENT": "prod"})],
)
def test_load_config_reports_selected_environment(tmp_path, environment, env):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "runtime:\n"
        "  environment: dev\n"
        "environments:\n"
        "  prod:\n"
        "    database_path: artifacts/prod.db\n"
        "  staging:\n"
        "    database_path: artifacts/staging.db\n",
        encoding="utf-8",
    )

    config = load_config(str(config_path), environment=environment, env=env)

    assert config.database_path == (tmp_path / "artifacts/prod.db").resolve()
    assert config.runtime.environment == "prod"


def test_load_config_empty_env_ignores_process_overrides(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("database_path: artifacts/local.db\n", encoding="utf-8")
    monkeypatch.setenv("ETL_DATABASE_PATH", "artifacts/process.db")
    monkeypatch.setenv("ETL_ENVIRONMENT", "prod")
    monkeypatch.setenv("ETL_MAX_REJECTION_RATE", "0.9")

    config = load_config(str(config_path), env={})

    assert config.database_path == (tmp_path / "artifacts/local.db").resolve()
    assert config.runtime.environment == "dev"
    assert config.quality_thresholds.max_rejection_rate == 0.2


def test_load_config_default_env_reads_process_overrides(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("database_path: artifacts/local.db\n", encoding="utf-8")
    monkeypatch.setenv("ETL_DATABASE_PATH", "artifacts/process.db")
    monkeypatch.setenv("ETL_ENVIRONMENT", "prod")
    monkeypatch.setenv("ETL_MAX_REJECTION_RATE", "0.9")

    for kwargs in ({}, {"env": None}):
        config = load_config(str(config_path), **kwargs)

        assert config.database_path == (tmp_path / "artifacts/process.db").resolve()
        assert config.runtime.environment == "prod"
        assert config.quality_thresholds.max_rejection_rate == 0.9


def test_load_config_applies_environment_profile(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "raw_data_path: data/source.csv",
                "data_contract_path: contracts/sales_contract.yaml",
                "database_path: artifacts/default.db",
                "schema_path: schema.sql",
                "report_output_path: artifacts/default-report.json",
                "analytics_output_path: artifacts/default-analytics.json",
                "profile_output_path: artifacts/default-profile.json",
                "monitoring_output_path: artifacts/default-monitoring.json",
                "warehouse_output_path: artifacts/default-warehouse",
                "analytics_top_n: 3",
                "runtime:",
                "  environment: dev",
                "  owner: data-team",
                "  default_trigger_mode: manual",
                "  schedule_name: adhoc",
                "environments:",
                "  prod:",
                "    data_contract_path: contracts/prod_sales_contract.yaml",
                "    database_path: artifacts/prod.db",
                "    report_output_path: artifacts/prod-report.json",
                "    analytics_output_path: artifacts/prod-analytics.json",
                "    profile_output_path: artifacts/prod-profile.json",
                "    monitoring_output_path: artifacts/prod-monitoring.json",
                "    warehouse_output_path: artifacts/prod-warehouse",
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

    assert config.data_contract_path == (tmp_path / "contracts/prod_sales_contract.yaml").resolve()
    assert config.database_path == (tmp_path / "artifacts/prod.db").resolve()
    assert config.report_output_path == (tmp_path / "artifacts/prod-report.json").resolve()
    assert config.analytics_output_path == (tmp_path / "artifacts/prod-analytics.json").resolve()
    assert config.profile_output_path == (tmp_path / "artifacts/prod-profile.json").resolve()
    assert config.monitoring_output_path == (
        tmp_path / "artifacts/prod-monitoring.json"
    ).resolve()
    assert config.warehouse_output_path == (tmp_path / "artifacts/prod-warehouse").resolve()
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
                "data_contract_path: contracts/sales_contract.yaml",
                "database_path: artifacts/default.db",
                f"schema_path: {schema_path}",
                "report_output_path: artifacts/default-report.json",
                "analytics_output_path: artifacts/default-analytics.json",
                "profile_output_path: artifacts/default-profile.json",
                "monitoring_output_path: artifacts/default-monitoring.json",
                "warehouse_output_path: artifacts/default-warehouse",
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
            "ETL_DATA_CONTRACT_PATH": "contracts/override_contract.yaml",
            "ETL_DATABASE_PATH": "artifacts/override.db",
            "ETL_ANALYTICS_OUTPUT_PATH": "artifacts/override-analytics.json",
            "ETL_PROFILE_OUTPUT_PATH": "artifacts/override-profile.json",
            "ETL_MONITORING_OUTPUT_PATH": "artifacts/override-monitoring.json",
            "ETL_WAREHOUSE_OUTPUT_PATH": "artifacts/override-warehouse",
            "ETL_OWNER": "platform-team",
            "ETL_SCHEDULE_NAME": "hourly-validation",
            "ETL_MAX_REJECTION_RATE": "0.05",
        },
    )

    assert config.data_contract_path == (tmp_path / "contracts/override_contract.yaml").resolve()
    assert config.database_path == (tmp_path / "artifacts/override.db").resolve()
    expected_analytics_path = (tmp_path / "artifacts/override-analytics.json").resolve()
    assert config.analytics_output_path == expected_analytics_path
    assert config.profile_output_path == (tmp_path / "artifacts/override-profile.json").resolve()
    assert config.monitoring_output_path == (
        tmp_path / "artifacts/override-monitoring.json"
    ).resolve()
    assert config.warehouse_output_path == (tmp_path / "artifacts/override-warehouse").resolve()
    assert config.runtime.environment == "staging"
    assert config.runtime.owner == "platform-team"
    assert config.runtime.schedule_name == "hourly-validation"
    assert config.quality_thresholds.max_rejection_rate == 0.05
