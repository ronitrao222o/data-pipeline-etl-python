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

            blank_columns = [
                str(position)
                for position, name in enumerate(reader.fieldnames, start=1)
                if not name.strip()
            ]
            if blank_columns:
                raise ValueError(
                    f"Input file {path} contains blank CSV headers at columns: "
                    f"{', '.join(blank_columns)}"
                )

            duplicate_headers = sorted(
                name for name, count in Counter(reader.fieldnames).items() if count > 1
            )
            if duplicate_headers:
                raise ValueError(
                    f"Input file {path} contains duplicate CSV headers: "
                    f"{', '.join(duplicate_headers)}"
                )

            data = []
            for record in reader:
                if None in record:
                    raise ValueError(
                        f"Input file {path} contains extra CSV values "
                        f"at line {reader.line_num}: expected {len(reader.fieldnames)} columns, "
                        f"got {len(reader.fieldnames) + len(record[None])}"
                    )
                data.append(record)

            logging.info("Successfully extracted %s rows from %s", len(data), path)
            return data

    except FileNotFoundError:
        logging.error("Input file not found: %s", path)
        raise
    except Exception as error:
        logging.error("Error while reading file %s: %s", path, error)
        raise
