from __future__ import annotations

import csv
import logging
from collections import Counter
from pathlib import Path


def extract_data(file_path: str | Path) -> list[dict[str, str]]:
    path = Path(file_path)

    try:
        with path.open(mode="r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                raise ValueError(f"Input file {path} does not contain a CSV header row")

            duplicate_headers = sorted(
                name for name, count in Counter(reader.fieldnames).items() if count > 1
            )
            if duplicate_headers:
                raise ValueError(
                    f"Input file {path} contains duplicate CSV headers: "
                    f"{', '.join(duplicate_headers)}"
                )

            data = list(reader)
            logging.info("Successfully extracted %s rows from %s", len(data), path)
            return data

    except FileNotFoundError:
        logging.error("Input file not found: %s", path)
        raise
    except Exception as error:
        logging.error("Error while reading file %s: %s", path, error)
        raise
