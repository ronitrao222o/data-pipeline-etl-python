CREATE TABLE IF NOT EXISTS sales (
    order_id INTEGER PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    product TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price REAL NOT NULL CHECK (price >= 0),
    total_amount REAL NOT NULL CHECK (total_amount >= 0)
);

CREATE INDEX IF NOT EXISTS idx_sales_order_date ON sales(order_date);
CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales(customer_id);
