const express = require('express');
const http = require('http');
const app = express();
const PORT = 3000;

app.use(express.json());

const servers = [
    { url: 'localhost:3001', isAlive: true },
    { url: 'localhost:3002', isAlive: true }
];

let currentServerIndex = 0;

function checkServerHealth(serverUrl) {
    return new Promise((resolve) => {
        const [host, port] = serverUrl.split(':');
        
        // Créer la requête
        const req = http.request({
            hostname: host,
            port: port,
            path: '/products',
            method: 'GET',
            timeout: 2000
        }, (res) => {
            let data = '';
            res.on('data', chunk => { data += chunk; });
            res.on('end', () => {
                resolve(true);
            });
        });

        req.on('error', () => {
            console.log(`Error checking ${serverUrl}`);
            resolve(false);
        });

        req.on('timeout', () => {
            console.log(`Timeout checking ${serverUrl}`);
            req.destroy();
            resolve(false);
        });

        req.end();
    });
}

async function updateServerStatus() {
    console.log('Checking servers health...');
    for (let i = 0; i < servers.length; i++) {
        servers[i].isAlive = await checkServerHealth(servers[i].url);
        console.log(`Server ${servers[i].url} is ${servers[i].isAlive ? 'alive' : 'down'}`);
    }

    // Update current server if needed
    if (!servers[currentServerIndex].isAlive) {
        const aliveServer = servers.findIndex(s => s.isAlive);
        if (aliveServer !== -1) {
            currentServerIndex = aliveServer;
            console.log(`Switched to server ${servers[currentServerIndex].url}`);
        }
    }
}

// Check server health every 5 seconds
setInterval(updateServerStatus, 5000);

app.get('/getServer', (req, res) => {
    const activeServer = servers.find(s => s.isAlive);
    if (activeServer) {
        res.json({
            code: 200,
            server: activeServer.url
        });
    } else {
        res.status(503).json({
            code: 503,
            message: "No available servers"
        });
    }
});

app.get('/status', (req, res) => {
    res.json({
        servers: servers.map(s => ({
            url: s.url,
            status: s.isAlive ? 'alive' : 'down'
        })),
        currentServer: servers[currentServerIndex].url
    });
});

app.listen(PORT, () => {
    console.log(`DNS Registry running on port ${PORT}`);
    updateServerStatus();
});