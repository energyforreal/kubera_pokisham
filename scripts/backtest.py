"""Backtest trading strategy on historical data."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.database import SessionLocal, init_db
from src.core.logger import logger
from src.data.feature_engineer import FeatureEngineer
from src.ml.xgboost_model import XGBoostTradingModel
from src.risk.position_sizer import PositionSizer


class Backtester:
    """Simple backtesting engine."""
    
    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = None
        self.trades = []
        self.model = XGBoostTradingModel()
        self.feature_engineer = FeatureEngineer()
        self.position_sizer = PositionSizer()
    
    def load_model(self, model_path: str):
        """Load trained model."""
        self.model.load(model_path)
        logger.info(f"Model loaded from {model_path}")
    
    def run(self, df: pd.DataFrame) -> dict:
        """Run backtest on historical data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Backtest results dictionary
        """
        logger.info(f"Running backtest on {len(df)} candles")
        
        # Create features
        df = self.feature_engineer.create_features(df)
        
        if df.empty:
            logger.error("Feature engineering failed")
            return {}
        
        # Get predictions
        X, _, feature_names = self.feature_engineer.prepare_for_model(df)
        predictions, confidences = self.model.predict(X)
        
        # Add predictions to dataframe
        df['prediction'] = predictions
        df['confidence'] = confidences
        
        # Map predictions
        label_map = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
        df['signal'] = df['prediction'].map(label_map)
        
        # Simulate trading
        for i, row in df.iterrows():
            current_price = row['close']
            signal = row['signal']
            confidence = row['confidence']
            
            # Check if confident enough
            if confidence < 0.65:
                continue
            
            # If we have a position, check exit
            if self.position:
                # Check stop loss / take profit
                if (self.position['side'] == 'buy' and current_price <= self.position['stop_loss']) or \
                   (self.position['side'] == 'sell' and current_price >= self.position['stop_loss']):
                    # Stop loss hit
                    self._close_position(current_price, row['timestamp'], 'stop_loss')
                elif (self.position['side'] == 'buy' and current_price >= self.position['take_profit']) or \
                     (self.position['side'] == 'sell' and current_price <= self.position['take_profit']):
                    # Take profit hit
                    self._close_position(current_price, row['timestamp'], 'take_profit')
                # Check signal reversal
                elif (self.position['side'] == 'buy' and signal == 'SELL') or \
                     (self.position['side'] == 'sell' and signal == 'BUY'):
                    self._close_position(current_price, row['timestamp'], 'signal')
            
            # Open new position if no position and strong signal
            if not self.position and signal in ['BUY', 'SELL']:
                self._open_position(
                    side='buy' if signal == 'BUY' else 'sell',
                    price=current_price,
                    timestamp=row['timestamp'],
                    atr=row.get('atr', current_price * 0.02),
                    confidence=confidence
                )
        
        # Close any open position at end
        if self.position:
            self._close_position(df.iloc[-1]['close'], df.iloc[-1]['timestamp'], 'end')
        
        # Calculate metrics
        return self._calculate_metrics()
    
    def _open_position(self, side: str, price: float, timestamp: datetime, atr: float, confidence: float):
        """Open a position."""
        # Calculate position size
        size = self.position_sizer.calculate_position_size(
            balance=self.balance,
            confidence=confidence
        )
        
        # Calculate stop loss and take profit
        if side == 'buy':
            stop_loss = price - (2 * atr)
            take_profit = price + (4 * atr)  # 2:1 RR
        else:
            stop_loss = price + (2 * atr)
            take_profit = price - (4 * atr)
        
        self.position = {
            'side': side,
            'entry_price': price,
            'size': size / price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': timestamp
        }
        
        # Deduct from balance
        self.balance -= size * 1.001  # Include 0.1% fee
    
    def _close_position(self, price: float, timestamp: datetime, reason: str):
        """Close the position."""
        if not self.position:
            return
        
        # Calculate PnL
        if self.position['side'] == 'buy':
            pnl = (price - self.position['entry_price']) * self.position['size']
        else:
            pnl = (self.position['entry_price'] - price) * self.position['size']
        
        # Deduct fee
        pnl -= (price * self.position['size'] * 0.001)
        
        # Update balance
        self.balance += (price * self.position['size']) + pnl
        
        # Record trade
        self.trades.append({
            'entry_price': self.position['entry_price'],
            'exit_price': price,
            'side': self.position['side'],
            'pnl': pnl,
            'pnl_pct': (pnl / (self.position['entry_price'] * self.position['size'])) * 100,
            'entry_time': self.position['entry_time'],
            'exit_time': timestamp,
            'reason': reason
        })
        
        self.position = None
    
    def _calculate_metrics(self) -> dict:
        """Calculate backtest metrics."""
        if not self.trades:
            return {
                'total_return': 0,
                'num_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0
            }
        
        total_return = (self.balance - self.initial_balance) / self.initial_balance
        
        wins = [t for t in self.trades if t['pnl'] > 0]
        losses = [t for t in self.trades if t['pnl'] < 0]
        
        win_rate = len(wins) / len(self.trades) if self.trades else 0
        avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
        
        gross_profit = sum(t['pnl'] for t in wins)
        gross_loss = abs(sum(t['pnl'] for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Simple Sharpe ratio
        returns = [t['pnl_pct'] / 100 for t in self.trades]
        sharpe = (sum(returns) / len(returns)) / (pd.Series(returns).std()) if returns else 0
        
        return {
            'initial_balance': self.initial_balance,
            'final_balance': self.balance,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'num_trades': len(self.trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': win_rate * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe
        }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Backtest trading strategy')
    parser.add_argument('--data', type=str, required=True, help='Path to historical data CSV')
    parser.add_argument('--model', type=str, default='models/xgboost_model.pkl', help='Path to trained model')
    parser.add_argument('--balance', type=float, default=10000, help='Initial balance')
    
    args = parser.parse_args()
    
    try:
        # Load data
        logger.info(f"Loading data from {args.data}")
        df = pd.read_csv(args.data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Initialize backtester
        backtester = Backtester(initial_balance=args.balance)
        backtester.load_model(args.model)
        
        # Run backtest
        results = backtester.run(df)
        
        # Print results
        print("\n" + "="*50)
        print("BACKTEST RESULTS")
        print("="*50)
        print(f"Initial Balance: ${results['initial_balance']:.2f}")
        print(f"Final Balance: ${results['final_balance']:.2f}")
        print(f"Total Return: {results['total_return_pct']:.2f}%")
        print(f"\nTrades: {results['num_trades']}")
        print(f"Winning: {results['winning_trades']}")
        print(f"Losing: {results['losing_trades']}")
        print(f"Win Rate: {results['win_rate']:.2f}%")
        print(f"\nAvg Win: ${results['avg_win']:.2f}")
        print(f"Avg Loss: ${results['avg_loss']:.2f}")
        print(f"Profit Factor: {results['profit_factor']:.2f}")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print("="*50 + "\n")
        
        logger.info("✅ Backtest complete!")
        
    except Exception as e:
        logger.error(f"❌ Backtest failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

