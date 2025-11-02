/**
 * Alert Manager - Manages alert rules, evaluation, and dispatching
 */

const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');
const { insertAlertLog } = require('../database/db');
const TelegramChannel = require('./channels/telegram-channel');
const SlackChannel = require('./channels/slack-channel');
const EmailChannel = require('./channels/email-channel');

class AlertManager {
    constructor(configPath) {
        this.configPath = configPath || path.join(__dirname, '../../config/alerts.json');
        this.config = this.loadConfig();
        this.channels = this.initializeChannels();
        this.alertHistory = [];
        this.rateLimitCache = new Map();
    }

    /**
     * Load alert configuration
     */
    loadConfig() {
        try {
            const data = fs.readFileSync(this.configPath, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            logger.error('Failed to load alert config', { error: error.message });
            return { channels: {}, rules: [], rateLimiting: { enabled: false }, deduplication: { enabled: false } };
        }
    }

    /**
     * Reload configuration
     */
    reloadConfig() {
        this.config = this.loadConfig();
        logger.info('Alert configuration reloaded');
    }

    /**
     * Initialize alert channels
     */
    initializeChannels() {
        const channels = {};

        if (this.config.channels.telegram?.enabled) {
            channels.telegram = new TelegramChannel();
        }

        if (this.config.channels.slack?.enabled) {
            channels.slack = new SlackChannel();
        }

        if (this.config.channels.email?.enabled) {
            channels.email = new EmailChannel();
        }

        logger.info('Alert channels initialized', { 
            channels: Object.keys(channels).join(', ') 
        });

        return channels;
    }

    /**
     * Evaluate rules and trigger alerts
     */
    async evaluateRules(healthStatus, performanceMetrics, errorCounts) {
        const context = {
            health: healthStatus,
            performance: performanceMetrics,
            errors: errorCounts,
            timestamp: new Date().toISOString()
        };

        for (const rule of this.config.rules) {
            if (!rule.enabled) continue;

            try {
                const triggered = this.evaluateRule(rule, context);
                
                if (triggered) {
                    await this.triggerAlert(rule, context);
                }
            } catch (error) {
                logger.error('Error evaluating rule', { 
                    rule: rule.name, 
                    error: error.message 
                });
            }
        }
    }

    /**
     * Evaluate a single rule
     */
    evaluateRule(rule, context) {
        const condition = rule.condition;

        // Component downtime check
        if (rule.id === 'component_downtime') {
            const components = context.health?.components || {};
            for (const [name, comp] of Object.entries(components)) {
                if (comp.status === 'critical' || 
                    (comp.details?.heartbeat_age && comp.details.heartbeat_age > 120)) {
                    return true;
                }
            }
            return false;
        }

        // API latency spike
        if (rule.id === 'api_latency_spike') {
            const backendLatency = context.performance?.backendLatency || 0;
            return backendLatency > 2000;
        }

        // High error rate
        if (rule.id === 'high_error_rate') {
            const errorsPer10Min = context.errors?.last10Minutes || 0;
            return errorsPer10Min > 5;
        }

        // Circuit breaker triggered
        if (rule.id === 'circuit_breaker_triggered') {
            const components = context.health?.components || {};
            const backend = components.backend?.details || {};
            const agent = components.tradingAgent?.details || {};
            return backend.circuit_breaker_active || agent.circuit_breaker_active;
        }

        // High memory usage
        if (rule.id === 'high_memory_usage') {
            const memoryUsage = context.performance?.memoryUsage || 0;
            return memoryUsage > 80;
        }

        // Trade execution failure
        if (rule.id === 'trade_execution_failure') {
            // This would be triggered by explicit trade failure events
            return context.tradeFailure === true;
        }

        return false;
    }

    /**
     * Trigger an alert
     */
    async triggerAlert(rule, context) {
        const alertId = `${rule.id}_${Date.now()}`;

        // Check rate limiting
        if (this.config.rateLimiting?.enabled) {
            if (this.isRateLimited(rule.id)) {
                logger.debug('Alert rate limited', { rule: rule.name });
                return;
            }
        }

        // Check deduplication
        if (this.config.deduplication?.enabled) {
            if (this.isDuplicate(rule.id)) {
                logger.debug('Duplicate alert suppressed', { rule: rule.name });
                return;
            }
        }

        // Build alert message
        const message = this.buildAlertMessage(rule, context);
        
        // Determine which channels to send to
        const channelsToSend = this.getChannelsForSeverity(rule.severity);

        // Send alerts
        const sentChannels = [];
        for (const channelName of channelsToSend) {
            const channel = this.channels[channelName];
            if (channel) {
                try {
                    await channel.send(message, rule.severity);
                    sentChannels.push(channelName);
                    logger.info('Alert sent', { 
                        channel: channelName, 
                        rule: rule.name,
                        severity: rule.severity
                    });
                } catch (error) {
                    logger.error('Failed to send alert', { 
                        channel: channelName, 
                        error: error.message 
                    });
                }
            }
        }

        // Log alert
        insertAlertLog(
            alertId,
            rule.name,
            rule.severity,
            message.text || message.title,
            context.component || 'system',
            context,
            sentChannels
        );

        // Update rate limit cache
        this.updateRateLimitCache(rule.id);
        this.updateDeduplicationCache(rule.id);

        // Add to history
        this.alertHistory.push({
            id: alertId,
            rule: rule.name,
            severity: rule.severity,
            timestamp: new Date().toISOString(),
            channels: sentChannels
        });

        // Keep history limited
        if (this.alertHistory.length > 100) {
            this.alertHistory = this.alertHistory.slice(-100);
        }
    }

    /**
     * Build alert message
     */
    buildAlertMessage(rule, context) {
        const emoji = {
            critical: '🔴',
            warning: '🟠',
            info: 'ℹ️'
        };

        let details = '';

        if (rule.id === 'component_downtime') {
            const components = context.health?.components || {};
            const downComponents = Object.entries(components)
                .filter(([_, comp]) => comp.status === 'critical')
                .map(([name, _]) => name);
            details = `Components down: ${downComponents.join(', ')}`;
        } else if (rule.id === 'api_latency_spike') {
            details = `Backend latency: ${context.performance?.backendLatency || 0}ms`;
        } else if (rule.id === 'high_error_rate') {
            details = `Errors in last 10 minutes: ${context.errors?.last10Minutes || 0}`;
        } else if (rule.id === 'high_memory_usage') {
            details = `Memory usage: ${(context.performance?.memoryUsage || 0).toFixed(1)}%`;
        }

        return {
            title: `${emoji[rule.severity]} ${rule.name}`,
            text: rule.description,
            details,
            severity: rule.severity,
            timestamp: context.timestamp
        };
    }

    /**
     * Get channels for severity level
     */
    getChannelsForSeverity(severity) {
        const channels = [];
        
        for (const [name, config] of Object.entries(this.config.channels)) {
            if (config.enabled && config.severity.includes(severity)) {
                channels.push(name);
            }
        }
        
        return channels;
    }

    /**
     * Check if alert is rate limited
     */
    isRateLimited(ruleId) {
        const cache = this.rateLimitCache.get(ruleId);
        if (!cache) return false;

        const now = Date.now();
        const windowMs = this.config.rateLimiting.windowMinutes * 60 * 1000;
        const maxAlerts = this.config.rateLimiting.maxAlertsPerWindow;

        // Clean old timestamps
        const recentAlerts = cache.filter(ts => (now - ts) < windowMs);
        this.rateLimitCache.set(ruleId, recentAlerts);

        return recentAlerts.length >= maxAlerts;
    }

    /**
     * Update rate limit cache
     */
    updateRateLimitCache(ruleId) {
        const cache = this.rateLimitCache.get(ruleId) || [];
        cache.push(Date.now());
        this.rateLimitCache.set(ruleId, cache);
    }

    /**
     * Check if alert is duplicate
     */
    isDuplicate(ruleId) {
        const now = Date.now();
        const windowMs = this.config.deduplication.windowMinutes * 60 * 1000;

        // Check recent alert history
        const recentAlert = this.alertHistory
            .reverse()
            .find(alert => alert.rule === ruleId);

        if (recentAlert) {
            const alertTime = new Date(recentAlert.timestamp).getTime();
            return (now - alertTime) < windowMs;
        }

        return false;
    }

    /**
     * Update deduplication cache
     */
    updateDeduplicationCache(ruleId) {
        // Already handled by alertHistory
    }

    /**
     * Get alert history
     */
    getAlertHistory(limit = 50) {
        return this.alertHistory.slice(-limit).reverse();
    }

    /**
     * Test alert channels
     */
    async testChannels() {
        const results = {};

        for (const [name, channel] of Object.entries(this.channels)) {
            try {
                await channel.send({
                    title: '🧪 Test Alert',
                    text: 'This is a test alert from the diagnostic system',
                    severity: 'info',
                    timestamp: new Date().toISOString()
                }, 'info');
                results[name] = 'success';
            } catch (error) {
                results[name] = `failed: ${error.message}`;
            }
        }

        return results;
    }
}

module.exports = AlertManager;

