from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def load_data(
    data: list[dict[str, Any]],
    db_path: str | Path = "sales.db",
    schema_path: str | Path = "schema.sql",
) -> int:
    database_path = Path(db_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    schema_file = Path(schema_path)

    inserted_count = 0

    with sqlite3.connect(database_path) as conn:
        cursor = conn.cursor()
        cursor.executescript(schema_file.read_text(encoding="utf-8"))

        for row in data:
            cursor.execute(
                """
                INSERT OR REPLACE INTO sales
                (order_id, customer_id, order_date, product, quantity, price, total_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["order_id"],
                    row["customer_id"],
                    row["order_date"].isoformat(),
                    row["product"],
                    row["quantity"],
                    row["price"],
                    row["total_amount"],
                ),
            )
            inserted_count += 1

    return inserted_count
