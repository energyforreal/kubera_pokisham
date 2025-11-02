/**
 * API Routes for Diagnostic Service
 */

const express = require('express');
const { 
    getRecentHealthSnapshots,
    getRecentPerformanceMetrics,
    getRecentAlerts,
    getRecentLogs,
    getComponentUptimeStats
} = require('../database/db');

const router = express.Router();

/**
 * GET /health - Overall system health
 */
router.get('/health', (req, res) => {
    try {
        const healthMonitor = req.app.get('healthMonitor');
        const status = healthMonitor.getStatus();
        
        res.json({
            status: 'success',
            data: status
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

/**
 * GET /metrics - Current performance metrics
 */
router.get('/metrics', (req, res) => {
    try {
        const performanceMonitor = req.app.get('performanceMonitor');
        const metrics = performanceMonitor.getMetrics();
        
        res.json({
            status: 'success',
            data: metrics
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

/**
 * GET /metrics/:component - Component-specific metrics
 */
router.get('/metrics/:component', (req, res) => {
    try {
        const { component } = req.params;
        const { limit = 100 } = req.query;
        
        const metrics = getRecentPerformanceMetrics(component, null, parseInt(limit));
        
        res.json({
            status: 'success',
            data: metrics
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

/**
 * GET /logs - Recent system logs
 */
router.get('/logs', (req, res) => {
    try {
        const { component, level, limit = 100 } = req.query;
        
        const logs = getRecentLogs(
            component || null,
            level || null,
            parseInt(limit)
        );
        
        res.json({
            status: 'success',
            data: logs
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

/**
 * GET /alerts - Recent alerts
 */
router.get('/alerts', (req, res) => {
    try {
        const { limit = 50 } = req.query;
        const alertManager = req.app.get('alertManager');
        
        const alerts = alertManager.getAlertHistory(parseInt(limit));
        
        res.json({
            status: 'success',
            data: alerts
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

/**
 * GET /alerts/history - Alerts from database
 */
router.get('/alerts/history', (req, res) => {
    try {
        const { limit = 50 } = req.query;
        const alerts = getRecentAlerts(parseInt(limit));
        
        res.json({
            status: 'success',
            data: alerts
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

/**
 * POST /alerts/test - Test alert channels
 */
router.post('/alerts/test', async (req, res) => {
    try {
        const alertManager = req.app.get('alertManager');
        const results = await alertManager.testChannels();
        
        res.json({
            status: 'success',
            data: results
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

/**
 * POST /alerts/rules - Update alert rules
 */
router.post('/alerts/rules', (req, res) => {
    try {
        const alertManager = req.app.get('alertManager');
        alertManager.reloadConfig();
        
        res.json({
            status: 'success',
            message: 'Alert rules reloaded'
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

/**
 * GET /status/summary - Dashboard summary
 */
router.get('/status/summary', (req, res) => {
    try {
        const healthMonitor = req.app.get('healthMonitor');
        const performanceMonitor = req.app.get('performanceMonitor');
        const logAggregator = req.app.get('logAggregator');
        
        const health = healthMonitor.getStatus();
        const metrics = performanceMonitor.getMetrics();
        const errorCounts = logAggregator.getErrorCounts();
        const uptimeStats = getComponentUptimeStats();
        
        res.json({
            status: 'success',
            data: {
                health,
                metrics,
                errorCounts,
                uptime: uptimeStats,
                timestamp: new Date().toISOString()
            }
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

/**
 * GET /history/health/:component - Health history for component
 */
router.get('/history/health/:component', (req, res) => {
    try {
        const { component } = req.params;
        const { limit = 100 } = req.query;
        
        const history = getRecentHealthSnapshots(component, parseInt(limit));
        
        res.json({
            status: 'success',
            data: history
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

/**
 * GET /uptime - Component uptime statistics
 */
router.get('/uptime', (req, res) => {
    try {
        const stats = getComponentUptimeStats();
        
        res.json({
            status: 'success',
            data: stats
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

/**
 * POST /events - Receive events from trading agent
 */
router.post('/events', (req, res) => {
    try {
        const { component, event_type, data, timestamp } = req.body;
        
        // Validate required fields
        if (!component || !event_type) {
            return res.status(400).json({
                status: 'error',
                message: 'Missing required fields: component and event_type'
            });
        }
        
        // Log event
        const logAggregator = req.app.get('logAggregator');
        if (logAggregator) {
            // Store event in log aggregator
            const eventMessage = `${event_type}: ${JSON.stringify(data || {})}`;
            logAggregator.logEntry(component, 'info', eventMessage, data || {});
        }
        
        // Optionally store in database or metrics
        // This can be extended based on needs
        
        res.json({
            status: 'success',
            message: 'Event received',
            event: {
                component,
                event_type,
                timestamp: timestamp || new Date().toISOString()
            }
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: error.message
        });
    }
});

module.exports = router;

