/**
 * Diagnostic Service - Main Server
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const fs = require('fs');

const logger = require('./utils/logger');
const { initDatabase } = require('./database/init-db');
const HealthMonitor = require('./monitors/health-monitor');
const PerformanceMonitor = require('./monitors/performance-monitor');
const LogAggregator = require('./monitors/log-aggregator');
const AlertManager = require('./alerts/alert-manager');
const PrometheusExporter = require('./exporters/prometheus-exporter');
const apiRoutes = require('./api/routes');

// Load configuration
const configPath = path.join(__dirname, '../config/config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

// Initialize Express app
const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Middleware
app.use(cors());
app.use(express.json());

// Initialize database
try {
    initDatabase();
    logger.info('Database initialized');
} catch (error) {
    logger.error('Database initialization failed', { error: error.message });
}

// Initialize monitors
const healthMonitor = new HealthMonitor(config);
const performanceMonitor = new PerformanceMonitor(config);
const logAggregator = new LogAggregator(config);
const alertManager = new AlertManager();
const prometheusExporter = new PrometheusExporter(healthMonitor, performanceMonitor, alertManager);

// Store instances for access in routes
app.set('healthMonitor', healthMonitor);
app.set('performanceMonitor', performanceMonitor);
app.set('logAggregator', logAggregator);
app.set('alertManager', alertManager);

// API Routes
app.get('/', (req, res) => {
    res.json({
        name: config.service.name,
        version: config.service.version,
        status: 'running',
        endpoints: {
            health: '/api/health',
            metrics: '/api/metrics',
            logs: '/api/logs',
            alerts: '/api/alerts',
            summary: '/api/status/summary'
        }
    });
});

app.use('/api', apiRoutes);

// Prometheus metrics endpoint
app.get('/metrics', async (req, res) => {
    try {
        const metrics = await prometheusExporter.getMetrics();
        res.set('Content-Type', 'text/plain');
        res.send(metrics);
    } catch (error) {
        logger.error('Prometheus metrics error', { error: error.message });
        res.status(500).send('Error generating metrics');
    }
});

// WebSocket connection handling
const wsClients = new Set();

wss.on('connection', (ws) => {
    logger.info('WebSocket client connected', { total: wsClients.size + 1 });
    wsClients.add(ws);

    // Send initial data
    ws.send(JSON.stringify({
        type: 'connected',
        message: 'Connected to diagnostic service',
        timestamp: new Date().toISOString()
    }));

    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            
            if (data.type === 'ping') {
                ws.send(JSON.stringify({
                    type: 'pong',
                    timestamp: new Date().toISOString()
                }));
            }
        } catch (error) {
            logger.error('WebSocket message error', { error: error.message });
        }
    });

    ws.on('close', () => {
        wsClients.delete(ws);
        logger.info('WebSocket client disconnected', { total: wsClients.size });
    });

    ws.on('error', (error) => {
        logger.error('WebSocket error', { error: error.message });
        wsClients.delete(ws);
    });
});

// Broadcast updates to all WebSocket clients
function broadcastUpdate(type, data) {
    const message = JSON.stringify({
        type,
        data,
        timestamp: new Date().toISOString()
    });

    wsClients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            try {
                client.send(message);
            } catch (error) {
                logger.error('Failed to send to WebSocket client', { error: error.message });
            }
        }
    });
}

// Start monitoring services
healthMonitor.start();
performanceMonitor.start();
logAggregator.start();

// Periodic health check and alert evaluation
setInterval(async () => {
    try {
        const health = healthMonitor.getStatus();
        const metrics = performanceMonitor.getMetrics();
        const errorCounts = logAggregator.getErrorCounts();

        // Broadcast to WebSocket clients
        broadcastUpdate('health', health);
        broadcastUpdate('metrics', metrics);

        // Evaluate alert rules
        await alertManager.evaluateRules(health, metrics, errorCounts);

    } catch (error) {
        logger.error('Periodic check error', { error: error.message });
    }
}, 30000); // Every 30 seconds

// Broadcast metrics updates
setInterval(() => {
    try {
        const metrics = performanceMonitor.getMetrics();
        broadcastUpdate('metrics', metrics);
    } catch (error) {
        logger.error('Metrics broadcast error', { error: error.message });
    }
}, 10000); // Every 10 seconds

// Error handling
app.use((err, req, res, next) => {
    logger.error('Express error', { error: err.message, stack: err.stack });
    res.status(500).json({
        status: 'error',
        message: err.message
    });
});

// Start server
const PORT = process.env.PORT || config.service.port || 8080;
server.listen(PORT, () => {
    logger.info(`${config.service.name} started`, { 
        port: PORT,
        websocket: 'enabled'
    });
    console.log(`\n🏥 Diagnostic Service running on http://localhost:${PORT}`);
    console.log(`📊 WebSocket available at ws://localhost:${PORT}`);
    console.log(`📖 API Documentation: http://localhost:${PORT}\n`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    logger.info('Shutting down diagnostic service...');
    
    healthMonitor.stop();
    performanceMonitor.stop();
    logAggregator.stop();
    
    server.close(() => {
        logger.info('Server closed');
        process.exit(0);
    });
});

process.on('SIGTERM', () => {
    logger.info('SIGTERM received, shutting down...');
    process.exit(0);
});

module.exports = { app, server };

