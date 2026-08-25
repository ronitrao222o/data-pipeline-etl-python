PYTHON ?= python3
VENV ?= .venv
IMAGE_NAME ?= data-pipeline-etl

VENV_PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff

.PHONY: setup test lint run dry-run clean docker-build docker-run

setup: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

test: setup
	$(PYTEST)

lint: setup
	$(RUFF) check src tests

run: setup
	$(VENV_PYTHON) -m src.pipeline --config config.yaml

dry-run: setup
	$(VENV_PYTHON) -m src.pipeline --config config.yaml --dry-run

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run: docker-build
	docker run --rm -v "$$(pwd)/artifacts:/app/artifacts" $(IMAGE_NAME)

clean:
	rm -rf .pytest_cache .ruff_cache artifacts
