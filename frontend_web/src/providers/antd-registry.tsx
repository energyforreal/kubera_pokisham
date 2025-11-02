'use client';

import React from 'react';
import { AntdRegistry } from '@ant-design/nextjs-registry';
import { ConfigProvider, theme } from 'antd';

export function AntdProvider({ children }: { children: React.ReactNode }) {
  return (
    <AntdRegistry>
      <ConfigProvider
        theme={{
          algorithm: theme.darkAlgorithm,
          token: {
            colorPrimary: '#ff6801', // Primary gradient orange
            colorSuccess: '#10b981',
            colorWarning: '#FDEE00', // Secondary gradient yellow
            colorError: '#ef4444',
            colorInfo: '#ffb347', // Light orange from gradient
            colorLink: '#ff7518', // Bright orange from secondary gradient
            colorBgContainer: '#1f2937',
            colorBgElevated: '#111827',
            colorBorder: '#374151',
            colorText: '#f9fafb',
            colorTextSecondary: '#9ca3af',
            colorTextTertiary: '#6b7280',
            borderRadius: 8,
            fontSize: 14,
          },
          components: {
            Button: {
              primaryShadow: '0 2px 8px rgba(255, 104, 1, 0.3)',
              controlHeight: 40,
              colorPrimary: '#ff6801',
              colorPrimaryHover: '#ffb347',
              colorPrimaryActive: '#ff7518',
            },
            Input: {
              controlHeight: 40,
              activeBorderColor: '#ff6801',
              hoverBorderColor: '#ffb347',
            },
            Select: {
              controlHeight: 40,
              colorPrimary: '#ff6801',
              colorPrimaryHover: '#ffb347',
            },
            Table: {
              headerBg: '#111827',
              headerColor: '#9ca3af',
              rowHoverBg: '#374151',
            },
            Statistic: {
              contentFontSize: 24,
            },
          },
        }}
      >
        {children}
      </ConfigProvider>
    </AntdRegistry>
  );
}

