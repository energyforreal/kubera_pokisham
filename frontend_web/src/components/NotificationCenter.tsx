/**
 * Notification Center Component - Real-time trade alerts and system notifications
 */
'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Bell, TrendingUp, TrendingDown, Target, AlertTriangle, Info, X, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { tradingWs } from '@/services/api';
import { cn } from '@/lib/utils';

interface Notification {
  id: string;
  type: 'trade' | 'signal' | 'position_closed' | 'position_updated' | 'alert' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  data?: any;
  read: boolean;
  level: 'success' | 'info' | 'warning' | 'error';
}

export default function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  useEffect(() => {
    // Listen to WebSocket events for real-time notifications
    
    tradingWs.on('trade', (data: any) => {
      addNotification({
        type: 'trade',
        title: 'Trade Executed',
        message: `${data.side || 'Trade'} ${data.symbol || ''} at $${data.price?.toFixed(2) || 'N/A'}`,
        data,
        level: data.status === 'filled' ? 'success' : 'info'
      });
    });

    tradingWs.on('signal', (data: any) => {
      addNotification({
        type: 'signal',
        title: 'New AI Signal',
        message: `${data.prediction || 'Signal'} for ${data.symbol || ''} with ${(data.confidence * 100)?.toFixed(1) || '0'}% confidence`,
        data,
        level: data.is_actionable ? 'success' : 'info'
      });
    });

    tradingWs.on('position_closed', (data: any) => {
      const pnl = data.pnl || 0;
      addNotification({
        type: 'position_closed',
        title: 'Position Closed',
        message: `${data.symbol || 'Position'} closed with ${pnl >= 0 ? 'profit' : 'loss'}: $${pnl.toFixed(2)}`,
        data,
        level: pnl >= 0 ? 'success' : 'error'
      });
    });

    tradingWs.on('position_updated', (data: any) => {
      addNotification({
        type: 'position_updated',
        title: 'Position Updated',
        message: `${data.symbol || 'Position'} stop-loss/take-profit updated`,
        data,
        level: 'info'
      });
    });

    tradingWs.on('portfolio_update', (data: any) => {
      addNotification({
        type: 'info',
        title: 'Portfolio Updated',
        message: `Balance: $${data.balance?.toFixed(2) || 'N/A'}, Equity: $${data.equity?.toFixed(2) || 'N/A'}`,
        data,
        level: 'info'
      });
    });

  }, []);

  const addNotification = (notif: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notif,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      read: false
    };
    
    setNotifications(prev => [newNotification, ...prev].slice(0, 100)); // Keep last 100
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'trade': return <TrendingUp className="h-4 w-4" />;
      case 'signal': return <Target className="h-4 w-4" />;
      case 'position_closed': return <TrendingDown className="h-4 w-4" />;
      case 'alert': return <AlertTriangle className="h-4 w-4" />;
      default: return <Info className="h-4 w-4" />;
    }
  };

  const getLevelColor = (level: string, read: boolean) => {
    const baseOpacity = read ? '20' : '30';
    switch (level) {
      case 'success': return `bg-green-500/${baseOpacity} border-green-500/${baseOpacity} text-green-400`;
      case 'error': return `bg-red-500/${baseOpacity} border-red-500/${baseOpacity} text-red-400`;
      case 'warning': return `bg-yellow-500/${baseOpacity} border-yellow-500/${baseOpacity} text-yellow-400`;
      default: return `bg-blue-500/${baseOpacity} border-blue-500/${baseOpacity} text-blue-400`;
    }
  };

  const filteredNotifications = filter === 'unread' 
    ? notifications.filter(n => !n.read)
    : notifications;

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <Card className="trading-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-accent-orange" />
            Notification Center
            {unreadCount > 0 && (
              <motion.span 
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="px-2 py-1 bg-accent-orange text-white rounded-full text-xs font-bold"
              >
                {unreadCount}
              </motion.span>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            <div className="flex bg-dark-surface rounded-lg p-1">
              <Button
                variant={filter === 'all' ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilter('all')}
                className="text-xs px-3"
              >
                All ({notifications.length})
              </Button>
              <Button
                variant={filter === 'unread' ? "default" : "ghost"}
                size="sm"
                onClick={() => setFilter('unread')}
                className="text-xs px-3"
              >
                Unread ({unreadCount})
              </Button>
            </div>
            {notifications.length > 0 && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={markAllAsRead}
                  className="text-xs"
                >
                  Mark All Read
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearAll}
                  className="text-xs"
                >
                  <Trash2 className="h-3 w-3 mr-1" />
                  Clear All
                </Button>
              </>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {filteredNotifications.length === 0 ? (
          <div className="text-center py-16">
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Bell className="h-16 w-16 text-gray-600 mx-auto mb-4" />
            </motion.div>
            <p className="text-gray-400 text-lg mb-2">
              {filter === 'unread' ? 'No Unread Notifications' : 'No Notifications'}
            </p>
            <p className="text-gray-500 text-sm">
              Real-time alerts will appear here when the bot takes actions
            </p>
            <p className="text-gray-600 text-xs mt-4">
              WebSocket connected • Listening for events
            </p>
          </div>
        ) : (
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            <AnimatePresence>
              {filteredNotifications.map((notif, index) => (
                <motion.div
                  key={notif.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  className={cn(
                    "p-4 rounded-lg border-l-4 cursor-pointer transition-all hover:shadow-lg",
                    getLevelColor(notif.level, notif.read),
                    notif.read ? 'opacity-60' : 'opacity-100'
                  )}
                  onClick={() => markAsRead(notif.id)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1">
                      <div className={cn(
                        "p-2 rounded-lg",
                        notif.level === 'success' ? 'bg-green-500/20' :
                        notif.level === 'error' ? 'bg-red-500/20' :
                        notif.level === 'warning' ? 'bg-yellow-500/20' :
                        'bg-blue-500/20'
                      )}>
                        {getNotificationIcon(notif.type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-white text-sm">{notif.title}</h4>
                          {!notif.read && (
                            <div className="w-2 h-2 bg-accent-orange rounded-full animate-pulse"></div>
                          )}
                        </div>
                        <p className="text-sm text-gray-300 mt-1">{notif.message}</p>
                        <p className="text-xs text-gray-500 mt-2">
                          {notif.timestamp.toLocaleTimeString()} • {notif.timestamp.toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteNotification(notif.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
