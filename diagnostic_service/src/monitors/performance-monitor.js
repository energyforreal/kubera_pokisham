/**
 * Performance Monitor - Tracks system performance metrics
 */

const os = require('os');
const osUtils = require('node-os-utils');
const axios = require('axios');
const logger = require('../utils/logger');
const { insertPerformanceMetric } = require('../database/db');

const cpu = osUtils.cpu;
const mem = osUtils.mem;

class PerformanceMonitor {
    constructor(config) {
        this.config = config;
        this.interval = config.monitoring.performanceCheckInterval || 60000;
        this.intervalId = null;
        this.metrics = {};
    }

    /**
     * Start performance monitoring
     */
    start() {
        logger.info('Starting performance monitor', { interval: this.interval });
        this.collect(); // Initial collection
        this.intervalId = setInterval(() => this.collect(), this.interval);
    }

    /**
     * Stop performance monitoring
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            logger.info('Performance monitor stopped');
        }
    }

    /**
     * Collect performance metrics
     */
    async collect() {
        logger.debug('Collecting performance metrics');

        try {
            // System metrics
            await this.collectSystemMetrics();
            
            // Backend API metrics
            await this.collectBackendMetrics();
            
            // Trading agent metrics
            await this.collectTradingAgentMetrics();

        } catch (error) {
            logger.error('Performance collection error', { error: error.message });
        }
    }

    /**
     * Collect system resource metrics
     */
    async collectSystemMetrics() {
        try {
            // CPU usage
            const cpuUsage = await cpu.usage();
            this.metrics.cpuUsage = cpuUsage;
            insertPerformanceMetric('system', 'cpu_usage', cpuUsage, 'percent');

            // Memory usage
            const memInfo = await mem.info();
            this.metrics.memoryUsage = memInfo.usedMemPercentage;
            this.metrics.memoryTotal = memInfo.totalMemMb;
            this.metrics.memoryUsed = memInfo.usedMemMb;
            
            insertPerformanceMetric('system', 'memory_usage', memInfo.usedMemPercentage, 'percent');
            insertPerformanceMetric('system', 'memory_used', memInfo.usedMemMb, 'MB');
            insertPerformanceMetric('system', 'memory_total', memInfo.totalMemMb, 'MB');

            // Free memory
            const freeMemMb = memInfo.freeMemMb;
            insertPerformanceMetric('system', 'memory_free', freeMemMb, 'MB');

            logger.debug('System metrics collected', {
                cpu: `${cpuUsage.toFixed(2)}%`,
                memory: `${memInfo.usedMemPercentage.toFixed(2)}%`
            });

        } catch (error) {
            logger.error('System metrics collection failed', { error: error.message });
        }
    }

    /**
     * Collect backend API performance metrics
     */
    async collectBackendMetrics() {
        try {
            const backendUrl = this.config.components.backend.healthEndpoint;
            const startTime = Date.now();

            const response = await axios.get(backendUrl, {
                timeout: this.config.components.backend.timeout
            });

            const latency = Date.now() - startTime;
            this.metrics.backendLatency = latency;

            insertPerformanceMetric('backend', 'api_latency', latency, 'ms');

            // Extract additional metrics from response
            const data = response.data;
            if (data.uptime_seconds) {
                insertPerformanceMetric('backend', 'uptime', data.uptime_seconds, 'seconds');
            }
            if (data.error_count !== undefined) {
                insertPerformanceMetric('backend', 'error_count', data.error_count, 'count');
            }

            logger.debug('Backend metrics collected', { latency: `${latency}ms` });

        } catch (error) {
            logger.error('Backend metrics collection failed', { error: error.message });
        }
    }

    /**
     * Collect trading agent performance metrics
     */
    async collectTradingAgentMetrics() {
        try {
            const fs = require('fs');
            const path = require('path');
            const healthFilePath = path.resolve(
                __dirname, 
                '../../..', 
                this.config.components.tradingAgent.healthFile
            );

            if (!fs.existsSync(healthFilePath)) {
                return;
            }

            const data = JSON.parse(fs.readFileSync(healthFilePath, 'utf8'));

            // Store metrics
            if (data.uptime_seconds) {
                insertPerformanceMetric('tradingAgent', 'uptime', data.uptime_seconds, 'seconds');
            }
            if (data.signals_count !== undefined) {
                insertPerformanceMetric('tradingAgent', 'signals_generated', data.signals_count, 'count');
            }
            if (data.trades_count !== undefined) {
                insertPerformanceMetric('tradingAgent', 'trades_executed', data.trades_count, 'count');
            }
            if (data.errors_count !== undefined) {
                insertPerformanceMetric('tradingAgent', 'error_count', data.errors_count, 'count');
            }

            this.metrics.agentSignals = data.signals_count || 0;
            this.metrics.agentTrades = data.trades_count || 0;
            this.metrics.agentErrors = data.errors_count || 0;

            logger.debug('Trading agent metrics collected', {
                signals: data.signals_count,
                trades: data.trades_count
            });

        } catch (error) {
            logger.error('Trading agent metrics collection failed', { error: error.message });
        }
    }

    /**
     * Get current metrics
     */
    getMetrics() {
        return {
            timestamp: new Date().toISOString(),
            ...this.metrics
        };
    }

    /**
     * Get metrics for specific component
     */
    getComponentMetrics(component) {
        const prefix = component.toLowerCase();
        const filtered = {};
        
        for (const [key, value] of Object.entries(this.metrics)) {
            if (key.toLowerCase().startsWith(prefix)) {
                filtered[key] = value;
            }
        }
        
        return filtered;
    }
}

module.exports = PerformanceMonitor;

