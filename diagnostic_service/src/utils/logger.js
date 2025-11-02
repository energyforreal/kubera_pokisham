/**
 * Enhanced logger utility for diagnostic service
 * Compatible with Python component logging system
 */

const fs = require('fs');
const path = require('path');

const LOG_LEVELS = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3
};

const currentLevel = process.env.LOG_LEVEL 
    ? LOG_LEVELS[process.env.LOG_LEVEL.toUpperCase()] 
    : LOG_LEVELS.INFO;

// Component-specific loggers
const componentLoggers = new Map();

class ComponentLogger {
    constructor(componentName) {
        this.componentName = componentName;
        this.logDir = path.join(process.cwd(), 'logs');
        this.sessionId = this.generateSessionId();
        
        // Ensure logs directory exists
        if (!fs.existsSync(this.logDir)) {
            fs.mkdirSync(this.logDir, { recursive: true });
        }
        
        // Create log file path
        const today = new Date().toISOString().split('T')[0].replace(/-/g, '');
        this.logFile = path.join(this.logDir, `${componentName}_${today}.json`);
    }
    
    generateSessionId() {
        const now = new Date();
        const timestamp = now.toISOString().replace(/[-:]/g, '').replace(/\..+/, '');
        const random = Math.random().toString(36).substring(2, 10);
        return `session_${timestamp}_${random}`;
    }
    
    formatLogEntry(level, operation, message, context = {}, durationMs = null, error = null) {
        const now = new Date();
        const utcTime = now.toISOString();
        const localTime = now.toLocaleString();
        
        const logEntry = {
            timestamp_utc: utcTime,
            timestamp_local: localTime,
            component: this.componentName,
            level: level.toUpperCase(),
            operation: operation,
            message: message,
            session_id: this.sessionId,
            context: context
        };
        
        if (durationMs !== null) {
            logEntry.duration_ms = durationMs;
        }
        
        if (error) {
            logEntry.error = {
                type: error.constructor.name,
                message: error.message,
                stack: error.stack
            };
        }
        
        return JSON.stringify(logEntry) + '\n';
    }
    
    writeLog(level, operation, message, context = {}, durationMs = null, error = null) {
        if (LOG_LEVELS[level.toUpperCase()] < currentLevel) {
            return;
        }
        
        const logEntry = this.formatLogEntry(level, operation, message, context, durationMs, error);
        
        // Write to file
        try {
            fs.appendFileSync(this.logFile, logEntry);
        } catch (err) {
            console.error('Failed to write to log file:', err);
        }
        
        // Also output to console for development
        const consoleMessage = `[${level.toUpperCase()}] [${this.componentName}] ${operation}: ${message}`;
        if (Object.keys(context).length > 0) {
            console.log(consoleMessage, context);
        } else {
            console.log(consoleMessage);
        }
    }
    
    info(operation, message, context = {}, durationMs = null) {
        this.writeLog('INFO', operation, message, context, durationMs);
    }
    
    warn(operation, message, context = {}, durationMs = null) {
        this.writeLog('WARN', operation, message, context, durationMs);
    }
    
    error(operation, message, context = {}, durationMs = null, error = null) {
        this.writeLog('ERROR', operation, message, context, durationMs, error);
    }
    
    debug(operation, message, context = {}, durationMs = null) {
        this.writeLog('DEBUG', operation, message, context, durationMs);
    }
}

function getComponentLogger(componentName) {
    if (!componentLoggers.has(componentName)) {
        componentLoggers.set(componentName, new ComponentLogger(componentName));
    }
    return componentLoggers.get(componentName);
}

// Legacy functions for backward compatibility
function formatMessage(level, message, context = {}) {
    const timestamp = new Date().toISOString();
    const contextStr = Object.keys(context).length > 0 ? ` ${JSON.stringify(context)}` : '';
    return `[${timestamp}] [${level}] ${message}${contextStr}`;
}

function debug(message, context) {
    if (currentLevel <= LOG_LEVELS.DEBUG) {
        console.log(formatMessage('DEBUG', message, context));
    }
}

function info(message, context) {
    if (currentLevel <= LOG_LEVELS.INFO) {
        console.log(formatMessage('INFO', message, context));
    }
}

function warn(message, context) {
    if (currentLevel <= LOG_LEVELS.WARN) {
        console.warn(formatMessage('WARN', message, context));
    }
}

function error(message, context) {
    if (currentLevel <= LOG_LEVELS.ERROR) {
        console.error(formatMessage('ERROR', message, context));
    }
}

module.exports = {
    getComponentLogger,
    ComponentLogger,
    debug,
    info,
    warn,
    error
};

