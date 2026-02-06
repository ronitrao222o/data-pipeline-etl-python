# Data Pipeline & ETL System (Python)

## Overview
This project implements a modular ETL (Extract, Transform, Load) pipeline using Python and SQLite.
The pipeline ingests raw sales data, applies transformations, and loads the processed data into a
relational database for analytics and reporting.

## Architecture
- Extract: Reads raw CSV data
- Transform: Cleans data and computes derived metrics
- Load: Stores processed data into SQLite database
- Structured logging added to track execution of extract, transform, and load steps
- Input validation added during transformation to safely handle missing or malformed records
- Configuration-driven pipeline using external YAML config for input paths
- Graceful error handling added during data extraction to handle missing or unreadable input files with clear logging

## Configuration
The pipeline uses a YAML configuration file (`config.yaml`) to manage input paths and runtime settings.


## How to Run
```bash
pip install -r requirements.txt
python src/pipeline.py
