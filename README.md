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


## How to Run
```bash
pip install -r requirements.txt
python src/pipeline.py
