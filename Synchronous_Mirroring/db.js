const { Pool } = require('pg');

const mainDB = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'ecommerce',
    password: '26012004',
    port: 5555
});

const mirrorDB = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'ecommerce_mirror',
    password: '26012004',
    port: 5432
});

async function query(text, params) {
    let result;
    
    try {
        result = await mainDB.query(text, params);
        await mirrorDB.query(text, params);
    } catch (mainError) {
        console.error('Main DB error:', mainError);
        try {
            result = await mirrorDB.query(text, params);
        } catch (mirrorError) {
            throw new Error('Both databases failed');
        }
    }
    
    return result;
}

module.exports = { query };