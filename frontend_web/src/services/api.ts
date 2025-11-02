/**
 * API client for trading backend
 */

import axios from 'axios';

// Use Next.js environment variable - will be replaced at build time
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Default API client with standard timeout
export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 15000,  // 15 seconds for most endpoints
  headers: {
    'Content-Type': 'application/json',
  },
});

// Separate client for prediction endpoints with longer timeout
export const predictionClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,  // 30 seconds for ML prediction endpoints
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token (apiClient)
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling (apiClient)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Request interceptor for adding auth token (predictionClient)
predictionClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling (predictionClient)
predictionClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error (Prediction):', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ============================================================================
// API Functions
// ============================================================================

export interface PredictionResponse {
  symbol: string;
  prediction: string;
  confidence: number;
  is_actionable: boolean;
  timestamp: string;
  individual_predictions?: any[];
  data_quality: number;
  // Add missing fields for better backend compatibility
  model_name?: string;
  features_used?: string[];
}

export interface PortfolioStatus {
  balance: number;
  equity: number;
  num_positions: number;
  total_pnl: number;
  total_pnl_percent: number;
  daily_pnl: number;
  positions: any[];
}

export interface TradeRequest {
  symbol: string;
  side?: string;
  confidence?: number;
  force?: boolean;
}

export const api = {
  // Health
  health: () => apiClient.get('/api/v1/health'),

  // Predictions (use predictionClient with longer timeout)
  getPrediction: (symbol: string = 'BTCUSD', timeframe: string = '15m') =>
    predictionClient.get<PredictionResponse>(`/api/v1/predict?symbol=${symbol}&timeframe=${timeframe}`),

  // Trading
  executeTrade: (data: TradeRequest) =>
    apiClient.post('/api/v1/trade', data),

  // Portfolio
  getPortfolioStatus: () =>
    apiClient.get<PortfolioStatus>('/api/v1/portfolio/status'),

  getPositions: () =>
    apiClient.get('/api/v1/positions'),

  closePosition: (symbol: string) =>
    apiClient.post(`/api/v1/positions/${symbol}/close`),

  updatePosition: (symbol: string, data: { stop_loss?: number; take_profit?: number }) =>
    apiClient.put(`/api/v1/positions/${symbol}`, data),

  // Trade History
  getTradeHistory: (limit: number = 50) =>
    apiClient.get(`/api/v1/trades/history?limit=${limit}`),

  // Analytics
  getDailyAnalytics: () =>
    apiClient.get('/api/v1/analytics/daily'),

  // Risk Settings
  getRiskSettings: () =>
    apiClient.get('/api/v1/settings/risk'),

  updateRiskSettings: (data: any) =>
    apiClient.post('/api/v1/settings/risk', data),

  // Market Data
  getTicker: (symbol: string) =>
    apiClient.get(`/api/v1/market/ticker/${symbol}`),

  getOHLC: (symbol: string, resolution: string = '15m', limit: number = 100) =>
    apiClient.get(`/api/v1/market/ohlc/${symbol}?resolution=${resolution}&limit=${limit}`),
};

// WebSocket connection
export class TradingWebSocket {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Function[]> = new Map();

  connect() {
    const wsUrl = API_URL.replace('http', 'ws') + '/ws';
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      try {
        // Handle plain text responses (like "pong")
        if (typeof event.data === 'string' && event.data === 'pong') {
          return; // Ignore plain text pong responses
        }
        
        const message = JSON.parse(event.data);
        
        // Ignore pong messages if they're JSON
        if (message.type === 'pong') {
          return;
        }
        
        this.emit(message.type, message.data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e, 'Data:', event.data);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Reconnect after 5 seconds
      setTimeout(() => this.connect(), 5000);
    };

    // Ping to keep connection alive
    setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000);
  }

  on(eventType: string, callback: Function) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType)!.push(callback);
  }

  off(eventType: string, callback: Function) {
    const callbacks = this.listeners.get(eventType);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private emit(eventType: string, data: any) {
    const callbacks = this.listeners.get(eventType);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const tradingWs = new TradingWebSocket();


