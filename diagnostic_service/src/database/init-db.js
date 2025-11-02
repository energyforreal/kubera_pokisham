/**
 * Database initialization script (File-based JSON storage)
 */

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '../../data');

function initDatabase() {
    console.log('Initializing diagnostic database...');
    
    // Create data directory if it doesn't exist
    if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
        console.log('Created data directory');
    }
    
    // Create empty JSON files for each "table"
    const files = [
        'health_snapshots.json',
        'performance_metrics.json',
        'alerts_log.json',
        'system_logs.json',
        'component_uptime.json',
        'trade_metrics.json'
    ];
    
    files.forEach(file => {
        const filePath = path.join(DATA_DIR, file);
        if (!fs.existsSync(filePath)) {
            fs.writeFileSync(filePath, JSON.stringify([]), 'utf8');
            console.log(`Created ${file}`);
        }
    });
    
    console.log('Database initialized successfully at:', DATA_DIR);
}

// Run if executed directly
if (require.main === module) {
    try {
        initDatabase();
    } catch (error) {
        console.error('Error initializing database:', error);
        process.exit(1);
    }
}

module.exports = { initDatabase };

