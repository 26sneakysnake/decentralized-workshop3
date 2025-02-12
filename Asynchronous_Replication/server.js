// server.js
const express = require('express');
const cors = require('cors');
const { writeToMain, read } = require('./db');

const app = express();
app.use(cors());
app.use(express.json());

app.get('/products', async (req, res) => {
    try {
        const { category, inStock } = req.query;
        let queryText = 'SELECT * FROM products WHERE 1=1';
        const params = [];

        if (category) {
            params.push(category);
            queryText += ` AND category = $${params.length}`;
        }
        if (inStock !== undefined) {
            params.push(inStock === 'true');
            queryText += ` AND in_stock = $${params.length}`;
        }

        const { rows } = await read(queryText, params);
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.post('/products', async (req, res) => {
    try {
        const { name, description, price, category, in_stock } = req.body;
        const { rows } = await writeToMain(
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
        const { rows } = await writeToMain(
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
        await writeToMain('DELETE FROM products WHERE id = $1', [req.params.id]);
        res.json({ message: 'Product deleted' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

const PORT = 3001;
app.listen(PORT, () => {
    console.log(`Asynchronous replication server running on port ${PORT}`);
});