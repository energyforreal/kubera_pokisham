"""Download data and run backtest - all in one."""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from src.core.database import SessionLocal, OHLCVData, init_db
from src.core.logger import logger
from src.data.delta_client import DeltaExchangeClient
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
        """Run backtest on historical data."""
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
                    self._close_position(current_price, row['timestamp'], 'stop_loss')
                elif (self.position['side'] == 'buy' and current_price >= self.position['take_profit']) or \
                     (self.position['side'] == 'sell' and current_price <= self.position['take_profit']):
                    self._close_position(current_price, row['timestamp'], 'take_profit')
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
        size = self.position_sizer.calculate_position_size(
            balance=self.balance,
            confidence=confidence
        )
        
        if side == 'buy':
            stop_loss = price - (2 * atr)
            take_profit = price + (4 * atr)
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
        
        self.balance -= size * 1.001
    
    def _close_position(self, price: float, timestamp: datetime, reason: str):
        """Close the position."""
        if not self.position:
            return
        
        if self.position['side'] == 'buy':
            pnl = (price - self.position['entry_price']) * self.position['size']
        else:
            pnl = (self.position['entry_price'] - price) * self.position['size']
        
        pnl -= (price * self.position['size'] * 0.001)
        self.balance += (price * self.position['size']) + pnl
        
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
    print("="*60)
    print("🚀 TRADING AGENT BACKTEST")
    print("="*60)
    
    try:
        # Step 1: Download data
        print("\n📥 Step 1: Downloading historical data...")
        client = DeltaExchangeClient()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)  # Last 30 days
        
        df = client.get_ohlc_candles(
            symbol='BTCUSD',
            resolution='15m',
            start=start_date,
            end=end_date,
            limit=3000
        )
        
        if df.empty:
            print("❌ No data fetched. Check API credentials in .env file")
            sys.exit(1)
        
        print(f"✅ Downloaded {len(df)} candles")
        
        # Save data
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        csv_path = data_dir / 'BTCUSD_15m_backtest.csv'
        df.to_csv(csv_path, index=False)
        print(f"✅ Saved to {csv_path}")
        
        # Step 2: Run backtest
        print("\n📊 Step 2: Running backtest...")
        backtester = Backtester(initial_balance=10000)
        backtester.load_model('models/xgboost_BTCUSD_15m.pkl')
        
        results = backtester.run(df)
        
        # Step 3: Display results
        print("\n" + "="*60)
        print("📈 BACKTEST RESULTS")
        print("="*60)
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
        print("="*60)
        
        # Evaluation
        print("\n🎯 EVALUATION:")
        if results['win_rate'] >= 55:
            print("✅ Win rate looks good (>55%)")
        else:
            print("⚠️  Win rate below target. Consider adjusting min_confidence")
        
        if results['profit_factor'] >= 1.5:
            print("✅ Profit factor is healthy (>1.5)")
        else:
            print("⚠️  Profit factor below target. Review strategy parameters")
        
        if results['total_return_pct'] > 0:
            print("✅ Positive returns achieved")
        else:
            print("⚠️  Negative returns. Strategy needs optimization")
        
        print("\n✅ Backtest complete! Review results before paper trading.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

