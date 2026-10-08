from datetime import date

import pytest

from src.analytics import build_sales_analytics


@pytest.mark.parametrize("top_n", [1, 2, 3])
def test_revenue_ties_rank_by_name_regardless_of_input_order(top_n):
    records = [
        {
            "order_id": order_id,
            "customer_id": customer,
            "order_date": date(2024, 1, 1),
            "product": product,
            "quantity": 1,
            "price": revenue,
            "total_amount": revenue,
        }
        for order_id, customer, product, revenue in [
            (1, "C003", "Mouse", 100.0),
            (2, "C002", "Keyboard", 100.0),
            (3, "C001", "Adapter", 50.0),
        ]
    ]

    for ordered_records in (records, list(reversed(records))):
        summary = build_sales_analytics(ordered_records, top_n=top_n)

        assert [metric.name for metric in summary.top_products] == [
            "Keyboard", "Mouse", "Adapter"
        ][:top_n]
        assert [metric.name for metric in summary.top_customers] == [
            "C002", "C003", "C001"
        ][:top_n]


def test_build_sales_analytics_ranks_products_and_customers():
    records = [
        {
            "order_id": 1,
            "customer_id": "C001",
            "order_date": date(2024, 1, 1),
            "product": "Laptop",
            "quantity": 1,
            "price": 60000.0,
            "total_amount": 60000.0,
        },
        {
            "order_id": 2,
            "customer_id": "C002",
            "order_date": date(2024, 1, 1),
            "product": "Mouse",
            "quantity": 2,
            "price": 500.0,
            "total_amount": 1000.0,
        },
        {
            "order_id": 3,
            "customer_id": "C001",
            "order_date": date(2024, 1, 2),
            "product": "Laptop",
            "quantity": 1,
            "price": 65000.0,
            "total_amount": 65000.0,
        },
    ]

    summary = build_sales_analytics(records, top_n=1)

    assert summary.order_count == 3
    assert summary.total_quantity == 4
    assert summary.total_revenue == 126000.0
    assert summary.average_order_value == 42000.0
    assert summary.top_products[0].name == "Laptop"
    assert summary.top_products[0].revenue == 125000.0
    assert summary.top_customers[0].name == "C001"
    assert [metric.name for metric in summary.daily_revenue] == [
        "2024-01-01",
        "2024-01-02",
    ]
