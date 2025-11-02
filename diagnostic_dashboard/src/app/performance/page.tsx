'use client';

import { useEffect, useState } from 'react';
import { diagnosticApi } from '@/lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useWebSocket } from '@/hooks/useWebSocket';

export default function PerformancePage() {
  const [metricsHistory, setMetricsHistory] = useState<any[]>([]);
  const { metrics: wsMetrics } = useWebSocket();

  useEffect(() => {
    // Fetch initial metrics
    const fetchMetrics = async () => {
      try {
        const data = await diagnosticApi.getMetrics();
        setMetricsHistory(prev => [...prev, { ...data, time: new Date().toLocaleTimeString() }].slice(-20));
      } catch (error) {
        console.error('Error fetching metrics:', error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  // Update with WebSocket data
  useEffect(() => {
    if (wsMetrics) {
      setMetricsHistory(prev => [
        ...prev,
        { ...wsMetrics, time: new Date().toLocaleTimeString() }
      ].slice(-20));
    }
  }, [wsMetrics]);

  const latestMetrics = metricsHistory[metricsHistory.length - 1] || {};

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
        Performance Monitoring
      </h1>

      {/* Current Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="CPU Usage"
          value={`${latestMetrics.cpuUsage?.toFixed(1) || '0'}%`}
          trend={getTrend(metricsHistory, 'cpuUsage')}
          color="blue"
        />
        <MetricCard
          title="Memory Usage"
          value={`${latestMetrics.memoryUsage?.toFixed(1) || '0'}%`}
          trend={getTrend(metricsHistory, 'memoryUsage')}
          color="green"
        />
        <MetricCard
          title="API Latency"
          value={`${latestMetrics.backendLatency || '0'}ms`}
          trend={getTrend(metricsHistory, 'backendLatency')}
          color="purple"
        />
        <MetricCard
          title="Memory Used"
          value={`${latestMetrics.memoryUsed?.toFixed(0) || '0'}MB`}
          trend={getTrend(metricsHistory, 'memoryUsed')}
          color="orange"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU & Memory Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold mb-4">System Resources</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metricsHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="cpuUsage" stroke="#3b82f6" name="CPU %" />
              <Line type="monotone" dataKey="memoryUsage" stroke="#10b981" name="Memory %" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* API Latency Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold mb-4">API Response Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metricsHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="backendLatency" stroke="#8b5cf6" name="Latency (ms)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trading Activity Chart */}
      {metricsHistory.some(m => m.agentSignals || m.agentTrades) && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold mb-4">Trading Activity</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metricsHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="agentSignals" stroke="#3b82f6" name="Signals" />
              <Line type="monotone" dataKey="agentTrades" stroke="#10b981" name="Trades" />
              <Line type="monotone" dataKey="agentErrors" stroke="#ef4444" name="Errors" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function MetricCard({ title, value, trend, color }: { title: string; value: string; trend?: number; color: keyof typeof colors }) {
  const colors = {
    blue: 'bg-blue-50 dark:bg-blue-900 text-blue-600',
    green: 'bg-green-50 dark:bg-green-900 text-green-600',
    purple: 'bg-purple-50 dark:bg-purple-900 text-purple-600',
    orange: 'bg-orange-50 dark:bg-orange-900 text-orange-600',
  };

  return (
    <div className={`rounded-lg p-4 ${colors[color]}`}>
      <div className="text-sm opacity-75 mb-1">{title}</div>
      <div className="text-2xl font-bold">{value}</div>
      {trend && (
        <div className="text-xs mt-1">
          {trend > 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}%
        </div>
      )}
    </div>
  );
}

function getTrend(history: any[], key: string): number | undefined {
  if (history.length < 2) return undefined;
  const current = history[history.length - 1]?.[key] || 0;
  const previous = history[history.length - 2]?.[key] || 0;
  if (previous === 0) return undefined;
  return ((current - previous) / previous) * 100;
}

