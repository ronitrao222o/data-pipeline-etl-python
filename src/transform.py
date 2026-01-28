from datetime import datetime

def transform_data(raw_data):
    transformed = []

    for row in raw_data:
        transformed.append({
            "order_id": int(row["order_id"]),
            "customer_id": row["customer_id"],
            "order_date": datetime.strptime(row["order_date"], "%Y-%m-%d").date(),
            "product": row["product"],
            "quantity": int(row["quantity"]),
            "price": float(row["price"]),
            "total_amount": int(row["quantity"]) * float(row["price"])
        })

    return transformed
