/**
 * Health Monitor - Monitors component health status
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');
const { insertHealthSnapshot, updateComponentUptime } = require('../database/db');

class HealthMonitor {
    constructor(config) {
        this.config = config;
        this.components = config.components;
        this.interval = config.monitoring.healthCheckInterval || 30000;
        this.healthStatus = {};
        this.intervalId = null;
    }

    /**
     * Start health monitoring
     */
    start() {
        logger.info('Starting health monitor', { interval: this.interval });
        this.check(); // Initial check
        this.intervalId = setInterval(() => this.check(), this.interval);
    }

    /**
     * Stop health monitoring
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            logger.info('Health monitor stopped');
        }
    }

    /**
     * Check health of all components
     */
    async check() {
        logger.debug('Running health check for all components');
        
        const results = await Promise.allSettled([
            this.checkBackend(),
            this.checkFrontend(),
            this.checkTradingAgent()
        ]);

        // Aggregate results
        const summary = {
            timestamp: new Date().toISOString(),
            overall: 'healthy',
            components: {}
        };

        results.forEach((result, index) => {
            const componentNames = ['backend', 'frontend', 'tradingAgent'];
            const componentName = componentNames[index];
            
            if (result.status === 'fulfilled') {
                summary.components[componentName] = result.value;
                if (result.value.status !== 'healthy') {
                    summary.overall = result.value.status === 'critical' ? 'critical' : 'warning';
                }
            } else {
                summary.components[componentName] = {
                    status: 'critical',
                    message: result.reason?.message || 'Unknown error'
                };
                summary.overall = 'critical';
            }
        });

        this.healthStatus = summary;
        return summary;
    }

    /**
     * Check backend API health
     */
    async checkBackend() {
        const component = this.components.backend;
        const startTime = Date.now();

        try {
            const response = await axios.get(component.healthEndpoint, {
                timeout: component.timeout
            });

            const responseTime = Date.now() - startTime;
            const data = response.data;

            let status = 'healthy';
            if (data.circuit_breaker_active) {
                status = 'warning';
            }
            if (responseTime > this.config.thresholds.responseTime.critical) {
                status = 'critical';
            } else if (responseTime > this.config.thresholds.responseTime.warning) {
                status = status === 'healthy' ? 'warning' : status;
            }

            const result = {
                component: 'backend',
                status,
                responseTime,
                details: {
                    uptime_seconds: data.uptime_seconds,
                    models_loaded: data.models_loaded,
                    circuit_breaker_active: data.circuit_breaker_active,
                    last_signal: data.last_signal,
                    last_trade: data.last_trade,
                    error_count: data.error_count
                }
            };

            // Store in database
            insertHealthSnapshot('backend', status, responseTime, result.details);
            updateComponentUptime('backend', status !== 'critical');

            return result;

        } catch (error) {
            logger.error('Backend health check failed', { error: error.message });
            
            const result = {
                component: 'backend',
                status: 'critical',
                responseTime: Date.now() - startTime,
                details: { error: error.message }
            };

            insertHealthSnapshot('backend', 'critical', result.responseTime, result.details);
            updateComponentUptime('backend', false);

            return result;
        }
    }

    /**
     * Check frontend health
     */
    async checkFrontend() {
        const component = this.components.frontend;
        const startTime = Date.now();

        try {
            const response = await axios.get(component.url, {
                timeout: component.timeout
            });

            const responseTime = Date.now() - startTime;
            const status = response.status === 200 ? 'healthy' : 'warning';

            const result = {
                component: 'frontend',
                status,
                responseTime,
                details: {
                    statusCode: response.status
                }
            };

            insertHealthSnapshot('frontend', status, responseTime, result.details);
            updateComponentUptime('frontend', status !== 'critical');

            return result;

        } catch (error) {
            logger.error('Frontend health check failed', { error: error.message });
            
            const result = {
                component: 'frontend',
                status: 'critical',
                responseTime: Date.now() - startTime,
                details: { error: error.message }
            };

            insertHealthSnapshot('frontend', 'critical', result.responseTime, result.details);
            updateComponentUptime('frontend', false);

            return result;
        }
    }

    /**
     * Check trading agent health via bot_health.json
     */
    async checkTradingAgent() {
        const component = this.components.tradingAgent;
        const healthFilePath = path.resolve(__dirname, '../../..', component.healthFile);

        try {
            if (!fs.existsSync(healthFilePath)) {
                throw new Error('Health file not found - agent may not be running');
            }

            const data = JSON.parse(fs.readFileSync(healthFilePath, 'utf8'));
            
            // Check heartbeat age
            const lastHeartbeat = data.last_heartbeat ? new Date(data.last_heartbeat) : null;
            const now = new Date();
            const heartbeatAge = lastHeartbeat ? (now - lastHeartbeat) / 1000 : Infinity;

            let status = 'healthy';
            if (!data.is_alive || heartbeatAge > component.maxHeartbeatAge * 2) {
                status = 'critical';
            } else if (heartbeatAge > component.maxHeartbeatAge) {
                status = 'warning';
            }

            if (data.circuit_breaker_active) {
                status = status === 'healthy' ? 'warning' : status;
            }

            const result = {
                component: 'tradingAgent',
                status,
                responseTime: 0,
                details: {
                    is_alive: data.is_alive,
                    heartbeat_age: Math.round(heartbeatAge),
                    models_loaded: data.models_loaded,
                    circuit_breaker_active: data.circuit_breaker_active,
                    signals_count: data.signals_count,
                    trades_count: data.trades_count,
                    errors_count: data.errors_count,
                    last_signal: data.last_signal,
                    last_trade: data.last_trade
                }
            };

            insertHealthSnapshot('tradingAgent', status, 0, result.details);
            updateComponentUptime('tradingAgent', status !== 'critical');

            return result;

        } catch (error) {
            logger.error('Trading agent health check failed', { error: error.message });
            
            const result = {
                component: 'tradingAgent',
                status: 'critical',
                responseTime: 0,
                details: { error: error.message }
            };

            insertHealthSnapshot('tradingAgent', 'critical', 0, result.details);
            updateComponentUptime('tradingAgent', false);

            return result;
        }
    }

    /**
     * Get current health status
     */
    getStatus() {
        return this.healthStatus;
    }
}

module.exports = HealthMonitor;

