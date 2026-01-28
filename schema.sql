CREATE TABLE IF NOT EXISTS sales (
    order_id INTEGER PRIMARY KEY,
    customer_id TEXT,
    order_date DATE,
    product TEXT,
    quantity INTEGER,
    price REAL,
    total_amount REAL
);
