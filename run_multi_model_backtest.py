"""Compare all multi-model strategies with backtesting."""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from src.core.logger import logger
from src.data.delta_client import DeltaExchangeClient
from src.data.feature_engineer import FeatureEngineer
from src.ml.multi_model_predictor import MultiModelPredictor
from src.risk.position_sizer import PositionSizer


class MultiModelBacktester:
    """Backtest multi-model strategies."""
    
    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = None
        self.trades = []
        self.position_sizer = PositionSizer()
    
    def run(self, df: pd.DataFrame, predictor: MultiModelPredictor) -> dict:
        """Run backtest on historical data."""
        logger.info(f"Running backtest with {predictor.strategy} strategy on {len(df)} candles")
        
        # Reset state
        self.balance = self.initial_balance
        self.position = None
        self.trades = []
        
        # Get signals for all candles
        for i in range(len(df)):
            # Need enough data for indicators
            if i < 200:
                continue
            
            # Get data up to current point
            current_df = df.iloc[:i+1].copy()
            
            # Get signal
            signal = predictor.get_latest_signal('BTCUSD', '15m')
            
            if not signal or not signal.get('actionable'):
                continue
            
            current_price = df.iloc[i]['close']
            prediction = signal['prediction']
            confidence = signal['confidence']
            
            # If we have a position, check exit
            if self.position:
                if (self.position['side'] == 'buy' and current_price <= self.position['stop_loss']) or \
                   (self.position['side'] == 'sell' and current_price >= self.position['stop_loss']):
                    self._close_position(current_price, df.iloc[i]['timestamp'], 'stop_loss')
                elif (self.position['side'] == 'buy' and current_price >= self.position['take_profit']) or \
                     (self.position['side'] == 'sell' and current_price <= self.position['take_profit']):
                    self._close_position(current_price, df.iloc[i]['timestamp'], 'take_profit')
                elif (self.position['side'] == 'buy' and prediction == 'SELL') or \
                     (self.position['side'] == 'sell' and prediction == 'BUY'):
                    self._close_position(current_price, df.iloc[i]['timestamp'], 'signal')
            
            # Open new position
            if not self.position and prediction in ['BUY', 'SELL']:
                atr = df.iloc[i].get('atr', current_price * 0.02)
                self._open_position(
                    side='buy' if prediction == 'BUY' else 'sell',
                    price=current_price,
                    timestamp=df.iloc[i]['timestamp'],
                    atr=atr,
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
    print("="*70)
    print("MULTI-MODEL STRATEGY COMPARISON")
    print("="*70)
    
    try:
        # Download data
        print("\n📥 Downloading historical data...")
        client = DeltaExchangeClient()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        df = client.get_ohlc_candles(
            symbol='BTCUSD',
            resolution='15m',
            start=start_date,
            end=end_date,
            limit=3000
        )
        
        if df.empty:
            print("❌ No data fetched")
            sys.exit(1)
        
        print(f"✅ Downloaded {len(df)} candles")
        
        # Test all three strategies
        strategies = ['confirmation', 'weighted', 'voting']
        results = {}
        
        for strategy in strategies:
            print(f"\n{'='*70}")
            print(f"📊 Testing Strategy: {strategy.upper()}")
            print("="*70)
            
            predictor = MultiModelPredictor(strategy=strategy)
            backtester = MultiModelBacktester(initial_balance=10000)
            
            result = backtester.run(df, predictor)
            results[strategy] = result
            
            # Display results
            print(f"\nResults for {strategy.capitalize()} Strategy:")
            print(f"  Initial Balance: ${result['initial_balance']:.2f}")
            print(f"  Final Balance: ${result['final_balance']:.2f}")
            print(f"  Total Return: {result['total_return_pct']:.2f}%")
            print(f"  ")
            print(f"  Trades: {result['num_trades']}")
            print(f"  Winning: {result['winning_trades']}")
            print(f"  Losing: {result['losing_trades']}")
            print(f"  Win Rate: {result['win_rate']:.2f}%")
            print(f"  ")
            print(f"  Avg Win: ${result['avg_win']:.2f}")
            print(f"  Avg Loss: ${result['avg_loss']:.2f}")
            print(f"  Profit Factor: {result['profit_factor']:.2f}")
            print(f"  Sharpe Ratio: {result['sharpe_ratio']:.2f}")
        
        # Comparison summary
        print(f"\n{'='*70}")
        print("📈 STRATEGY COMPARISON SUMMARY")
        print("="*70)
        
        print(f"\n{'Strategy':<15} {'Win Rate':<12} {'Trades':<10} {'Profit Factor':<15} {'Return %':<12}")
        print("-"*70)
        
        for strategy in strategies:
            r = results[strategy]
            print(f"{strategy.capitalize():<15} {r['win_rate']:<12.2f} {r['num_trades']:<10} {r['profit_factor']:<15.2f} {r['total_return_pct']:<12.2f}")
        
        # Recommendation
        print(f"\n{'='*70}")
        print("💡 RECOMMENDATION")
        print("="*70)
        
        best_strategy = max(results, key=lambda x: results[x]['profit_factor'])
        best_result = results[best_strategy]
        
        print(f"\nBest Strategy: {best_strategy.upper()}")
        print(f"  - Win Rate: {best_result['win_rate']:.2f}%")
        print(f"  - Profit Factor: {best_result['profit_factor']:.2f}")
        print(f"  - Total Return: {best_result['total_return_pct']:.2f}%")
        print(f"  - Trades: {best_result['num_trades']}")
        
        print(f"\nTo use this strategy, set in config.yaml:")
        print(f"  multi_model:")
        print(f"    enabled: true")
        print(f"    strategy: \"{best_strategy}\"")
        
        print("\n✅ Backtest comparison complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

