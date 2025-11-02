'use client';

import { useEffect, useState } from 'react';
import { diagnosticApi, Alert } from '@/lib/api';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [testResults, setTestResults] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const data = await diagnosticApi.getAlerts(50);
      setAlerts(data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const testAlertChannels = async () => {
    try {
      setTesting(true);
      const results = await diagnosticApi.testAlerts();
      setTestResults(results);
    } catch (error) {
      console.error('Error testing alerts:', error);
      setTestResults({ error: 'Test failed' });
    } finally {
      setTesting(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, []);

  const severityIcons = {
    critical: <AlertTriangle className="w-5 h-5 text-red-600" />,
    warning: <Info className="w-5 h-5 text-yellow-600" />,
    info: <CheckCircle className="w-5 h-5 text-blue-600" />,
  };

  const severityColors = {
    critical: 'bg-red-100 dark:bg-red-900 border-red-300 dark:border-red-700',
    warning: 'bg-yellow-100 dark:bg-yellow-900 border-yellow-300 dark:border-yellow-700',
    info: 'bg-blue-100 dark:bg-blue-900 border-blue-300 dark:border-blue-700',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          System Alerts
        </h1>
        <div className="flex space-x-3">
          <button
            onClick={testAlertChannels}
            disabled={testing}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {testing ? 'Testing...' : 'Test Alert Channels'}
          </button>
          <button
            onClick={fetchAlerts}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Test Results */}
      {testResults && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="font-semibold mb-2">Test Results:</h3>
          <div className="space-y-2">
            {Object.entries(testResults).map(([channel, result]) => (
              <div key={channel} className="flex items-center justify-between">
                <span className="capitalize">{channel}:</span>
                <span className={result === 'success' ? 'text-green-600' : 'text-red-600'}>
                  {String(result)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alert Statistics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-red-50 dark:bg-red-900 rounded-lg p-4 border border-red-200 dark:border-red-700">
          <div className="text-3xl font-bold text-red-600">
            {alerts.filter(a => a.severity === 'critical').length}
          </div>
          <div className="text-sm text-red-700 dark:text-red-300">Critical Alerts</div>
        </div>
        <div className="bg-yellow-50 dark:bg-yellow-900 rounded-lg p-4 border border-yellow-200 dark:border-yellow-700">
          <div className="text-3xl font-bold text-yellow-600">
            {alerts.filter(a => a.severity === 'warning').length}
          </div>
          <div className="text-sm text-yellow-700 dark:text-yellow-300">Warning Alerts</div>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900 rounded-lg p-4 border border-blue-200 dark:border-blue-700">
          <div className="text-3xl font-bold text-blue-600">
            {alerts.filter(a => a.severity === 'info').length}
          </div>
          <div className="text-sm text-blue-700 dark:text-blue-300">Info Alerts</div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {loading && alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">Loading alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No alerts yet</div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`rounded-lg border-2 p-4 ${severityColors[alert.severity as keyof typeof severityColors]}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className="mt-1">
                    {severityIcons[alert.severity as keyof typeof severityIcons]}
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{alert.rule}</h3>
                    <p className="text-sm opacity-75 mt-1">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                    {alert.channels && alert.channels.length > 0 && (
                      <div className="flex gap-2 mt-2">
                        {alert.channels.map((channel) => (
                          <span
                            key={channel}
                            className="px-2 py-1 bg-white/50 dark:bg-black/50 rounded text-xs"
                          >
                            {channel}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                <span className="px-3 py-1 bg-white/50 dark:bg-black/50 rounded-full text-xs font-medium uppercase">
                  {alert.severity}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

