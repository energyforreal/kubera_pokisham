/**
 * Trade History Component - Using Ant Design Table with Advanced Features
 */

'use client';

import { useEffect, useState } from 'react';
import { Table, Statistic, Row, Col, Segmented, Tag, DatePicker, Timeline, Drawer, Tabs } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ArrowUpOutlined, ArrowDownOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Column, Pie } from '@ant-design/charts';
import type { ColumnConfig, PieConfig } from '@ant-design/charts';
import { api } from '@/services/api';
import { motion } from 'framer-motion';
import { History, TrendingUp, TrendingDown, Calendar } from 'lucide-react';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

interface Trade {
  id: number;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number;
  size: number;
  pnl: number;
  timestamp: string;
  exit_timestamp?: string;
  exit_reason?: string;
}

export default function TradeHistory() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'profit' | 'loss'>('all');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeView, setActiveView] = useState<'table' | 'timeline'>('table');

  useEffect(() => {
    fetchTradeHistory();
  }, []);

  const fetchTradeHistory = async () => {
    try {
      const response = await api.getTradeHistory(100);
      setTrades(response.data.trades);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch trade history:', error);
      setLoading(false);
    }
  };

  const filteredTrades = trades.filter((trade: Trade) => {
    // Filter by profit/loss
    if (filter === 'profit' && trade.pnl <= 0) return false;
    if (filter === 'loss' && trade.pnl >= 0) return false;
    
    // Filter by date range
    if (dateRange && dateRange[0] && dateRange[1]) {
      const tradeDate = dayjs(trade.timestamp);
      if (tradeDate.isBefore(dateRange[0]) || tradeDate.isAfter(dateRange[1])) {
        return false;
      }
    }
    
    return true;
  });

  const totalPnl = filteredTrades.reduce((sum: number, t: Trade) => sum + (t.pnl || 0), 0);
  const winningTrades = filteredTrades.filter((t: Trade) => t.pnl > 0).length;
  const losingTrades = filteredTrades.filter((t: Trade) => t.pnl < 0).length;
  const winRate = filteredTrades.length > 0 ? (winningTrades / filteredTrades.length) * 100 : 0;
  const avgPnl = filteredTrades.length > 0 ? totalPnl / filteredTrades.length : 0;
  
  // Chart data
  const pnlChartData = filteredTrades.map((trade) => ({
    date: new Date(trade.timestamp).toLocaleDateString(),
    pnl: trade.pnl,
    type: trade.pnl >= 0 ? 'Profit' : 'Loss',
  }));
  
  const winLossPieData = [
    { type: 'Winning Trades', value: winningTrades },
    { type: 'Losing Trades', value: losingTrades },
  ];

  const handleRowClick = (trade: Trade) => {
    setSelectedTrade(trade);
    setDrawerOpen(true);
  };
  
  const columns: ColumnsType<Trade> = [
    {
      title: 'Date',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string) => new Date(timestamp).toLocaleString(),
      sorter: (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      width: 180,
    },
    {
      title: 'Symbol',
      dataIndex: 'symbol',
      key: 'symbol',
      filters: Array.from(new Set(trades.map(t => t.symbol))).map(symbol => ({
        text: symbol,
        value: symbol,
      })),
      onFilter: (value, record) => record.symbol === value,
      render: (symbol: string) => <strong>{symbol}</strong>,
    },
    {
      title: 'Side',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side.toLowerCase() === 'buy' ? 'green' : 'red'}>
          {side.toUpperCase()}
        </Tag>
      ),
      filters: [
        { text: 'BUY', value: 'buy' },
        { text: 'SELL', value: 'sell' },
      ],
      onFilter: (value, record) => record.side.toLowerCase() === value,
    },
    {
      title: 'Entry',
      dataIndex: 'entry_price',
      key: 'entry_price',
      render: (price: number) => `$${price?.toFixed(2) || '-'}`,
      sorter: (a, b) => (a.entry_price || 0) - (b.entry_price || 0),
    },
    {
      title: 'Exit',
      dataIndex: 'exit_price',
      key: 'exit_price',
      render: (price: number) => `$${price?.toFixed(2) || '-'}`,
      sorter: (a, b) => (a.exit_price || 0) - (b.exit_price || 0),
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => size?.toFixed(4),
      sorter: (a, b) => (a.size || 0) - (b.size || 0),
    },
    {
      title: 'P&L',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <span className={pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}>
          <strong>${pnl?.toFixed(2) || '0.00'}</strong>
        </span>
      ),
      sorter: (a, b) => (a.pnl || 0) - (b.pnl || 0),
      defaultSortOrder: 'descend',
    },
    {
      title: 'Exit Reason',
      dataIndex: 'exit_reason',
      key: 'exit_reason',
      render: (reason: string) => reason || '-',
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="trading-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5 text-accent-purple" />
            Trade History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Summary Statistics */}
          <Row gutter={16} className="mb-6">
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="Total Trades"
                value={trades.length}
                valueStyle={{ color: '#06b6d4' }}
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
                title="Avg P&L"
                value={avgPnl}
                precision={2}
                prefix="$"
                valueStyle={{ color: avgPnl >= 0 ? '#10b981' : '#ef4444' }}
              />
            </Col>
          </Row>

          {/* Filters */}
          <div className="mb-4 flex flex-wrap gap-4 items-center">
            <Segmented
              value={filter}
              onChange={(value) => setFilter(value as 'all' | 'profit' | 'loss')}
              options={[
                { label: `All (${trades.length})`, value: 'all' },
                { label: 'Profit', value: 'profit' },
                { label: 'Loss', value: 'loss' },
              ]}
            />
            
            <RangePicker
              value={dateRange}
              onChange={(dates) => setDateRange(dates)}
              format="YYYY-MM-DD"
              placeholder={['Start Date', 'End Date']}
              className="max-w-xs"
            />
            
            <Segmented
              value={activeView}
              onChange={(value) => setActiveView(value as 'table' | 'timeline')}
              options={[
                { label: 'Table View', value: 'table', icon: <History className="h-4 w-4" /> },
                { label: 'Timeline View', value: 'timeline', icon: <ClockCircleOutlined /> },
              ]}
            />
          </div>

          {/* Table View */}
          {activeView === 'table' && (
            <Table
              columns={columns}
              dataSource={filteredTrades}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total) => `Total ${total} trades`,
              }}
              scroll={{ x: 1000 }}
              size="small"
              onRow={(record) => ({
                onClick: () => handleRowClick(record),
                style: { cursor: 'pointer' },
              })}
            />
          )}

          {/* Timeline View */}
          {activeView === 'timeline' && (
            <div className="max-h-96 overflow-y-auto">
              <Timeline mode="left">
                {filteredTrades.map((trade) => (
                  <Timeline.Item
                    key={trade.id}
                    color={trade.pnl >= 0 ? 'green' : 'red'}
                    dot={trade.pnl >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                    label={new Date(trade.timestamp).toLocaleString()}
                  >
                    <div 
                      className="cursor-pointer hover:bg-dark-surface p-3 rounded-lg transition-colors"
                      onClick={() => handleRowClick(trade)}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <strong>{trade.symbol}</strong>
                        <Tag color={trade.side.toLowerCase() === 'buy' ? 'green' : 'red'}>
                          {trade.side.toUpperCase()}
                        </Tag>
                        <Badge variant={trade.pnl >= 0 ? 'success' : 'destructive'}>
                          ${trade.pnl?.toFixed(2)}
                        </Badge>
        </div>
                      <div className="text-sm text-gray-400">
                        Entry: ${trade.entry_price?.toFixed(2)} → Exit: ${trade.exit_price?.toFixed(2)}
      </div>
                      {trade.exit_reason && (
                        <div className="text-xs text-gray-500 mt-1">
                          Reason: {trade.exit_reason}
        </div>
                      )}
        </div>
                  </Timeline.Item>
                ))}
              </Timeline>
        </div>
          )}

          {/* Charts Section */}
          <div className="mt-8">
            <Tabs defaultActiveKey="pnl">
              <TabPane tab="P&L Chart" key="pnl">
                <div className="h-64">
                  <Column
                    data={pnlChartData}
                    xField="date"
                    yField="pnl"
                    seriesField="type"
                    color={(datum: { type: string }) => (datum.type === 'Profit' ? '#ff6801' : '#ef4444')}
                    columnStyle={{
                      radius: [4, 4, 0, 0],
                    }}
                    yAxis={{
                      label: {
                        formatter: (value: string) => `$${value}`,
                        style: {
                          fill: '#9ca3af',
                        },
                      },
                      grid: {
                        line: {
                          style: {
                            stroke: '#374151',
                            opacity: 0.3,
                          },
                        },
                      },
                    }}
                    xAxis={{
                      label: {
                        style: {
                          fill: '#9ca3af',
                        },
                      },
                    }}
                    tooltip={{
                      formatter: (data: { type: string; pnl: number }) => ({
                        name: data.type,
                        value: `$${data.pnl.toFixed(2)}`,
                      }),
                    }}
                  />
        </div>
              </TabPane>
              
              <TabPane tab="Win/Loss Distribution" key="distribution">
                <div className="h-64">
                  <Pie
                    data={winLossPieData}
                    angleField="value"
                    colorField="type"
                    radius={0.8}
                    innerRadius={0.6}
                    color={['#ff6801', '#ef4444']}
                    label={{
                      type: 'spider',
                      content: '{name}\n{percentage}',
                      style: {
                        fill: '#f9fafb',
                      },
                    }}
                    statistic={{
                      title: {
                        content: 'Win Rate',
                        style: {
                          color: '#9ca3af',
                          fontSize: '14px',
                        },
                      },
                      content: {
                        content: `${winRate.toFixed(1)}%`,
                        style: {
                          color: '#ff6801',
                          fontSize: '24px',
                          fontWeight: 'bold',
                        },
                      },
                    }}
                    legend={{
                      itemName: {
                        style: {
                          fill: '#f9fafb',
                        },
                      },
                    }}
                  />
      </div>
              </TabPane>
            </Tabs>
          </div>
        </CardContent>
      </Card>

      {/* Trade Details Drawer */}
      <Drawer
        title={<div className="flex items-center gap-2">
          <History className="h-5 w-5 text-accent-cyan" />
          Trade Details
        </div>}
        placement="right"
        width={500}
        onClose={() => setDrawerOpen(false)}
        open={drawerOpen}
      >
        {selectedTrade && (
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h3 className="text-2xl font-bold text-white">{selectedTrade.symbol}</h3>
                <Tag color={selectedTrade.side.toLowerCase() === 'buy' ? 'green' : 'red'} className="text-base">
                  {selectedTrade.side.toUpperCase()}
                </Tag>
              </div>
              <Badge variant={selectedTrade.pnl >= 0 ? 'success' : 'destructive'} className="text-lg px-3 py-1">
                {selectedTrade.pnl >= 0 ? '+' : ''}${selectedTrade.pnl?.toFixed(2)}
              </Badge>
            </div>

            {/* Trade Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-400">Entry Price</p>
                <p className="text-xl font-semibold text-white">${selectedTrade.entry_price?.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Exit Price</p>
                <p className="text-xl font-semibold text-white">${selectedTrade.exit_price?.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Position Size</p>
                <p className="text-xl font-semibold text-white">{selectedTrade.size?.toFixed(4)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">P&L %</p>
                <p className={`text-xl font-semibold ${selectedTrade.pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                  {((selectedTrade.pnl / (selectedTrade.entry_price * selectedTrade.size)) * 100).toFixed(2)}%
                </p>
              </div>
            </div>

            {/* Timeline */}
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Timeline
              </h4>
              <Timeline>
                <Timeline.Item color="green">
                  <p className="text-white font-medium">Trade Opened</p>
                  <p className="text-sm text-gray-400">{new Date(selectedTrade.timestamp).toLocaleString()}</p>
                </Timeline.Item>
                {selectedTrade.exit_timestamp && (
                  <Timeline.Item color={selectedTrade.pnl >= 0 ? 'green' : 'red'}>
                    <p className="text-white font-medium">Trade Closed</p>
                    <p className="text-sm text-gray-400">{new Date(selectedTrade.exit_timestamp).toLocaleString()}</p>
                  </Timeline.Item>
                )}
              </Timeline>
            </div>

            {/* Exit Reason */}
            {selectedTrade.exit_reason && (
              <div className="p-4 bg-dark-surface rounded-lg border border-dark-border">
                <p className="text-sm text-gray-400 mb-1">Exit Reason</p>
                <p className="text-white">{selectedTrade.exit_reason}</p>
              </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <Statistic
                title="Duration"
                value={selectedTrade.exit_timestamp 
                  ? Math.round((new Date(selectedTrade.exit_timestamp).getTime() - new Date(selectedTrade.timestamp).getTime()) / 60000)
                  : 0}
                suffix="min"
                valueStyle={{ fontSize: '16px', color: '#06b6d4' }}
              />
              <Statistic
                title="Cost Basis"
                value={(selectedTrade.entry_price * selectedTrade.size).toFixed(2)}
                prefix="$"
                valueStyle={{ fontSize: '16px', color: '#8b5cf6' }}
              />
              <Statistic
                title="ROI"
                value={((selectedTrade.pnl / (selectedTrade.entry_price * selectedTrade.size)) * 100).toFixed(1)}
                suffix="%"
                valueStyle={{ 
                  fontSize: '16px', 
                  color: selectedTrade.pnl >= 0 ? '#10b981' : '#ef4444' 
                }}
              />
            </div>
          </div>
        )}
      </Drawer>
    </motion.div>
  );
}

