/**
 * Position Manager with Stop-Loss/Take-Profit editing
 */

'use client';

import { useState, ChangeEvent } from 'react';
import { api } from '@/services/api';

interface Position {
  symbol: string;
  side: string;
  entry_price: number;
  size: number;
  stop_loss: number;
  take_profit: number;
  unrealized_pnl?: number;
}

interface PositionManagerProps {
  position: Position;
  onUpdate?: () => void;
}

export default function PositionManager({ position, onUpdate }: PositionManagerProps) {
  const [editing, setEditing] = useState(false);
  const [stopLoss, setStopLoss] = useState(position.stop_loss);
  const [takeProfit, setTakeProfit] = useState(position.take_profit);
  const [loading, setLoading] = useState(false);

  const handleUpdate = async () => {
    setLoading(true);
    try {
      await api.updatePosition(position.symbol, {
        stop_loss: stopLoss,
        take_profit: takeProfit
      });
      
      alert('✅ Position updated successfully!');
      setEditing(false);
      onUpdate?.();
    } catch (error: any) {
      alert(`❌ Update failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = async () => {
    if (!confirm(`Are you sure you want to close ${position.symbol} position?`)) {
      return;
    }

    setLoading(true);
    try {
      await api.closePosition(position.symbol);
      alert('✅ Position closed successfully!');
      onUpdate?.();
    } catch (error: any) {
      alert(`❌ Close failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap font-medium">{position.symbol}</td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`px-2 py-1 text-xs rounded ${
          position.side === 'buy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {position.side.toUpperCase()}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">${position.entry_price.toFixed(2)}</td>
      <td className="px-6 py-4 whitespace-nowrap">{position.size.toFixed(4)}</td>
      <td className="px-6 py-4 whitespace-nowrap">
        {editing ? (
          <input
            type="number"
            value={stopLoss}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setStopLoss(parseFloat(e.target.value))}
            className="w-24 px-2 py-1 border rounded"
            step="0.01"
          />
        ) : (
          `$${position.stop_loss.toFixed(2)}`
        )}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        {editing ? (
          <input
            type="number"
            value={takeProfit}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setTakeProfit(parseFloat(e.target.value))}
            className="w-24 px-2 py-1 border rounded"
            step="0.01"
          />
        ) : (
          `$${position.take_profit.toFixed(2)}`
        )}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={position.unrealized_pnl && position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
          ${position.unrealized_pnl?.toFixed(2) || '0.00'}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex gap-2">
          {editing ? (
            <>
              <button
                onClick={handleUpdate}
                disabled={loading}
                className="text-green-600 hover:text-green-800 text-sm font-medium disabled:opacity-50"
              >
                Save
              </button>
              <button
                onClick={() => {
                  setEditing(false);
                  setStopLoss(position.stop_loss);
                  setTakeProfit(position.take_profit);
                }}
                disabled={loading}
                className="text-gray-600 hover:text-gray-800 text-sm"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setEditing(true)}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                Edit
              </button>
              <button
                onClick={handleClose}
                disabled={loading}
                className="text-red-600 hover:text-red-800 text-sm disabled:opacity-50"
              >
                Close
              </button>
            </>
          )}
        </div>
      </td>
    </tr>
  );
}

