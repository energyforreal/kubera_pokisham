/**
 * WebSocket hook for real-time updates
 */

import { useEffect, useRef, useState, useCallback } from 'react';

function buildWsCandidates(): string[] {
  // 1) Explicit env wins
  const envUrl = process.env.NEXT_PUBLIC_DIAGNOSTIC_WS;
  const candidates: string[] = [];
  if (envUrl && envUrl.trim().length > 0) candidates.push(envUrl.trim());
  
  // 2) Build from current location, prefer secure when page is https
  if (typeof window !== 'undefined') {
    const isSecure = window.location.protocol === 'https:';
    const protocol = isSecure ? 'wss' : 'ws';
    const host = window.location.hostname || 'localhost';
    // Default diagnostic service port is 8080 unless NEXT_PUBLIC_DIAGNOSTIC_PORT is set
    const port = process.env.NEXT_PUBLIC_DIAGNOSTIC_PORT || '8080';
    candidates.push(`${protocol}://${host}:${port}`);
    if (host === 'localhost') {
      candidates.push(`${protocol}://127.0.0.1:${port}`);
    }
  }
  
  // 3) SSR fallback
  if (candidates.length === 0) candidates.push('ws://localhost:8080');
  return candidates;
}

interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp: string;
}

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [health, setHealth] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout>();

  const candidateUrls = useRef<string[]>([]);
  const candidateIndex = useRef<number>(0);

  const connect = useCallback(() => {
    if (candidateUrls.current.length === 0) {
      candidateUrls.current = buildWsCandidates();
      candidateIndex.current = 0;
    }
    const url = candidateUrls.current[candidateIndex.current % candidateUrls.current.length];
    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        
        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);

        // Store interval for cleanup
        (ws.current as any).pingInterval = pingInterval;
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Update specific state based on message type
          if (message.type === 'health') {
            setHealth(message.data);
          } else if (message.type === 'metrics') {
            setMetrics(message.data);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error, 'url:', url);
        // Proactively rotate to next candidate on error
        try {
          candidateIndex.current += 1;
          if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.close();
          }
        } catch {}
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        // Clear ping interval
        if ((ws.current as any)?.pingInterval) {
          clearInterval((ws.current as any).pingInterval);
        }

        // Attempt reconnection after 5 seconds
        reconnectTimeout.current = setTimeout(() => {
          candidateIndex.current += 1; // try next candidate on each reconnect
          const nextUrl = candidateUrls.current[candidateIndex.current % candidateUrls.current.length];
          console.log('Attempting to reconnect...', 'next url:', nextUrl);
          connect();
        }, 5000);
      };
    } catch (error) {
      console.error('WebSocket connection error:', error, 'url:', url);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if ((ws.current as any)?.pingInterval) {
        clearInterval((ws.current as any).pingInterval);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  return {
    isConnected,
    lastMessage,
    health,
    metrics,
  };
}

