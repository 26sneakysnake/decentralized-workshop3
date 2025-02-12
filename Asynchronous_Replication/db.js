// db.js
const { Pool } = require('pg');

const mainDB = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'ecommerce',
    password: '26012004',
    port: 5555
});

const replicaDB = new Pool({
    user: 'postgres',
    host: 'localhost',
    database: 'ecommerce_mirror',
    password: '26012004',
    port: 5432
});

let pendingChanges = [];

async function writeToMain(query, params) {
    const result = await mainDB.query(query, params);
    pendingChanges.push({ query, params, timestamp: new Date() });
    return result;
}

async function syncToReplica() {
    if (pendingChanges.length === 0) return;

    console.log(`Syncing ${pendingChanges.length} changes to replica...`);
    
    try {
        const client = await replicaDB.connect();
        await client.query('BEGIN');

        for (const change of pendingChanges) {
            await client.query(change.query, change.params);
        }

        await client.query('COMMIT');
        client.release();

        console.log('Sync successful, clearing pending changes');
        pendingChanges = [];
    } catch (error) {
        console.error('Sync failed:', error);
    }
}

// Sync every 5 seconds
setInterval(syncToReplica, 5000);

async function read(query, params) {
    try {
        return await mainDB.query(query, params);
    } catch (error) {
        console.log('Main DB error, falling back to replica');
        return await replicaDB.query(query, params);
    }
}

module.exports = { writeToMain, read };