/**
 * Email Alert Channel
 */

const nodemailer = require('nodemailer');
const logger = require('../../utils/logger');

class EmailChannel {
    constructor() {
        this.config = {
            host: process.env.EMAIL_SMTP_HOST,
            port: parseInt(process.env.EMAIL_SMTP_PORT || '587'),
            user: process.env.EMAIL_SMTP_USER,
            password: process.env.EMAIL_SMTP_PASSWORD,
            from: process.env.EMAIL_FROM,
            to: process.env.EMAIL_TO
        };

        if (!this.config.host || !this.config.user || !this.config.password) {
            logger.warn('Email credentials not configured');
            this.transporter = null;
        } else {
            this.transporter = nodemailer.createTransporter({
                host: this.config.host,
                port: this.config.port,
                secure: this.config.port === 465,
                auth: {
                    user: this.config.user,
                    pass: this.config.password
                }
            });
        }
    }

    /**
     * Send alert via Email
     */
    async send(message, severity) {
        if (!this.transporter) {
            throw new Error('Email not configured');
        }

        const mailOptions = {
            from: this.config.from,
            to: this.config.to,
            subject: `[${severity.toUpperCase()}] ${message.title}`,
            html: this.buildHtmlContent(message, severity)
        };

        try {
            await this.transporter.sendMail(mailOptions);
            logger.debug('Email alert sent successfully');
            
        } catch (error) {
            logger.error('Failed to send email alert', { error: error.message });
            throw error;
        }
    }

    /**
     * Build HTML email content
     */
    buildHtmlContent(message, severity) {
        const color = {
            critical: '#ff0000',
            warning: '#ff9900',
            info: '#0099ff'
        };

        return `
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: ${color[severity] || '#0099ff'}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }
                    .content { background: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-top: none; }
                    .details { background: white; padding: 15px; margin: 10px 0; border-left: 4px solid ${color[severity] || '#0099ff'}; }
                    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>${message.title}</h2>
                    </div>
                    <div class="content">
                        <p><strong>Severity:</strong> ${severity.toUpperCase()}</p>
                        <p>${message.text}</p>
                        
                        ${message.details ? `
                        <div class="details">
                            <strong>Details:</strong><br>
                            ${message.details}
                        </div>
                        ` : ''}
                        
                        <p><strong>Timestamp:</strong> ${new Date(message.timestamp).toLocaleString()}</p>
                    </div>
                    <div class="footer">
                        <p>Trading System Diagnostic Alert</p>
                    </div>
                </div>
            </body>
            </html>
        `;
    }
}

module.exports = EmailChannel;

