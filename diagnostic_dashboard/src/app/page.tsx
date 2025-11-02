'use client';

import { useEffect, useState } from 'react';
import { diagnosticApi, SystemSummary } from '@/lib/api';
import { useWebSocket } from '@/hooks/useWebSocket';
import StatusCard from '@/components/StatusCard';
import { RefreshCw, Wifi, WifiOff } from 'lucide-react';

export default function HomePage() {
  const [summary, setSummary] = useState<SystemSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isConnected, health: wsHealth } = useWebSocket();

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const data = await diagnosticApi.getSummary();
      setSummary(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch summary');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  // Update with WebSocket data
  useEffect(() => {
    if (wsHealth && summary) {
      setSummary({
        ...summary,
        health: wsHealth,
        timestamp: new Date().toISOString(),
      });
    }
  }, [wsHealth]);

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
          <p className="text-gray-600 dark:text-gray-400">Loading system status...</p>
        </div>
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className="bg-red-100 dark:bg-red-900 border border-red-300 dark:border-red-700 rounded-lg p-4">
        <h3 className="text-red-800 dark:text-red-100 font-semibold mb-2">Error</h3>
        <p className="text-red-700 dark:text-red-200">{error}</p>
        <button
          onClick={fetchSummary}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const overallStatus = summary?.health?.overall || 'unknown';
  const components = summary?.health?.components || {};
  const metrics = summary?.metrics;
  const errorCounts = summary?.errorCounts || { lastHour: 0, last10Minutes: 0 };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            System Status
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Real-time monitoring of all trading system components
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-sm">
            {isConnected ? (
              <>
                <Wifi className="w-4 h-4 text-green-500" />
                <span className="text-green-600 dark:text-green-400">Live</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-red-500" />
                <span className="text-red-600 dark:text-red-400">Disconnected</span>
              </>
            )}
          </div>
          
          <button
            onClick={fetchSummary}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Overall Status Banner */}
      <div className={`rounded-lg p-6 ${
        overallStatus === 'healthy'
          ? 'bg-green-100 dark:bg-green-900 border border-green-300'
          : overallStatus === 'warning'
          ? 'bg-yellow-100 dark:bg-yellow-900 border border-yellow-300'
          : 'bg-red-100 dark:bg-red-900 border border-red-300'
      }`}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-1">
              {overallStatus === 'healthy' && '✅ System Healthy'}
              {overallStatus === 'warning' && '⚠️ System Warning'}
              {overallStatus === 'critical' && '🔴 System Critical'}
            </h2>
            <p className="text-sm opacity-75">
              Last updated: {summary?.timestamp ? new Date(summary.timestamp).toLocaleString() : 'Never'}
            </p>
          </div>
          
          <div className="text-right">
            <div className="text-3xl font-bold">
              {Object.values(components).filter((c: any) => c.status === 'healthy').length}/
              {Object.keys(components).length}
            </div>
            <div className="text-sm opacity-75">Components Healthy</div>
          </div>
        </div>
      </div>

      {/* Component Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(components).map(([name, data]: [string, any]) => (
          <StatusCard
            key={name}
            component={data.component || name}
            status={data.status}
            responseTime={data.responseTime}
            details={data.details}
            lastUpdate={summary?.timestamp}
          />
        ))}
      </div>

      {/* Performance Metrics */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-xl font-bold mb-4">Performance Metrics</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-900 rounded">
            <div className="text-2xl font-bold text-blue-600">
              {metrics?.cpuUsage?.toFixed(1) || '0'}%
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">CPU Usage</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-900 rounded">
            <div className="text-2xl font-bold text-green-600">
              {metrics?.memoryUsage?.toFixed(1) || '0'}%
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Memory Usage</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-900 rounded">
            <div className="text-2xl font-bold text-purple-600">
              {metrics?.backendLatency || '0'}ms
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">API Latency</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-900 rounded">
            <div className="text-2xl font-bold text-orange-600">
              {errorCounts.last10Minutes || 0}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Recent Errors</div>
          </div>
        </div>
      </div>

      {/* Trading Metrics */}
      {(metrics?.agentSignals || metrics?.agentTrades) && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-xl font-bold mb-4">Trading Activity</h3>
          
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900 rounded">
              <div className="text-2xl font-bold text-blue-600">
                {metrics?.agentSignals || 0}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Signals Generated</div>
            </div>
            
            <div className="text-center p-4 bg-green-50 dark:bg-green-900 rounded">
              <div className="text-2xl font-bold text-green-600">
                {metrics?.agentTrades || 0}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Trades Executed</div>
            </div>
            
            <div className="text-center p-4 bg-red-50 dark:bg-red-900 rounded">
              <div className="text-2xl font-bold text-red-600">
                {metrics?.agentErrors || 0}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Errors</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

