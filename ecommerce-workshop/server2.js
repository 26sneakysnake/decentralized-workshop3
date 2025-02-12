const express = require('express');
const cors = require('cors');
const pool = require('./db');

const app = express();
const PORT = 3002;

app.use(cors());
app.use(express.json());

app.get('/products', async (req, res) => {
    try {
        const { category, inStock } = req.query;
        let query = 'SELECT * FROM products WHERE 1=1';
        const params = [];

        if (category) {
            params.push(category);
            query += ` AND category = $${params.length}`;
        }
        if (inStock !== undefined) {
            params.push(inStock === 'true');
            query += ` AND in_stock = $${params.length}`;
        }

        const { rows } = await pool.query(query, params);
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/products/:id', async (req, res) => {
    try {
        const { rows } = await pool.query('SELECT * FROM products WHERE id = $1', [req.params.id]);
        if (rows.length === 0) return res.status(404).json({ message: 'Product not found' });
        res.json(rows[0]);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.post('/products', async (req, res) => {
    try {
        const { name, description, price, category, in_stock } = req.body;
        const { rows } = await pool.query(
            'INSERT INTO products (name, description, price, category, in_stock) VALUES ($1, $2, $3, $4, $5) RETURNING *',
            [name, description, price, category, in_stock]
        );
        res.json(rows[0]);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.put('/products/:id', async (req, res) => {
    try {
        const { name, description, price, category, in_stock } = req.body;
        const { rows } = await pool.query(
            'UPDATE products SET name = $1, description = $2, price = $3, category = $4, in_stock = $5 WHERE id = $6 RETURNING *',
            [name, description, price, category, in_stock, req.params.id]
        );
        res.json(rows[0]);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.delete('/products/:id', async (req, res) => {
    try {
        await pool.query('DELETE FROM products WHERE id = $1', [req.params.id]);
        res.json({ message: 'Product deleted' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Orders Routes
app.post('/orders', async (req, res) => {
    const client = await pool.connect();
    try {
        await client.query('BEGIN');
        const { user_id, products } = req.body;
        let total_price = 0;

        for (let item of products) {
            const { rows } = await client.query('SELECT price FROM products WHERE id = $1', [item.product_id]);
            total_price += rows[0].price * item.quantity;
        }

        const orderResult = await client.query(
            'INSERT INTO orders (user_id, total_price) VALUES ($1, $2) RETURNING id',
            [user_id, total_price]
        );

        const order_id = orderResult.rows[0].id;

        for (let item of products) {
            await client.query(
                'INSERT INTO order_items (order_id, product_id, quantity, price_at_time) VALUES ($1, $2, $3, $4)',
                [order_id, item.product_id, item.quantity, item.price]
            );
        }

        await client.query('COMMIT');
        res.json({ order_id, total_price });
    } catch (err) {
        await client.query('ROLLBACK');
        res.status(500).json({ error: err.message });
    } finally {
        client.release();
    }
});

app.get('/orders/:userId', async (req, res) => {
    try {
        const { rows } = await pool.query(
            'SELECT o.*, oi.product_id, oi.quantity, oi.price_at_time FROM orders o LEFT JOIN order_items oi ON o.id = oi.order_id WHERE o.user_id = $1',
            [req.params.userId]
        );
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Cart Routes
app.post('/cart/:userId', async (req, res) => {
    try {
        const { userId } = req.params;
        const { product_id, quantity } = req.body;

        const existingItem = await pool.query(
            'SELECT * FROM cart WHERE user_id = $1 AND product_id = $2',
            [userId, product_id]
        );

        if (existingItem.rows.length > 0) {
            const { rows } = await pool.query(
                'UPDATE cart SET quantity = $1 WHERE user_id = $2 AND product_id = $3 RETURNING *',
                [quantity, userId, product_id]
            );
            res.json(rows[0]);
        } else {
            const { rows } = await pool.query(
                'INSERT INTO cart (user_id, product_id, quantity) VALUES ($1, $2, $3) RETURNING *',
                [userId, product_id, quantity]
            );
            res.json(rows[0]);
        }
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/cart/:userId', async (req, res) => {
    try {
        const { rows } = await pool.query(
            'SELECT c.*, p.name, p.price FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = $1',
            [req.params.userId]
        );
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.delete('/cart/:userId/item/:productId', async (req, res) => {
    try {
        await pool.query(
            'DELETE FROM cart WHERE user_id = $1 AND product_id = $2',
            [req.params.userId, req.params.productId]
        );
        res.json({ message: 'Item removed from cart' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.listen(PORT, () => {
    console.log(`E-commerce server running on port ${PORT}`);
});