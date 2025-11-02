/**
 * Trading Simulator Component - Backtest strategies
 */
'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PlayCircle } from 'lucide-react';

export default function TradingSimulator() {
  return (
    <Card className="trading-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PlayCircle className="h-5 w-5 text-accent-cyan" />
          Trading Simulator
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-center py-16">
          <PlayCircle className="h-16 w-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg mb-2">Trading Simulator</p>
          <p className="text-gray-500 text-sm">
            Backtest strategies with historical data
          </p>
          <p className="text-gray-600 text-xs mt-4">
            Coming Soon - Advanced backtesting features
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
