/**
 * Database connection and helper functions (File-based JSON storage)
 */

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '../../data');
const DB_FILES = {
    healthSnapshots: path.join(DATA_DIR, 'health_snapshots.json'),
    performanceMetrics: path.join(DATA_DIR, 'performance_metrics.json'),
    alertsLog: path.join(DATA_DIR, 'alerts_log.json'),
    systemLogs: path.join(DATA_DIR, 'system_logs.json'),
    componentUptime: path.join(DATA_DIR, 'component_uptime.json'),
    tradeMetrics: path.join(DATA_DIR, 'trade_metrics.json')
};

/**
 * Ensure data directory and files exist
 */
function ensureDatabase() {
    if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    
    Object.values(DB_FILES).forEach(file => {
        if (!fs.existsSync(file)) {
            fs.writeFileSync(file, JSON.stringify([]), 'utf8');
        }
    });
}

/**
 * Read data from file
 */
function readData(filename) {
    try {
        const data = fs.readFileSync(filename, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        return [];
    }
}

/**
 * Write data to file
 */
function writeData(filename, data) {
    try {
        fs.writeFileSync(filename, JSON.stringify(data, null, 2), 'utf8');
    } catch (error) {
        console.error('Error writing data:', error);
    }
}

/**
 * Get database connection (compatibility)
 */
function getDatabase() {
    ensureDatabase();
    return { ensureDatabase };
}

/**
 * Insert health snapshot
 */
function insertHealthSnapshot(component, status, responseTime, details) {
    ensureDatabase();
    const data = readData(DB_FILES.healthSnapshots);
    data.push({
        id: Date.now(),
        component,
        status,
        response_time: responseTime,
        details: JSON.stringify(details),
        timestamp: new Date().toISOString()
    });
    
    // Keep only last 1000 records
    const trimmed = data.slice(-1000);
    writeData(DB_FILES.healthSnapshots, trimmed);
    
    return { lastID: data.length };
}

/**
 * Insert performance metric
 */
function insertPerformanceMetric(component, metricName, metricValue, unit) {
    ensureDatabase();
    const data = readData(DB_FILES.performanceMetrics);
    data.push({
        id: Date.now(),
        component,
        metric_name: metricName,
        metric_value: metricValue,
        unit,
        timestamp: new Date().toISOString()
    });
    
    // Keep only last 2000 records
    const trimmed = data.slice(-2000);
    writeData(DB_FILES.performanceMetrics, trimmed);
    
    return { lastID: data.length };
}

/**
 * Insert alert log
 */
function insertAlertLog(alertId, ruleName, severity, message, component, details, channels) {
    ensureDatabase();
    const data = readData(DB_FILES.alertsLog);
    data.push({
        id: Date.now(),
        alert_id: alertId,
        rule_name: ruleName,
        severity,
        message,
        component,
        details: JSON.stringify(details),
        channels_sent: JSON.stringify(channels),
        timestamp: new Date().toISOString()
    });
    
    // Keep only last 500 records
    const trimmed = data.slice(-500);
    writeData(DB_FILES.alertsLog, trimmed);
    
    return { lastID: data.length };
}

/**
 * Insert system log
 */
function insertSystemLog(component, level, message, context) {
    ensureDatabase();
    const data = readData(DB_FILES.systemLogs);
    data.push({
        id: Date.now(),
        component,
        level,
        message,
        context: JSON.stringify(context),
        timestamp: new Date().toISOString()
    });
    
    // Keep only last 1000 records
    const trimmed = data.slice(-1000);
    writeData(DB_FILES.systemLogs, trimmed);
    
    return { lastID: data.length };
}

/**
 * Update component uptime
 */
function updateComponentUptime(component, isOnline) {
    ensureDatabase();
    const data = readData(DB_FILES.componentUptime);
    let record = data.find(r => r.component === component);
    
    if (!record) {
        record = {
            component,
            total_uptime_seconds: 0,
            last_online: isOnline ? new Date().toISOString() : null,
            last_offline: isOnline ? null : new Date().toISOString(),
            downtime_count: 0
        };
        data.push(record);
    } else {
        if (isOnline) {
            record.last_online = new Date().toISOString();
        } else {
            record.last_offline = new Date().toISOString();
            record.downtime_count++;
        }
    }
    
    writeData(DB_FILES.componentUptime, data);
}

/**
 * Get recent health snapshots
 */
function getRecentHealthSnapshots(component, limit = 100) {
    ensureDatabase();
    const data = readData(DB_FILES.healthSnapshots);
    return data
        .filter(r => r.component === component)
        .slice(-limit)
        .reverse();
}

/**
 * Get recent performance metrics
 */
function getRecentPerformanceMetrics(component, metricName, limit = 100) {
    ensureDatabase();
    const data = readData(DB_FILES.performanceMetrics);
    return data
        .filter(r => r.component === component && (!metricName || r.metric_name === metricName))
        .slice(-limit)
        .reverse();
}

/**
 * Get recent alerts
 */
function getRecentAlerts(limit = 50) {
    ensureDatabase();
    const data = readData(DB_FILES.alertsLog);
    return data.slice(-limit).reverse();
}

/**
 * Get recent logs
 */
function getRecentLogs(component = null, level = null, limit = 100) {
    ensureDatabase();
    const data = readData(DB_FILES.systemLogs);
    let filtered = data;
    
    if (component) {
        filtered = filtered.filter(r => r.component === component);
    }
    
    if (level) {
        filtered = filtered.filter(r => r.level === level);
    }
    
    return filtered.slice(-limit).reverse();
}

/**
 * Get component uptime stats
 */
function getComponentUptimeStats() {
    ensureDatabase();
    return readData(DB_FILES.componentUptime);
}

/**
 * Clean old data based on retention policy
 */
function cleanOldData(retentionDays = 30) {
    ensureDatabase();
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - retentionDays);
    const cutoff = cutoffDate.toISOString();
    
    Object.entries(DB_FILES).forEach(([name, file]) => {
        if (name === 'componentUptime') return; // Don't clean uptime data
        
        const data = readData(file);
        const filtered = data.filter(r => r.timestamp >= cutoff);
        writeData(file, filtered);
    });
    
    console.log(`Cleaned data older than ${retentionDays} days`);
}

module.exports = {
    getDatabase,
    insertHealthSnapshot,
    insertPerformanceMetric,
    insertAlertLog,
    insertSystemLog,
    updateComponentUptime,
    getRecentHealthSnapshots,
    getRecentPerformanceMetrics,
    getRecentAlerts,
    getRecentLogs,
    getComponentUptimeStats,
    cleanOldData
};

