# Diagnostic Dashboard

Comprehensive monitoring and diagnostic dashboard for AI Trading System.

## Features

- **Real-time Status Monitoring**: View health status of all system components
- **Performance Metrics**: Track CPU, memory, API latency, and trading activity
- **Live Logs**: Stream and filter system logs in real-time
- **Alert Management**: View alert history and test alert channels
- **WebSocket Integration**: Real-time updates without polling

## Getting Started

### Installation

```bash
npm install
```

### Configuration

Create `.env.local` file:

```env
NEXT_PUBLIC_DIAGNOSTIC_API=http://localhost:8080/api
NEXT_PUBLIC_DIAGNOSTIC_WS=ws://localhost:8080
```

### Development

```bash
npm run dev
```

Dashboard will be available at `http://localhost:3001`

### Production

```bash
npm run build
npm start
```

## Pages

- **Status**: Overview of all components with health status
- **Performance**: Real-time performance metrics and charts
- **Logs**: System logs with filtering and search
- **Alerts**: Alert history and channel testing

## Technologies

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Recharts
- WebSocket

## API Integration

The dashboard connects to the diagnostic service running on port 8080.
Ensure the diagnostic service is running before accessing the dashboard.

