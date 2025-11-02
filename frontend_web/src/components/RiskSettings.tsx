/**
 * Risk Settings Panel - Using Ant Design Form
 */

'use client';

import { useEffect, useState } from 'react';
import { Form, InputNumber, Slider, Button, Alert, Row, Col, Divider } from 'antd';
import { SaveOutlined, EditOutlined, CloseOutlined } from '@ant-design/icons';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import { Settings, ShieldAlert } from 'lucide-react';
import { api } from '@/services/api';
import toast from 'react-hot-toast';

export default function RiskSettings() {
  const [form] = Form.useForm();
  const [settings, setSettings] = useState<any>(null);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await api.getRiskSettings();
      setSettings(response.data);
      
      // Populate form
      form.setFieldsValue({
        max_daily_loss_percent: response.data.risk_management.max_daily_loss_percent,
        max_drawdown_percent: response.data.risk_management.max_drawdown_percent,
        max_consecutive_losses: response.data.risk_management.max_consecutive_losses,
        stop_loss_atr_multiplier: response.data.risk_management.stop_loss_atr_multiplier,
        take_profit_risk_reward: response.data.risk_management.take_profit_risk_reward,
        min_confidence: response.data.signal_filters.min_confidence,
      });
      
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
      toast.error('Failed to fetch risk settings');
      setLoading(false);
    }
  };

  const handleSave = async (values: any) => {
    setSaving(true);
    try {
      await api.updateRiskSettings(values);
      toast.success('Settings updated! Please restart the backend for changes to take effect.');
      setEditing(false);
      fetchSettings();
    } catch (error: any) {
      toast.error(`Update failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    setEditing(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="trading-card">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-accent-orange" />
              Risk Management Settings
              <Badge variant="warning">Critical</Badge>
            </CardTitle>
            {!editing ? (
              <Button
                type="primary"
                icon={<EditOutlined />}
                onClick={() => setEditing(true)}
              >
                Edit Settings
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button
                  icon={<CloseOutlined />}
                  onClick={handleCancel}
                >
                  Cancel
                </Button>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  loading={saving}
                  onClick={() => form.submit()}
                >
                  Save Changes
                </Button>
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSave}
            disabled={!editing}
          >
            <Divider orientation="left">Loss Protection</Divider>
            <Row gutter={24}>
              <Col xs={24} md={12}>
                <Form.Item
                  name="max_daily_loss_percent"
                  label="Max Daily Loss (%)"
                  tooltip="Maximum loss allowed in a single day"
                  rules={[
                    { required: true, message: 'Required' },
                    { type: 'number', min: 0, max: 100, message: 'Must be between 0-100' },
                  ]}
                >
                  <InputNumber
                    className="w-full"
                    step={0.5}
                    formatter={(value) => `${value}%`}
                    parser={(value) => value?.replace('%', '') as any}
                  />
                </Form.Item>
              </Col>

              <Col xs={24} md={12}>
                <Form.Item
                  name="max_drawdown_percent"
                  label="Max Drawdown (%)"
                  tooltip="Maximum drawdown from peak before circuit breaker triggers"
                  rules={[
                    { required: true, message: 'Required' },
                    { type: 'number', min: 0, max: 100, message: 'Must be between 0-100' },
                  ]}
                >
                  <InputNumber
                    className="w-full"
                    step={0.5}
                    formatter={(value) => `${value}%`}
                    parser={(value) => value?.replace('%', '') as any}
                  />
                </Form.Item>
              </Col>

              <Col xs={24} md={12}>
                <Form.Item
                  name="max_consecutive_losses"
                  label="Max Consecutive Losses"
                  tooltip="Triggers circuit breaker after this many consecutive losses"
                  rules={[
                    { required: true, message: 'Required' },
                    { type: 'number', min: 1, max: 20, message: 'Must be between 1-20' },
                  ]}
                >
                  <InputNumber className="w-full" step={1} />
                </Form.Item>
              </Col>
            </Row>

            <Divider orientation="left">Trade Parameters</Divider>
            <Row gutter={24}>
              <Col xs={24} md={12}>
                <Form.Item
                  name="stop_loss_atr_multiplier"
                  label="Stop Loss ATR Multiplier"
                  tooltip="Stop loss distance in ATR multiples"
                  rules={[
                    { required: true, message: 'Required' },
                    { type: 'number', min: 0.5, max: 10, message: 'Must be between 0.5-10' },
                  ]}
                >
                  <InputNumber
                    className="w-full"
                    step={0.1}
                    formatter={(value) => `${value}x`}
                    parser={(value) => value?.replace('x', '') as any}
                  />
                </Form.Item>
              </Col>

              <Col xs={24} md={12}>
                <Form.Item
                  name="take_profit_risk_reward"
                  label="Take Profit Risk/Reward Ratio"
                  tooltip="Risk/reward ratio for take profit targets"
                  rules={[
                    { required: true, message: 'Required' },
                    { type: 'number', min: 0.5, max: 10, message: 'Must be between 0.5-10' },
                  ]}
                >
                  <InputNumber
                    className="w-full"
                    step={0.1}
                    formatter={(value) => `${value}:1`}
                    parser={(value) => value?.replace(':1', '') as any}
                  />
                </Form.Item>
              </Col>

              <Col xs={24} md={12}>
                <Form.Item
                  name="min_confidence"
                  label="Minimum Signal Confidence"
                  tooltip="Minimum confidence required for signal execution"
                  rules={[
                    { required: true, message: 'Required' },
                    { type: 'number', min: 0.5, max: 1, message: 'Must be between 0.5-1' },
                  ]}
                >
                  <Slider
                    min={0.5}
                    max={1}
                    step={0.05}
                    marks={{
                      0.5: '50%',
                      0.65: '65%',
                      0.75: '75%',
                      1: '100%',
                    }}
                    tooltip={{ formatter: (value) => `${((value || 0) * 100).toFixed(0)}%` }}
                  />
                </Form.Item>
              </Col>
            </Row>
          </Form>

          <Alert
            message="Important"
            description="Changes to these settings require restarting the backend API to take effect."
            type="warning"
            icon={<ShieldAlert className="h-4 w-4" />}
            showIcon
            className="mt-6"
          />
        </CardContent>
      </Card>
    </motion.div>
  );
}

