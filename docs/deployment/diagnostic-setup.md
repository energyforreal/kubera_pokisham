# Diagnostic System Setup Guide

## Step-by-Step Installation

### Step 1: Install Dependencies

```bash
# Install diagnostic service dependencies
cd diagnostic_service
npm install

# Install diagnostic dashboard dependencies
cd ../diagnostic_dashboard
npm install
```

### Step 2: Configure Environment Variables

**For Diagnostic Service:**

Create `diagnostic_service/.env`:

```env
PORT=8080
NODE_ENV=production

# Monitoring Configuration
HEALTH_CHECK_INTERVAL=30000
PERFORMANCE_CHECK_INTERVAL=60000
LOG_WATCH_ENABLED=true

# Target URLs
BACKEND_API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
BOT_HEALTH_FILE=../bot_health.json
LOG_FILE=../logs/kubera_pokisham.log

# Alert Channels - Copy from your main .env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID

# Optional: Slack
SLACK_WEBHOOK_URL=

# Optional: Email
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=
EMAIL_SMTP_PASSWORD=
EMAIL_FROM=
EMAIL_TO=

# Settings
ALERT_RATE_LIMIT_MINUTES=5
ALERT_DEDUPLICATION_ENABLED=true
DATABASE_PATH=./data/diagnostic.db
```

**For Diagnostic Dashboard:**

Create `diagnostic_dashboard/.env.local`:

```env
NEXT_PUBLIC_DIAGNOSTIC_API=http://localhost:8080/api
NEXT_PUBLIC_DIAGNOSTIC_WS=ws://localhost:8080
```

### Step 3: Initialize Database

```bash
cd diagnostic_service
npm run init-db
```

You should see: "Database initialized successfully"

### Step 4: Test Individual Components

**Test Diagnostic Service:**

```bash
cd diagnostic_service
npm start
```

Open `http://localhost:8080` - You should see service info.

**Test Diagnostic Dashboard:**

```bash
cd diagnostic_dashboard
npm run dev
```

Open `http://localhost:3001` - Dashboard should load (may show connection errors until service is running).

### Step 5: Full System Startup

Stop any test services (Ctrl+C), then:

```bash
# From project root
restart.bat
```

This will start all components in order:
1. ✅ Trading Bot (port: agent process)
2. ✅ Backend API (port: 8000)
3. ✅ Frontend Dashboard (port: 3000)
4. ✅ Diagnostic Service (port: 8080)
5. ✅ Diagnostic Dashboard (port: 3001)

### Step 6: Verify Installation

**Check All Services:**

1. Trading Dashboard: http://localhost:3000
2. **Diagnostic Dashboard: http://localhost:3001** ← New!
3. Backend API Docs: http://localhost:8000/docs
4. Diagnostic API: http://localhost:8080
5. Prometheus Metrics: http://localhost:8080/metrics

**Verify Monitoring:**

1. Open Diagnostic Dashboard: http://localhost:3001
2. Check all three components show as healthy (🟢)
3. Review performance metrics
4. Check logs tab for activity
5. Send Telegram /status command to verify bot

### Step 7: Test Alert Channels

1. Go to http://localhost:3001/alerts
2. Click "Test Alert Channels"
3. Verify you receive a test message on Telegram
4. Check results shown on screen

## Verification Checklist

- [ ] Diagnostic service running on port 8080
- [ ] Diagnostic dashboard accessible on port 3001
- [ ] All components showing healthy status
- [ ] WebSocket connected (Live indicator on dashboard)
- [ ] Performance metrics updating
- [ ] Logs streaming properly
- [ ] Telegram alerts working
- [ ] Prometheus metrics endpoint responding

## Common Setup Issues

### Issue: npm install fails

**Solution:**
```bash
# Clear cache and retry
npm cache clean --force
npm install
```

### Issue: Port already in use

**Solution:**
```bash
# Change port in diagnostic_service/.env
PORT=8081

# Update diagnostic_dashboard/.env.local
NEXT_PUBLIC_DIAGNOSTIC_API=http://localhost:8081/api
NEXT_PUBLIC_DIAGNOSTIC_WS=ws://localhost:8081
```

### Issue: Database initialization fails

**Solution:**
```bash
# Create data directory manually
mkdir diagnostic_service/data

# Retry initialization
cd diagnostic_service
npm run init-db
```

### Issue: Dashboard shows "Failed to fetch"

**Possible causes:**
1. Diagnostic service not running - start it first
2. Wrong URL in .env.local - verify configuration
3. CORS issue - check browser console for details

**Solution:**
```bash
# Restart diagnostic service
cd diagnostic_service
npm start

# In another terminal, restart dashboard
cd diagnostic_dashboard
npm run dev
```

### Issue: Alerts not sending

**Solution:**
1. Verify credentials in `.env`
2. Check Telegram bot token is correct
3. Test via dashboard's "Test Alert Channels" button
4. Review diagnostic service console for errors

### Issue: Components showing as down

**Possible causes:**
1. Components actually not running
2. Incorrect URLs in config
3. Firewall blocking connections

**Solution:**
1. Verify all services are running:
   ```bash
   # Check processes
   tasklist | findstr "python node"
   ```
2. Check URLs in `diagnostic_service/config/config.json`
3. Try accessing endpoints manually:
   ```bash
   curl http://localhost:8000/api/v1/health
   curl http://localhost:3000
   ```

## Optional: Slack Integration

1. Create Slack Incoming Webhook:
   - Go to https://api.slack.com/apps
   - Create app → Incoming Webhooks
   - Add webhook to workspace
   - Copy webhook URL

2. Add to `diagnostic_service/.env`:
   ```env
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

3. Enable in `diagnostic_service/config/alerts.json`:
   ```json
   "slack": {
     "enabled": true,
     "severity": ["critical", "warning"]
   }
   ```

4. Restart diagnostic service
5. Test via dashboard

## Optional: Email Alerts

1. Get Gmail App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"

2. Configure in `diagnostic_service/.env`:
   ```env
   EMAIL_SMTP_HOST=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_SMTP_USER=your.email@gmail.com
   EMAIL_SMTP_PASSWORD=your_app_password
   EMAIL_FROM=your.email@gmail.com
   EMAIL_TO=recipient@example.com
   ```

3. Enable in `diagnostic_service/config/alerts.json`:
   ```json
   "email": {
     "enabled": true,
     "severity": ["critical"]
   }
   ```

4. Restart and test

## Next Steps

1. **Customize Alert Rules**: Edit `diagnostic_service/config/alerts.json`
2. **Adjust Thresholds**: Modify `diagnostic_service/config/config.json`
3. **Setup Grafana**: Import dashboard from `monitoring/grafana/dashboards/`
4. **Monitor Daily**: Bookmark http://localhost:3001 for easy access
5. **Review Documentation**: Read `DIAGNOSTIC_SYSTEM.md` for complete guide

## Backup & Maintenance

### Backup Diagnostic Data

```bash
# Backup database
copy diagnostic_service\data\diagnostic.db diagnostic_service\data\diagnostic.db.backup

# Backup configuration
copy diagnostic_service\config\alerts.json diagnostic_service\config\alerts.json.backup
copy diagnostic_service\config\config.json diagnostic_service\config\config.json.backup
```

### Clean Old Data

The system automatically cleans data older than 30 days. To manually clean:

1. Stop diagnostic service
2. Delete `diagnostic_service/data/diagnostic.db`
3. Run `npm run init-db`
4. Restart service

### Update Dependencies

```bash
# Update diagnostic service
cd diagnostic_service
npm update

# Update diagnostic dashboard
cd ../diagnostic_dashboard
npm update
```

## Support & Troubleshooting

1. Check `DIAGNOSTIC_SYSTEM.md` for complete documentation
2. Review diagnostic service console logs
3. Check browser console in diagnostic dashboard
4. Review `logs/kubera_pokisham.log` for trading agent logs
5. Test components individually to isolate issues

## Success Criteria

You've successfully installed the diagnostic system when:

✅ All services start without errors
✅ Diagnostic dashboard shows all components as healthy
✅ Performance metrics are updating in real-time
✅ Logs are streaming and searchable
✅ Test alert successfully sent to Telegram
✅ WebSocket connection is stable (Live indicator)
✅ Prometheus metrics endpoint is responding

**Congratulations! Your diagnostic system is now operational!** 🎉

---

For complete documentation, see `DIAGNOSTIC_SYSTEM.md`

