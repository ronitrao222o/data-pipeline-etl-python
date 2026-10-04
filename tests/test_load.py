import sqlite3
from datetime import date
from pathlib import Path

import pytest

from src.load import load_data

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema.sql"


@pytest.mark.parametrize("fail_load", [False, True])
def test_load_closes_connection_and_preserves_transaction(tmp_path, monkeypatch, fail_load):
    database_path = tmp_path / "sales.db"
    connect = sqlite3.connect
    connections = []

    def track_connection(*args, **kwargs):
        connection = connect(*args, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(sqlite3, "connect", track_connection)
    row = {
        "order_id": 1,
        "customer_id": "C001",
        "order_date": date(2024, 1, 1),
        "product": "Keyboard",
        "quantity": 2,
        "price": 50.0,
        "total_amount": 100.0,
    }

    if fail_load:
        with pytest.raises(sqlite3.IntegrityError):
            load_data([row, {**row, "order_id": 2, "quantity": 0}], database_path, SCHEMA_PATH)
    else:
        assert load_data([row], database_path, SCHEMA_PATH) == 1

    assert len(connections) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        connections[0].execute("SELECT 1")

    verification_connection = connect(database_path)
    try:
        rows = verification_connection.execute("SELECT order_id FROM sales").fetchall()
        assert rows == ([] if fail_load else [(1,)])
    finally:
        verification_connection.close()
