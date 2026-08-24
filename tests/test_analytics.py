from datetime import date

from src.analytics import build_sales_analytics


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
