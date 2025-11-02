/**
 * Log Aggregator - Aggregates and parses logs from all components
 */

const fs = require('fs');
const path = require('path');
const { Tail } = require('tail');
const logger = require('../utils/logger');
const { insertSystemLog } = require('../database/db');

class LogAggregator {
    constructor(config) {
        this.config = config;
        this.logFile = path.resolve(__dirname, '../../..', process.env.LOG_FILE || '../logs/kubera_pokisham.log');
        this.tail = null;
        this.errorCounts = {
            lastHour: 0,
            last10Minutes: 0
        };
        this.errorTimestamps = [];
    }

    /**
     * Start log aggregation
     */
    start() {
        if (!this.config.monitoring.logWatchEnabled) {
            logger.info('Log watching disabled');
            return;
        }

        logger.info('Starting log aggregator', { logFile: this.logFile });

        try {
            // Check if log file exists
            if (!fs.existsSync(this.logFile)) {
                logger.warn('Log file does not exist yet', { path: this.logFile });
                // We'll try to watch it anyway, tail will wait for file creation
            }

            // Start tailing log file
            this.tail = new Tail(this.logFile, {
                follow: true,
                useWatchFile: true,
                fsWatchOptions: {
                    interval: 1000
                }
            });

            this.tail.on('line', (line) => this.processLogLine(line));
            
            this.tail.on('error', (error) => {
                logger.error('Log tail error', { error: error.message });
            });

            logger.info('Log aggregator started');

        } catch (error) {
            logger.error('Failed to start log aggregator', { error: error.message });
        }

        // Periodic error count cleanup
        setInterval(() => this.cleanupErrorCounts(), 60000);
    }

    /**
     * Stop log aggregation
     */
    stop() {
        if (this.tail) {
            this.tail.unwatch();
            this.tail = null;
            logger.info('Log aggregator stopped');
        }
    }

    /**
     * Process a log line
     */
    processLogLine(line) {
        try {
            // Try to parse as JSON (structured logs)
            const log = this.parseLogLine(line);
            
            if (log) {
                // Store in database
                insertSystemLog(
                    log.component || 'tradingAgent',
                    log.level,
                    log.message,
                    log.context
                );

                // Track errors
                if (log.level === 'error' || log.level === 'critical') {
                    this.trackError();
                }

                // Log critical errors to console
                if (log.level === 'critical' || log.level === 'error') {
                    logger.warn('Critical/Error log detected', {
                        component: log.component,
                        message: log.message
                    });
                }
            }

        } catch (error) {
            // Silently ignore parse errors for non-JSON lines
        }
    }

    /**
     * Parse log line into structured format
     */
    parseLogLine(line) {
        try {
            // Check if it's JSON format
            if (line.trim().startsWith('{')) {
                const parsed = JSON.parse(line);
                return {
                    level: parsed.level || 'info',
                    message: parsed.message || parsed.msg || line,
                    component: parsed.component || parsed.logger || 'tradingAgent',
                    context: parsed
                };
            }

            // Try to parse structured format: [timestamp] [level] message
            const match = line.match(/\[(.*?)\]\s*\[(.*?)\]\s*(.*)/);
            if (match) {
                return {
                    level: match[2].toLowerCase(),
                    message: match[3],
                    component: 'tradingAgent',
                    context: { raw: line }
                };
            }

            // Fallback: classify based on keywords
            const levelKeywords = {
                error: ['error', 'exception', 'failed', 'failure', 'critical'],
                warning: ['warning', 'warn', 'deprecated'],
                info: ['info', 'started', 'stopped', 'initialized']
            };

            let level = 'info';
            const lowerLine = line.toLowerCase();
            
            for (const [lvl, keywords] of Object.entries(levelKeywords)) {
                if (keywords.some(kw => lowerLine.includes(kw))) {
                    level = lvl;
                    break;
                }
            }

            return {
                level,
                message: line,
                component: 'tradingAgent',
                context: { raw: line }
            };

        } catch (error) {
            return null;
        }
    }

    /**
     * Track error occurrence
     */
    trackError() {
        const now = Date.now();
        this.errorTimestamps.push(now);
    }

    /**
     * Cleanup old error timestamps
     */
    cleanupErrorCounts() {
        const now = Date.now();
        const oneHourAgo = now - (60 * 60 * 1000);
        const tenMinutesAgo = now - (10 * 60 * 1000);

        // Remove timestamps older than 1 hour
        this.errorTimestamps = this.errorTimestamps.filter(ts => ts > oneHourAgo);

        // Count errors
        this.errorCounts.lastHour = this.errorTimestamps.length;
        this.errorCounts.last10Minutes = this.errorTimestamps.filter(ts => ts > tenMinutesAgo).length;
    }

    /**
     * Get error counts
     */
    getErrorCounts() {
        this.cleanupErrorCounts();
        return { ...this.errorCounts };
    }

    /**
     * Get recent logs from database
     */
    getRecentLogs(component = null, level = null, limit = 100) {
        const { getRecentLogs } = require('../database/db');
        return getRecentLogs(component, level, limit);
    }
}

module.exports = LogAggregator;

