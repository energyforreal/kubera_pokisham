'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Bot, 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Target,
  DollarSign,
  AlertCircle,
  Settings
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { useActivityStream } from '@/hooks/useActivityStream';

interface Activity {
  id: string;
  timestamp: string;
  type: 'prediction' | 'trade' | 'position_change' | 'error' | 'system';
  message: string;
  data: Record<string, any>;
  level: 'info' | 'success' | 'warning' | 'error';
}

export default function BotActivityMonitor() {
  const { activities, isConnected, error, reconnect } = useActivityStream();

  const getActivityIcon = (type: string, level: string) => {
    switch (type) {
      case 'prediction':
        return <Target className="h-4 w-4 text-blue-500" />;
      case 'trade':
        return <DollarSign className="h-4 w-4 text-green-500" />;
      case 'position_change':
        return <TrendingUp className="h-4 w-4 text-purple-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'system':
        return <Settings className="h-4 w-4 text-gray-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getActivityColor = (level: string) => {
    switch (level) {
      case 'success':
        return 'border-l-green-500 bg-green-500/5';
      case 'warning':
        return 'border-l-yellow-500 bg-yellow-500/5';
      case 'error':
        return 'border-l-red-500 bg-red-500/5';
      default:
        return 'border-l-blue-500 bg-blue-500/5';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      }) + ' IST';
    } catch (err) {
      return 'Invalid timestamp';
    }
  };

  const formatPredictionMessage = (activity: Activity) => {
    const { message, data } = activity;
    
    // Extract confidence from data if available
    if (data.confidence) {
      const confidence = (data.confidence * 100).toFixed(1);
      return message.replace(/\(confidence: [^)]+\)/, `(${confidence}% confidence)`);
    }
    
    return message;
  };

  const formatTradeMessage = (activity: Activity) => {
    const { message, data } = activity;
    
    // Format trade message with better formatting
    if (data.price && data.quantity) {
      return message.replace(/\$([0-9,]+\.?[0-9]*)/, (match, price) => {
        return `$${parseFloat(price).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      });
    }
    
    return message;
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <div className="flex items-center space-x-2">
          <CardTitle className="text-lg font-semibold">Recent Activity</CardTitle>
          <div className="flex items-center space-x-2">
            {/* Connection status indicator */}
              <div className={cn(
              "h-2 w-2 rounded-full",
              isConnected ? "bg-green-500" : "bg-red-500"
            )} />
            <span className="text-xs text-muted-foreground">
              {isConnected ? 'Live' : 'Disconnected'}
            </span>
              </div>
            </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={reconnect}
          disabled={isConnected}
          className="h-8 w-8 p-0"
        >
          <RefreshCw className={cn("h-4 w-4", isConnected ? "" : "animate-spin")} />
        </Button>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Error state */}
        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <p className="text-sm text-red-400">{error}</p>
              </div>
            </div>
          )}

        {/* Activities list */}
        <div className="space-y-3">
            <AnimatePresence>
            {activities.length === 0 ? (
              <div className="text-center py-8">
                <Activity className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">
                  {isConnected ? 'Waiting for activities...' : 'Connecting to activity stream...'}
                </p>
              </div>
            ) : (
              activities.slice(0, 10).map((activity, index) => (
                  <motion.div
                    key={activity.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                    className={cn(
                    "p-4 rounded-lg border-l-4 transition-all duration-200",
                    getActivityColor(activity.level)
                    )}
                  >
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-0.5">
                    {getActivityIcon(activity.type, activity.level)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-foreground">
                          {activity.type === 'prediction' 
                            ? formatPredictionMessage(activity)
                            : activity.type === 'trade'
                            ? formatTradeMessage(activity)
                            : activity.message
                          }
                        </p>
                        
                        {/* Confidence badge for predictions */}
                        {activity.type === 'prediction' && activity.data.confidence && (
                          <div className="flex-shrink-0 ml-2">
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                              {(activity.data.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                      </div>
                      
                      <div className="mt-2 flex items-center text-xs text-muted-foreground">
                        <Clock className="h-3 w-3 mr-1" />
                        <span>{formatTimestamp(activity.timestamp)}</span>
                        
                        {/* Additional info for trades */}
                        {activity.type === 'trade' && activity.data.status && (
                          <span className="ml-2 px-1.5 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800">
                            {activity.data.status}
                          </span>
                        )}
                      </div>
                    </div>
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
          </div>
          
        {/* Activity summary */}
        {activities.length > 0 && (
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Showing {Math.min(activities.length, 10)} of {activities.length} activities</span>
              <span>Last 24 hours</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
  );
}
