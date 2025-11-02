/**
 * Status Card Component - Display component health status
 */

interface StatusCardProps {
  component: string;
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  responseTime?: number;
  details?: any;
  lastUpdate?: string;
}

const statusColors = {
  healthy: 'bg-green-100 text-green-800 border-green-300',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  critical: 'bg-red-100 text-red-800 border-red-300',
  unknown: 'bg-gray-100 text-gray-800 border-gray-300',
};

const statusIcons = {
  healthy: '🟢',
  warning: '🟠',
  critical: '🔴',
  unknown: '⚪',
};

export default function StatusCard({
  component,
  status,
  responseTime,
  details,
  lastUpdate,
}: StatusCardProps) {
  return (
    <div className={`border-2 rounded-lg p-4 ${statusColors[status]}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold">{component}</h3>
        <span className="text-2xl">{statusIcons[status]}</span>
      </div>
      
      <div className="space-y-1 text-sm">
        <div className="flex justify-between">
          <span>Status:</span>
          <span className="font-medium uppercase">{status}</span>
        </div>
        
        {responseTime !== undefined && (
          <div className="flex justify-between">
            <span>Response Time:</span>
            <span className="font-medium">{responseTime}ms</span>
          </div>
        )}
        
        {details?.heartbeat_age !== undefined && (
          <div className="flex justify-between">
            <span>Last Heartbeat:</span>
            <span className="font-medium">{details.heartbeat_age}s ago</span>
          </div>
        )}
        
        {details?.uptime_seconds !== undefined && (
          <div className="flex justify-between">
            <span>Uptime:</span>
            <span className="font-medium">
              {Math.floor(details.uptime_seconds / 3600)}h{' '}
              {Math.floor((details.uptime_seconds % 3600) / 60)}m
            </span>
          </div>
        )}
        
        {details?.circuit_breaker_active && (
          <div className="mt-2 p-2 bg-red-200 dark:bg-red-900 rounded text-xs">
            ⚠️ Circuit Breaker Active
          </div>
        )}
      </div>
      
      {lastUpdate && (
        <div className="mt-3 text-xs opacity-75">
          Updated: {new Date(lastUpdate).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}

