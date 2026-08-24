from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from .models import AnalyticsDimensionMetric, SalesAnalyticsSummary
except ImportError:  # pragma: no cover - fallback for direct script execution
    from models import AnalyticsDimensionMetric, SalesAnalyticsSummary


def _rank_metrics(
    grouped_values: dict[str, dict[str, float | int]],
    top_n: int,
) -> list[AnalyticsDimensionMetric]:
    metrics = [
        AnalyticsDimensionMetric(
            name=name,
            order_count=int(values["order_count"]),
            quantity_sold=int(values["quantity_sold"]),
            revenue=round(float(values["revenue"]), 2),
        )
        for name, values in grouped_values.items()
    ]
    return sorted(metrics, key=lambda metric: metric.revenue, reverse=True)[:top_n]


def _daily_metrics(
    grouped_values: dict[str, dict[str, float | int]],
) -> list[AnalyticsDimensionMetric]:
    return [
        AnalyticsDimensionMetric(
            name=name,
            order_count=int(values["order_count"]),
            quantity_sold=int(values["quantity_sold"]),
            revenue=round(float(values["revenue"]), 2),
        )
        for name, values in sorted(grouped_values.items())
    ]


def build_sales_analytics(
    records: list[dict[str, Any]],
    top_n: int = 5,
) -> SalesAnalyticsSummary:
    revenue_by_product: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"order_count": 0, "quantity_sold": 0, "revenue": 0.0}
    )
    revenue_by_customer: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"order_count": 0, "quantity_sold": 0, "revenue": 0.0}
    )
    revenue_by_date: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"order_count": 0, "quantity_sold": 0, "revenue": 0.0}
    )

    total_quantity = 0
    total_revenue = 0.0

    for record in records:
        quantity = int(record["quantity"])
        revenue = float(record["total_amount"])
        order_date = record["order_date"].isoformat()

        total_quantity += quantity
        total_revenue += revenue

        for group_key, group_name in (
            ("product", str(record["product"])),
            ("customer_id", str(record["customer_id"])),
        ):
            grouped = revenue_by_product if group_key == "product" else revenue_by_customer
            grouped[group_name]["order_count"] += 1
            grouped[group_name]["quantity_sold"] += quantity
            grouped[group_name]["revenue"] += revenue

        revenue_by_date[order_date]["order_count"] += 1
        revenue_by_date[order_date]["quantity_sold"] += quantity
        revenue_by_date[order_date]["revenue"] += revenue

    order_count = len(records)
    return SalesAnalyticsSummary(
        order_count=order_count,
        total_quantity=total_quantity,
        total_revenue=round(total_revenue, 2),
        average_order_value=round(total_revenue / order_count, 2) if order_count else 0.0,
        top_products=_rank_metrics(revenue_by_product, top_n),
        top_customers=_rank_metrics(revenue_by_customer, top_n),
        daily_revenue=_daily_metrics(revenue_by_date),
    )


def write_analytics_report(
    analytics_summary: SalesAnalyticsSummary,
    output_path: str | Path,
) -> None:
    report_path = Path(output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        analytics_summary.to_json(),
        encoding="utf-8",
    )
