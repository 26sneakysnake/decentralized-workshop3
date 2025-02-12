CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100),
    in_stock BOOLEAN DEFAULT true
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price_at_time DECIMAL(10,2) NOT NULL
);

CREATE TABLE cart (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL
);