/**
 * Telegram Alert Channel
 */

const axios = require('axios');
const logger = require('../../utils/logger');

class TelegramChannel {
    constructor() {
        this.botToken = process.env.TELEGRAM_BOT_TOKEN;
        this.chatId = process.env.TELEGRAM_CHAT_ID;
        
        if (!this.botToken || !this.chatId) {
            logger.warn('Telegram credentials not configured');
        }
    }

    /**
     * Send alert via Telegram
     */
    async send(message, severity) {
        if (!this.botToken || !this.chatId) {
            throw new Error('Telegram not configured');
        }

        const formattedMessage = this.formatMessage(message, severity);
        
        try {
            const url = `https://api.telegram.org/bot${this.botToken}/sendMessage`;
            
            await axios.post(url, {
                chat_id: this.chatId,
                text: formattedMessage,
                parse_mode: 'HTML',
                disable_web_page_preview: true
            });

            logger.debug('Telegram alert sent successfully');
            
        } catch (error) {
            logger.error('Failed to send Telegram alert', { error: error.message });
            throw error;
        }
    }

    /**
     * Format message for Telegram
     */
    formatMessage(message, severity) {
        const severityEmoji = {
            critical: '🔴',
            warning: '🟠',
            info: 'ℹ️'
        };

        const emoji = severityEmoji[severity] || 'ℹ️';
        
        let text = `${emoji} <b>${message.title}</b>\n\n`;
        
        if (message.text) {
            text += `${message.text}\n\n`;
        }
        
        if (message.details) {
            text += `<i>${message.details}</i>\n\n`;
        }
        
        text += `⏰ ${new Date(message.timestamp).toLocaleString()}`;
        
        return text;
    }
}

module.exports = TelegramChannel;

