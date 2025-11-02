import { useState, useEffect, useRef, useCallback } from 'react';

interface Activity {
  id: string;
  timestamp: string;
  type: 'prediction' | 'trade' | 'position_change' | 'error' | 'system';
  message: string;
  data: Record<string, any>;
  level: 'info' | 'success' | 'warning' | 'error';
}

interface UseActivityStreamReturn {
  activities: Activity[];
  isConnected: boolean;
  error: string | null;
  reconnect: () => void;
}

export function useActivityStream(): UseActivityStreamReturn {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      // Close existing connection
      if (wsRef.current) {
        wsRef.current.close();
      }

      // Create new WebSocket connection
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/v1/activities/stream`;
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected to activity stream');
        setIsConnected(true);
        setError(null);

        // Start heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }
        heartbeatIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send('ping');
          }
        }, 30000); // Send ping every 30 seconds
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle heartbeat messages
          if (data.type === 'heartbeat') {
            return; // Ignore heartbeat messages
          }

          // Handle activity messages
          if (data.type && data.message) {
            setActivities(prev => {
              // Add new activity at the beginning (most recent first)
              const newActivity = {
                id: data.id,
                timestamp: data.timestamp,
                type: data.type,
                message: data.message,
                data: data.data || {},
                level: data.level || 'info'
              };

              // Remove duplicate if exists and add new one
              const filtered = prev.filter(activity => activity.id !== newActivity.id);
              return [newActivity, ...filtered].slice(0, 50); // Keep last 50 activities
            });
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected from activity stream');
        setIsConnected(false);
        
        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }

        // Attempt to reconnect after 5 seconds
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect to activity stream...');
          connect();
        }, 5000);
      };

      wsRef.current.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('Connection error - attempting to reconnect...');
      };

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to connect to activity stream');
    }
  }, []);

  const reconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    connect();
  }, [connect]);

  // Load initial activities from API
  useEffect(() => {
    const loadInitialActivities = async () => {
      try {
        const response = await fetch('/api/v1/activities/recent?limit=10');
        if (response.ok) {
          const data = await response.json();
          if (data.activities) {
            setActivities(data.activities);
          }
        }
      } catch (err) {
        console.error('Failed to load initial activities:', err);
      }
    };

    loadInitialActivities();
  }, []);

  // Connect on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
    };
  }, [connect]);

  return {
    activities,
    isConnected,
    error,
    reconnect
  };
}
