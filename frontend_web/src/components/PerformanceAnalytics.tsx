/**
 * Performance Analytics Component - Detailed metrics with Ant Design
 */
'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Row, Col, Statistic, Tabs, Empty, Spin } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { Line, Column } from '@ant-design/charts';
import type { LineConfig, ColumnConfig } from '@ant-design/charts';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, TrendingDown, DollarSign, Percent } from 'lucide-react';
import { api } from '@/services/api';
import useSWR from 'swr';

const { TabPane } = Tabs;

export default function PerformanceAnalytics() {
  const [activeTab, setActiveTab] = useState('overview');
  
  // Fetch analytics data
  const { data: analytics, error, isLoading } = useSWR(
    '/api/v1/analytics/daily',
    async () => {
      try {
        const response = await api.getDailyAnalytics();
        return response.data;
      } catch (error) {
        console.error('Analytics fetch error:', error);
        return null;
      }
    },
    { refreshInterval: 30000 }
  );

  const { data: tradeHistory } = useSWR(
    '/api/v1/trades/history',
    async () => {
      try {
        const response = await api.getTradeHistory(100);
        return response.data.trades || [];
      } catch (error) {
        console.error('Trade history fetch error:', error);
        return [];
      }
    },
    { refreshInterval: 60000 }
  );

  // Calculate metrics from trade history
  const totalTrades = tradeHistory?.length || 0;
  const winningTrades = tradeHistory?.filter((t: any) => t.pnl > 0).length || 0;
  const losingTrades = tradeHistory?.filter((t: any) => t.pnl < 0).length || 0;
  const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;
  const totalPnl = tradeHistory?.reduce((sum: number, t: any) => sum + (t.pnl || 0), 0) || 0;
  const avgWin = winningTrades > 0 
    ? tradeHistory?.filter((t: any) => t.pnl > 0).reduce((sum: number, t: any) => sum + t.pnl, 0) / winningTrades 
    : 0;
  const avgLoss = losingTrades > 0
    ? Math.abs(tradeHistory?.filter((t: any) => t.pnl < 0).reduce((sum: number, t: any) => sum + t.pnl, 0) / losingTrades)
    : 0;
  const profitFactor = avgLoss > 0 ? avgWin / avgLoss : 0;

  // Prepare chart data
  const equityCurveData = tradeHistory?.reduce((acc: any[], trade: any, idx: number) => {
    const prevEquity = idx > 0 ? acc[idx - 1].equity : 10000;
    acc.push({
      date: new Date(trade.timestamp).toLocaleDateString(),
      equity: prevEquity + (trade.pnl || 0),
      pnl: trade.pnl || 0,
    });
    return acc;
  }, []) || [];

  // Monthly P&L data
  const monthlyPnlData = tradeHistory?.reduce((acc: any[], trade: any) => {
    const month = new Date(trade.timestamp).toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    const existing = acc.find(item => item.month === month);
    if (existing) {
      existing.pnl += trade.pnl || 0;
    } else {
      acc.push({ month, pnl: trade.pnl || 0 });
    }
    return acc;
  }, []) || [];

  const equityChartConfig: LineConfig = {
    data: equityCurveData,
    xField: 'date',
    yField: 'equity',
    smooth: true,
    color: '#ff6801',
    lineStyle: {
      lineWidth: 2,
    },
    point: {
      size: 3,
      shape: 'circle',
    },
    yAxis: {
      label: {
        formatter: (v: string) => `$${parseFloat(v).toFixed(0)}`,
        style: { fill: '#9ca3af' },
      },
      grid: {
        line: {
          style: { stroke: '#374151', opacity: 0.3 },
        },
      },
    },
    xAxis: {
      label: {
        style: { fill: '#9ca3af' },
      },
    },
    tooltip: {
      formatter: (datum: any) => ({
        name: 'Equity',
        value: `$${datum.equity.toFixed(2)}`,
      }),
    },
  };

  const monthlyPnlConfig: ColumnConfig = {
    data: monthlyPnlData,
    xField: 'month',
    yField: 'pnl',
    color: (datum: any) => (datum.pnl >= 0 ? '#10b981' : '#ef4444'),
    columnStyle: {
      radius: [4, 4, 0, 0],
    },
    yAxis: {
      label: {
        formatter: (v: string) => `$${parseFloat(v).toFixed(0)}`,
        style: { fill: '#9ca3af' },
      },
      grid: {
        line: {
          style: { stroke: '#374151', opacity: 0.3 },
        },
      },
    },
    xAxis: {
      label: {
        style: { fill: '#9ca3af' },
      },
    },
    tooltip: {
      formatter: (datum: any) => ({
        name: 'P&L',
        value: `$${datum.pnl.toFixed(2)}`,
      }),
    },
  };

  if (isLoading) {
    return (
      <Card className="trading-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-accent-purple" />
            Performance Analytics
          </CardTitle>
        </CardHeader>
        <CardContent className="py-16 text-center">
          <Spin size="large" />
          <p className="text-gray-400 mt-4">Loading analytics...</p>
        </CardContent>
      </Card>
    );
  }

  if (!analytics && !tradeHistory?.length) {
    return (
      <Card className="trading-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-accent-purple" />
            Performance Analytics
          </CardTitle>
        </CardHeader>
        <CardContent className="py-16">
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="No analytics data available yet. Start trading to see performance metrics."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="trading-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-accent-purple" />
            Performance Analytics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            <TabPane tab="Overview" key="overview">
              {/* Key Metrics */}
              <Row gutter={[16, 16]} className="mb-6">
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="Total Trades"
                    value={totalTrades}
                    valueStyle={{ color: '#06b6d4' }}
                    prefix={<BarChart3 className="h-4 w-4" />}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="Win Rate"
                    value={winRate}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: winRate >= 50 ? '#10b981' : '#ef4444' }}
                    prefix={winRate >= 50 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="Total P&L"
                    value={totalPnl}
                    precision={2}
                    prefix="$"
                    valueStyle={{ color: totalPnl >= 0 ? '#10b981' : '#ef4444' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="Profit Factor"
                    value={profitFactor}
                    precision={2}
                    valueStyle={{ color: profitFactor >= 1 ? '#10b981' : '#ef4444' }}
                  />
                </Col>
              </Row>

              {/* Risk Metrics */}
              {analytics?.risk_metrics && (
                <>
                  <h3 className="text-lg font-semibold text-white mb-4">Risk Metrics</h3>
                  <Row gutter={[16, 16]} className="mb-6">
                    <Col xs={24} sm={12} md={6}>
                      <Statistic
                        title="Sharpe Ratio"
                        value={analytics.risk_metrics.sharpe_ratio || 0}
                        precision={2}
                        valueStyle={{ color: '#8b5cf6' }}
                      />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                      <Statistic
                        title="Sortino Ratio"
                        value={analytics.risk_metrics.sortino_ratio || 0}
                        precision={2}
                        valueStyle={{ color: '#8b5cf6' }}
                      />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                      <Statistic
                        title="Max Drawdown"
                        value={analytics.risk_metrics.max_drawdown ? analytics.risk_metrics.max_drawdown * 100 : 0}
                        precision={1}
                        suffix="%"
                        valueStyle={{ color: '#ef4444' }}
                        prefix={<ArrowDownOutlined />}
                      />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                      <Statistic
                        title="Avg Win / Avg Loss"
                        value={avgWin}
                        precision={2}
                        prefix="$"
                        suffix={` / $${avgLoss.toFixed(2)}`}
                        valueStyle={{ color: '#10b981' }}
                      />
                    </Col>
                  </Row>
                </>
              )}
            </TabPane>

            <TabPane tab="Equity Curve" key="equity">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white mb-2">Equity Growth Over Time</h3>
                <p className="text-sm text-gray-400">Track your account balance progression</p>
              </div>
              {equityCurveData.length > 0 ? (
                <div className="h-96">
                  <Line {...equityChartConfig} />
                </div>
              ) : (
                <Empty description="No equity data available" />
              )}
            </TabPane>

            <TabPane tab="Monthly P&L" key="monthly">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white mb-2">Monthly Profit & Loss</h3>
                <p className="text-sm text-gray-400">Monthly performance breakdown</p>
              </div>
              {monthlyPnlData.length > 0 ? (
                <div className="h-96">
                  <Column {...monthlyPnlConfig} />
                </div>
              ) : (
                <Empty description="No monthly data available" />
              )}
            </TabPane>

            <TabPane tab="Statistics" key="stats">
              <Row gutter={[16, 16]}>
                <Col xs={24} md={12}>
                  <div className="p-4 bg-dark-surface rounded-lg border border-dark-border">
                    <h4 className="text-sm text-gray-400 mb-4">Trading Performance</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-white">Winning Trades:</span>
                        <span className="text-accent-green font-semibold">{winningTrades}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-white">Losing Trades:</span>
                        <span className="text-accent-red font-semibold">{losingTrades}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-white">Average Win:</span>
                        <span className="text-accent-green font-semibold">${avgWin.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-white">Average Loss:</span>
                        <span className="text-accent-red font-semibold">${avgLoss.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-white">Profit Factor:</span>
                        <span className={profitFactor >= 1 ? 'text-accent-green' : 'text-accent-red'}>
                          {profitFactor.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                </Col>
                <Col xs={24} md={12}>
                  <div className="p-4 bg-dark-surface rounded-lg border border-dark-border">
                    <h4 className="text-sm text-gray-400 mb-4">Risk Analysis</h4>
                    <div className="space-y-3">
                      {analytics?.risk_metrics ? (
                        <>
                          <div className="flex justify-between items-center">
                            <span className="text-white">Sharpe Ratio:</span>
                            <span className="text-accent-purple font-semibold">
                              {analytics.risk_metrics.sharpe_ratio?.toFixed(2) || 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-white">Sortino Ratio:</span>
                            <span className="text-accent-purple font-semibold">
                              {analytics.risk_metrics.sortino_ratio?.toFixed(2) || 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-white">Max Drawdown:</span>
                            <span className="text-accent-red font-semibold">
                              {analytics.risk_metrics.max_drawdown 
                                ? `${(analytics.risk_metrics.max_drawdown * 100).toFixed(2)}%` 
                                : 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-white">Win Rate:</span>
                            <span className={winRate >= 50 ? 'text-accent-green' : 'text-accent-red'}>
                              {winRate.toFixed(1)}%
                            </span>
                          </div>
                        </>
                      ) : (
                        <Empty description="No risk metrics available" />
                      )}
                    </div>
                  </div>
                </Col>
              </Row>
            </TabPane>
          </Tabs>
        </CardContent>
      </Card>
    </motion.div>
  );
}
