import sqlite3

def load_data(data, db_path="sales.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(open("schema.sql").read())

    for row in data:
        cursor.execute("""
            INSERT OR REPLACE INTO sales 
            (order_id, customer_id, order_date, product, quantity, price, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row["order_id"],
            row["customer_id"],
            row["order_date"],
            row["product"],
            row["quantity"],
            row["price"],
            row["total_amount"]
        ))

    conn.commit()
    conn.close()
