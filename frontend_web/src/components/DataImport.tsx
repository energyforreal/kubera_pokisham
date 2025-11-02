/**
 * Data Import Component - CSV Upload for Trade Data
 */

'use client';

import { useState } from 'react';
import { Upload, Button, message, Progress, Alert, Table } from 'antd';
import type { UploadProps } from 'antd';
import { InboxOutlined, UploadOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import { Upload as UploadIcon, FileText, CheckCircle } from 'lucide-react';

const { Dragger } = Upload;

interface ParsedTrade {
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number;
  size: number;
  pnl: number;
  timestamp: string;
}

export default function DataImport() {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [parsedData, setParsedData] = useState<ParsedTrade[]>([]);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');

  const parseCSV = (file: File): Promise<ParsedTrade[]> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const text = e.target?.result as string;
          const lines = text.split('\n').filter(line => line.trim());
          const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
          
          const trades: ParsedTrade[] = [];
          
          for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(',');
            const trade: any = {};
            
            headers.forEach((header, index) => {
              trade[header] = values[index]?.trim();
            });
            
            // Map to expected format
            trades.push({
              symbol: trade.symbol || trade.pair || 'UNKNOWN',
              side: trade.side || trade.type || 'BUY',
              entry_price: parseFloat(trade.entry_price || trade.entry || '0'),
              exit_price: parseFloat(trade.exit_price || trade.exit || '0'),
              size: parseFloat(trade.size || trade.quantity || trade.amount || '0'),
              pnl: parseFloat(trade.pnl || trade.profit || trade.pl || '0'),
              timestamp: trade.timestamp || trade.date || trade.time || new Date().toISOString(),
            });
          }
          
          resolve(trades);
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  };

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.csv',
    beforeUpload: async (file) => {
      const isCSV = file.type === 'text/csv' || file.name.endsWith('.csv');
      if (!isCSV) {
        message.error('You can only upload CSV files!');
        return Upload.LIST_IGNORE;
      }

      const isLt5M = file.size / 1024 / 1024 < 5;
      if (!isLt5M) {
        message.error('CSV must be smaller than 5MB!');
        return Upload.LIST_IGNORE;
      }

      setUploading(true);
      setUploadStatus('uploading');
      setUploadProgress(0);

      try {
        // Simulate upload progress
        const progressInterval = setInterval(() => {
          setUploadProgress((prev) => {
            if (prev >= 90) {
              clearInterval(progressInterval);
              return 90;
            }
            return prev + 10;
          });
        }, 200);

        const parsed = await parseCSV(file);
        
        clearInterval(progressInterval);
        setUploadProgress(100);
        setParsedData(parsed);
        setUploadStatus('success');
        message.success(`Successfully parsed ${parsed.length} trades from CSV`);
      } catch (error) {
        setUploadStatus('error');
        message.error('Failed to parse CSV file. Please check the format.');
      } finally {
        setUploading(false);
      }

      return false; // Prevent auto upload
    },
    onDrop(e) {
      console.log('Dropped files', e.dataTransfer.files);
    },
  };

  const columns = [
    {
      title: 'Symbol',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: 'Side',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Badge variant={side.toUpperCase() === 'BUY' ? 'success' : 'destructive'}>
          {side.toUpperCase()}
        </Badge>
      ),
    },
    {
      title: 'Entry',
      dataIndex: 'entry_price',
      key: 'entry_price',
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: 'Exit',
      dataIndex: 'exit_price',
      key: 'exit_price',
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => size.toFixed(4),
    },
    {
      title: 'P&L',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <span className={pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}>
          ${pnl.toFixed(2)}
        </span>
      ),
    },
  ];

  const handleImport = async () => {
    // TODO: Send parsedData to backend API
    message.success('Import functionality coming soon!');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="trading-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UploadIcon className="h-5 w-5 text-accent-purple" />
            Import Trade Data
            <Badge variant="info">CSV</Badge>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Instructions */}
          <Alert
            message="CSV Format Requirements"
            description={
              <div className="text-sm">
                <p className="mb-2">Your CSV file should include the following columns:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li><strong>symbol</strong> or <strong>pair</strong>: Trading pair (e.g., BTCUSD)</li>
                  <li><strong>side</strong> or <strong>type</strong>: BUY or SELL</li>
                  <li><strong>entry_price</strong> or <strong>entry</strong>: Entry price</li>
                  <li><strong>exit_price</strong> or <strong>exit</strong>: Exit price</li>
                  <li><strong>size</strong>, <strong>quantity</strong>, or <strong>amount</strong>: Position size</li>
                  <li><strong>pnl</strong>, <strong>profit</strong>, or <strong>pl</strong>: Profit/Loss</li>
                  <li><strong>timestamp</strong>, <strong>date</strong>, or <strong>time</strong>: Trade date/time</li>
                </ul>
              </div>
            }
            type="info"
            showIcon
            icon={<FileText className="h-4 w-4" />}
          />

          {/* Upload Area */}
          <Dragger {...uploadProps} disabled={uploading}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ color: '#06b6d4', fontSize: 48 }} />
            </p>
            <p className="ant-upload-text text-white">Click or drag CSV file to this area to upload</p>
            <p className="ant-upload-hint text-gray-400">
              Support for a single upload. Maximum file size: 5MB
            </p>
          </Dragger>

          {/* Upload Progress */}
          {uploading && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Processing CSV...</span>
                <span className="text-sm text-white">{uploadProgress}%</span>
              </div>
              <Progress
                percent={uploadProgress}
                status="active"
                strokeColor="#06b6d4"
              />
            </div>
          )}

          {/* Success Status */}
          {uploadStatus === 'success' && parsedData.length > 0 && (
            <Alert
              message={
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4" />
                  <span>Successfully Parsed {parsedData.length} Trades</span>
                </div>
              }
              description="Review the data below and click Import to add these trades to your history."
              type="success"
              showIcon
              icon={<CheckCircleOutlined />}
            />
          )}

          {/* Preview Table */}
          {parsedData.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Preview Data</h3>
                <Button
                  type="primary"
                  icon={<UploadOutlined />}
                  onClick={handleImport}
                  size="large"
                >
                  Import {parsedData.length} Trades
                </Button>
              </div>

              <Table
                columns={columns}
                dataSource={parsedData}
                rowKey={(record, index) => index?.toString() || '0'}
                pagination={{ pageSize: 10 }}
                scroll={{ x: 800 }}
                size="small"
              />
            </div>
          )}

          {/* Sample CSV Download */}
          <div className="pt-4 border-t border-dark-border">
            <p className="text-sm text-gray-400 mb-2">Need a template?</p>
            <Button
              type="link"
              icon={<UploadOutlined />}
              onClick={() => {
                const sampleCSV = `symbol,side,entry_price,exit_price,size,pnl,timestamp
BTCUSD,BUY,45000.00,46000.00,0.1,100.00,2024-01-15T10:30:00Z
BTCUSD,SELL,45500.00,44500.00,0.05,-50.00,2024-01-15T14:20:00Z`;
                
                const blob = new Blob([sampleCSV], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'sample_trades.csv';
                a.click();
                window.URL.revokeObjectURL(url);
                
                message.success('Sample CSV downloaded!');
              }}
            >
              Download Sample CSV
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

