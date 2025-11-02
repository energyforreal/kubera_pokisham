/**
 * Slack Alert Channel
 */

const axios = require('axios');
const logger = require('../../utils/logger');

class SlackChannel {
    constructor() {
        this.webhookUrl = process.env.SLACK_WEBHOOK_URL;
        
        if (!this.webhookUrl) {
            logger.warn('Slack webhook URL not configured');
        }
    }

    /**
     * Send alert via Slack
     */
    async send(message, severity) {
        if (!this.webhookUrl) {
            throw new Error('Slack not configured');
        }

        const payload = this.buildPayload(message, severity);
        
        try {
            await axios.post(this.webhookUrl, payload);
            logger.debug('Slack alert sent successfully');
            
        } catch (error) {
            logger.error('Failed to send Slack alert', { error: error.message });
            throw error;
        }
    }

    /**
     * Build Slack payload
     */
    buildPayload(message, severity) {
        const color = {
            critical: '#ff0000',
            warning: '#ff9900',
            info: '#0099ff'
        };

        return {
            attachments: [
                {
                    color: color[severity] || '#0099ff',
                    title: message.title,
                    text: message.text,
                    fields: [
                        {
                            title: 'Details',
                            value: message.details || 'N/A',
                            short: false
                        },
                        {
                            title: 'Severity',
                            value: severity.toUpperCase(),
                            short: true
                        },
                        {
                            title: 'Timestamp',
                            value: new Date(message.timestamp).toLocaleString(),
                            short: true
                        }
                    ],
                    footer: 'Trading Diagnostic System',
                    ts: Math.floor(new Date(message.timestamp).getTime() / 1000)
                }
            ]
        };
    }
}

module.exports = SlackChannel;

