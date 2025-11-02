# TypeScript/Frontend Cursor Rules

## Overview
Guidelines for TypeScript and frontend development in the Trading Agent project, covering Next.js, React, TypeScript patterns, and API integration.

## TypeScript Configuration

### Strict Mode
- Always use TypeScript strict mode (`"strict": true` in tsconfig.json)
- Enable `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`
- Use consistent casing in file names (`"forceConsistentCasingInFileNames": true`)
- Enable incremental compilation for faster builds

### Type Definitions
- Define types for all API responses
- Use interfaces for object shapes
- Use type aliases for unions and intersections
- Avoid `any` - use `unknown` if type is truly unknown

```typescript
// Good: Proper type definitions
interface TradeResponse {
  status: 'filled' | 'rejected' | 'pending';
  message: string;
  data?: TradeData;
}

interface TradeData {
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  pnl?: number;
}

// Bad: Using any
function processTrade(data: any) { ... }
```

## React/Next.js Patterns

### Component Structure
- Use functional components with hooks
- Use TypeScript interfaces for props
- Extract custom hooks for reusable logic
- Keep components focused and single-purpose

```typescript
import React, { useState, useEffect } from 'react';

interface PortfolioStatusProps {
  initialBalance: number;
  refreshInterval?: number;
}

export function PortfolioStatus({ 
  initialBalance, 
  refreshInterval = 5000 
}: PortfolioStatusProps) {
  const [balance, setBalance] = useState(initialBalance);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    const interval = setInterval(async () => {
      setLoading(true);
      try {
        const data = await fetchPortfolioStatus();
        setBalance(data.balance);
      } catch (error) {
        console.error('Failed to fetch portfolio status:', error);
      } finally {
        setLoading(false);
      }
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [refreshInterval]);
  
  return (
    <div>
      <p>Balance: ${balance.toFixed(2)}</p>
      {loading && <span>Loading...</span>}
    </div>
  );
}
```

### Custom Hooks
- Prefix custom hooks with `use`
- Return objects with named properties
- Include proper TypeScript types
- Handle loading and error states

```typescript
interface UsePortfolioStatusResult {
  balance: number;
  equity: number;
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

export function usePortfolioStatus(): UsePortfolioStatusResult {
  const [balance, setBalance] = useState(0);
  const [equity, setEquity] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/portfolio/status');
      if (!response.ok) throw new Error('Failed to fetch portfolio');
      const data = await response.json();
      setBalance(data.balance);
      setEquity(data.equity);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, []);
  
  return { balance, equity, loading, error, refresh };
}
```

### State Management
- Use React hooks (useState, useReducer) for local state
- Use Context API for shared state
- Use Zustand for complex global state (if needed)
- Avoid prop drilling - use context or state management

### Next.js App Router
- Use App Router directory structure (`app/` directory)
- Use Server Components by default
- Use Client Components only when needed (`'use client'`)
- Use Route Handlers for API endpoints when needed
- Use proper metadata exports for SEO

```typescript
// app/dashboard/page.tsx (Server Component by default)
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Trading Dashboard',
  description: 'AI Trading Agent Dashboard',
};

export default async function DashboardPage() {
  // Server-side data fetching
  const portfolioData = await fetchPortfolioData();
  
  return (
    <div>
      <DashboardClient initialData={portfolioData} />
    </div>
  );
}

// app/components/DashboardClient.tsx (Client Component)
'use client';

import { useEffect, useState } from 'react';

interface DashboardClientProps {
  initialData: PortfolioData;
}

export function DashboardClient({ initialData }: DashboardClientProps) {
  const [data, setData] = useState(initialData);
  
  // Client-side interactivity
  return <div>...</div>;
}
```

## API Integration

### API Client Patterns
- Create typed API client functions
- Use proper error handling
- Include loading and error states
- Use SWR or React Query for data fetching and caching

```typescript
// lib/api/client.ts
interface ApiClient {
  get<T>(url: string): Promise<T>;
  post<T>(url: string, data: unknown): Promise<T>;
}

class ApiClientImpl implements ApiClient {
  private baseURL: string;
  
  constructor(baseURL: string = '/api/v1') {
    this.baseURL = baseURL;
  }
  
  async get<T>(url: string): Promise<T> {
    const response = await fetch(`${this.baseURL}${url}`);
    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }
    return response.json();
  }
  
  async post<T>(url: string, data: unknown): Promise<T> {
    const response = await fetch(`${this.baseURL}${url}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }
    return response.json();
  }
}

export const apiClient = new ApiClientImpl();
```

### SWR Integration
```typescript
import useSWR from 'swr';
import { apiClient } from '@/lib/api/client';

function usePortfolioStatus() {
  const { data, error, isLoading, mutate } = useSWR(
    '/portfolio/status',
    () => apiClient.get<PortfolioStatus>('/portfolio/status'),
    {
      refreshInterval: 5000,
      revalidateOnFocus: true,
    }
  );
  
  return {
    portfolio: data,
    loading: isLoading,
    error,
    refresh: mutate,
  };
}
```

### Error Handling
- Handle network errors gracefully
- Show user-friendly error messages
- Implement retry logic for transient failures
- Use error boundaries for component-level error handling

```typescript
async function fetchWithRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 2 ** attempt * 1000));
    }
  }
  throw new Error('Max retries exceeded');
}
```

## WebSocket Integration

### WebSocket Client
- Use proper connection lifecycle management
- Handle reconnection logic
- Clean up connections in useEffect cleanup
- Use proper TypeScript types for messages

```typescript
import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  type: string;
  data: unknown;
  timestamp?: string;
}

export function useWebSocket(url: string) {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;
    
    ws.onopen = () => {
      setConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        setMessages(prev => [...prev, message]);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      setConnected(false);
      console.log('WebSocket disconnected');
    };
    
    return () => {
      ws.close();
    };
  }, [url]);
  
  const send = (message: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  };
  
  return { messages, connected, send };
}
```

## Component Patterns

### Form Handling
- Use controlled components
- Validate inputs client-side
- Show validation errors clearly
- Handle async form submissions

```typescript
import { useState, FormEvent } from 'react';

interface TradeFormData {
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity?: number;
}

export function TradeForm() {
  const [formData, setFormData] = useState<TradeFormData>({
    symbol: 'BTCUSD',
    side: 'BUY',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof TradeFormData, string>>>({});
  const [submitting, setSubmitting] = useState(false);
  
  const validate = (): boolean => {
    const newErrors: typeof errors = {};
    if (!formData.symbol) newErrors.symbol = 'Symbol is required';
    if (!formData.side) newErrors.side = 'Side is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    
    setSubmitting(true);
    try {
      await apiClient.post('/trade', formData);
      // Success handling
    } catch (error) {
      console.error('Trade submission failed:', error);
    } finally {
      setSubmitting(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <button type="submit" disabled={submitting}>
        {submitting ? 'Submitting...' : 'Submit Trade'}
      </button>
    </form>
  );
}
```

### Loading States
- Show loading indicators during async operations
- Use skeleton screens for better UX
- Disable interactive elements during loading

### Error States
- Display user-friendly error messages
- Provide actions to retry or recover
- Log errors for debugging

## Styling

### Tailwind CSS
- Use Tailwind utility classes
- Create custom components with Tailwind
- Use responsive design utilities
- Follow mobile-first approach

```typescript
export function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {children}
    </div>
  );
}

export function Button({ 
  onClick, 
  disabled, 
  children 
}: { 
  onClick?: () => void; 
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      {children}
    </button>
  );
}
```

### Component Libraries
- Use Radix UI for accessible components
- Use Ant Design charts for data visualization
- Customize components to match design system
- Maintain consistent styling across the application

## Code Quality

### Best Practices
- Use meaningful variable and function names
- Keep components small and focused
- Extract reusable logic into custom hooks
- Use TypeScript types consistently
- Avoid prop drilling - use context when needed
- Memoize expensive computations with useMemo
- Optimize re-renders with React.memo when appropriate

### Performance
- Use React.memo for expensive components
- Use useMemo for expensive calculations
- Use useCallback for function props
- Lazy load heavy components
- Optimize bundle size with dynamic imports

```typescript
import { memo, useMemo, useCallback } from 'react';

interface ExpensiveComponentProps {
  data: number[];
  onUpdate: (value: number) => void;
}

export const ExpensiveComponent = memo(function ExpensiveComponent({
  data,
  onUpdate,
}: ExpensiveComponentProps) {
  const sum = useMemo(() => data.reduce((a, b) => a + b, 0), [data]);
  const handleUpdate = useCallback((value: number) => {
    onUpdate(value);
  }, [onUpdate]);
  
  return <div>Sum: {sum}</div>;
});
```

## Testing

### Component Testing
- Use React Testing Library for component tests
- Test user interactions, not implementation details
- Mock API calls and external dependencies
- Test error states and edge cases

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { PortfolioStatus } from './PortfolioStatus';

describe('PortfolioStatus', () => {
  it('displays portfolio balance', async () => {
    const mockFetch = jest.fn().mockResolvedValue({
      json: async () => ({ balance: 10000, equity: 10500 }),
    });
    global.fetch = mockFetch;
    
    render(<PortfolioStatus initialBalance={10000} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Balance:/)).toBeInTheDocument();
    });
  });
});
```

