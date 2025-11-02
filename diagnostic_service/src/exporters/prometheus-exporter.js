/**
 * Prometheus Metrics Exporter
 */

const promClient = require('prom-client');
const logger = require('../utils/logger');

// Create a Registry
const register = new promClient.Registry();

// Add default metrics
promClient.collectDefaultMetrics({ register });

// Custom metrics
const componentHealthGauge = new promClient.Gauge({
    name: 'diagnostic_component_health',
    help: 'Component health status (0=critical, 1=warning, 2=healthy)',
    labelNames: ['component'],
    registers: [register]
});

const componentResponseTimeGauge = new promClient.Gauge({
    name: 'diagnostic_component_response_time_ms',
    help: 'Component response time in milliseconds',
    labelNames: ['component'],
    registers: [register]
});

const componentUptimeGauge = new promClient.Gauge({
    name: 'diagnostic_component_uptime_seconds',
    help: 'Component uptime in seconds',
    labelNames: ['component'],
    registers: [register]
});

const systemCpuGauge = new promClient.Gauge({
    name: 'diagnostic_system_cpu_usage_percent',
    help: 'System CPU usage percentage',
    registers: [register]
});

const systemMemoryGauge = new promClient.Gauge({
    name: 'diagnostic_system_memory_usage_percent',
    help: 'System memory usage percentage',
    registers: [register]
});

const alertCounter = new promClient.Counter({
    name: 'diagnostic_alerts_total',
    help: 'Total number of alerts triggered',
    labelNames: ['severity', 'rule'],
    registers: [register]
});

const errorCounter = new promClient.Counter({
    name: 'diagnostic_errors_total',
    help: 'Total number of errors logged',
    labelNames: ['component', 'level'],
    registers: [register]
});

const tradeCounter = new promClient.Counter({
    name: 'diagnostic_trades_total',
    help: 'Total number of trades executed',
    labelNames: ['status'],
    registers: [register]
});

class PrometheusExporter {
    constructor(healthMonitor, performanceMonitor, alertManager) {
        this.healthMonitor = healthMonitor;
        this.performanceMonitor = performanceMonitor;
        this.alertManager = alertManager;
    }

    /**
     * Update metrics from current state
     */
    updateMetrics() {
        try {
            // Update health metrics
            const health = this.healthMonitor.getStatus();
            if (health && health.components) {
                for (const [name, component] of Object.entries(health.components)) {
                    const statusValue = this.getStatusValue(component.status);
                    componentHealthGauge.set({ component: name }, statusValue);
                    
                    if (component.responseTime !== undefined) {
                        componentResponseTimeGauge.set({ component: name }, component.responseTime);
                    }
                }
            }

            // Update performance metrics
            const metrics = this.performanceMonitor.getMetrics();
            if (metrics.cpuUsage !== undefined) {
                systemCpuGauge.set(metrics.cpuUsage);
            }
            if (metrics.memoryUsage !== undefined) {
                systemMemoryGauge.set(metrics.memoryUsage);
            }

        } catch (error) {
            logger.error('Error updating Prometheus metrics', { error: error.message });
        }
    }

    /**
     * Convert status string to numeric value
     */
    getStatusValue(status) {
        const values = {
            'critical': 0,
            'warning': 1,
            'healthy': 2
        };
        return values[status] || 0;
    }

    /**
     * Record an alert
     */
    recordAlert(severity, ruleName) {
        alertCounter.inc({ severity, rule: ruleName });
    }

    /**
     * Record an error
     */
    recordError(component, level) {
        errorCounter.inc({ component, level });
    }

    /**
     * Record a trade
     */
    recordTrade(status) {
        tradeCounter.inc({ status });
    }

    /**
     * Get metrics in Prometheus format
     */
    async getMetrics() {
        this.updateMetrics();
        return register.metrics();
    }
}

module.exports = PrometheusExporter;

