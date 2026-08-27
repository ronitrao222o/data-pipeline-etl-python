from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from .models import WarehouseExportPartition, WarehouseExportSummary
except ImportError:  # pragma: no cover - fallback for direct script execution
    from models import WarehouseExportPartition, WarehouseExportSummary


WAREHOUSE_COLUMNS = [
    "order_id",
    "customer_id",
    "order_date",
    "product",
    "quantity",
    "price",
    "total_amount",
]


def export_partitioned_sales(
    records: list[dict[str, Any]],
    output_path: str | Path,
    run_id: str,
    dry_run: bool = False,
) -> WarehouseExportSummary:
    base_path = Path(output_path)
    manifest_path = base_path / "_manifest.json"

    if dry_run:
        return WarehouseExportSummary(
            output_path=base_path,
            manifest_path=manifest_path,
            partition_column="order_month",
            partition_count=0,
            exported_record_count=0,
            skipped=True,
            partitions=[],
        )

    grouped_records = _group_by_order_month(records)
    partitions: list[WarehouseExportPartition] = []

    for order_month, partition_records in sorted(grouped_records.items()):
        partition_path = base_path / f"order_month={order_month}" / "part-000.csv"
        partition_path.parent.mkdir(parents=True, exist_ok=True)
        _write_partition(partition_path, partition_records)
        partitions.append(
            WarehouseExportPartition(
                partition_value=order_month,
                path=partition_path,
                record_count=len(partition_records),
            )
        )

    summary = WarehouseExportSummary(
        output_path=base_path,
        manifest_path=manifest_path,
        partition_column="order_month",
        partition_count=len(partitions),
        exported_record_count=sum(partition.record_count for partition in partitions),
        skipped=False,
        partitions=partitions,
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({"run_id": run_id, **summary.to_dict()}, indent=2),
        encoding="utf-8",
    )
    return summary


def _group_by_order_month(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped_records: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for record in records:
        order_month = record["order_date"].strftime("%Y-%m")
        grouped_records[order_month].append(record)

    return grouped_records


def _write_partition(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=WAREHOUSE_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "order_id": record["order_id"],
                    "customer_id": record["customer_id"],
                    "order_date": record["order_date"].isoformat(),
                    "product": record["product"],
                    "quantity": record["quantity"],
                    "price": record["price"],
                    "total_amount": record["total_amount"],
                }
            )
