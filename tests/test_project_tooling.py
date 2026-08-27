import tomllib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_project_has_container_and_command_tooling():
    assert (ROOT_DIR / "Dockerfile").exists()
    assert (ROOT_DIR / ".dockerignore").exists()
    assert (ROOT_DIR / "Makefile").exists()
    assert (ROOT_DIR / "contracts/sales_orders_contract.yaml").exists()
    assert (ROOT_DIR / "docs/data_contract.md").exists()
    assert (ROOT_DIR / "docs/lineage.md").exists()
    assert (ROOT_DIR / "docs/warehouse_exports.md").exists()

    dockerfile = (ROOT_DIR / "Dockerfile").read_text(encoding="utf-8")
    makefile = (ROOT_DIR / "Makefile").read_text(encoding="utf-8")

    assert '"src.pipeline"' in dockerfile
    assert "$(RUFF) check src tests" in makefile
    assert "pytest" in makefile


def test_pyproject_configures_pytest_and_ruff():
    pyproject = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]
    assert pyproject["tool"]["ruff"]["target-version"] == "py311"
