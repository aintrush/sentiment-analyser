"""
Backtesting Engine Module

I built this backtesting system to test my trading strategies without risking real money.
I learned that it's really important to include transaction costs and risk management,
otherwise the results look way too good to be true.

IMPORTANT BACKTESTING CONCEPTS:
- Look-ahead bias: Using information we wouldn't have had at the time
- Sharpe ratio: Risk-adjusted return (higher is better, >1 is good, >2 is excellent)
- Overfitting: When strategies work great historically but fail in real trading
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Backtester:
    """
    My backtesting engine that tries to simulate real trading as closely as possible.
    I learned that backtesting needs to be realistic or the results are meaningless.
    
    Features:
    - Next-day execution to avoid look-ahead bias
    - Transaction costs (10 bps each way)
    - 5% stop-loss on all trades
    - Complete performance metrics
    - Benchmark comparison
    """
    
    def __init__(self, initial_capital: float = 100000, 
                 transaction_cost_bps: float = 10, 
                 stop_loss_pct: float = 0.05):
        """
        Initialize the backtester with trading parameters.
        
        Args:
            initial_capital (float): Starting capital (default ₹100,000)
            transaction_cost_bps (float): Transaction cost in basis points (default 10 bps = 0.1%)
            stop_loss_pct (float): Stop-loss percentage (default 5%)
        """
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost_bps / 10000  # Convert bps to decimal
        self.stop_loss_pct = stop_loss_pct
        self.risk_free_rate = 0.06  # 6% annual risk-free rate for Sharpe ratio
    
    def execute_trades(self, data: pd.DataFrame, signals: pd.Series) -> pd.DataFrame:
        """
        Execute trading signals with realistic market simulation.
        
        Look-ahead bias prevention:
        - Signals generated at T close are executed at T+1 open
        - No use of future price information in trade decisions
        
        Position sizing rules:
        - Maximum 100% of portfolio value in positions
        - No leverage - portfolio value never goes negative
        - Fixed position sizing to prevent compounding errors
        
        Args:
            data (pd.DataFrame): OHLCV data
            signals (pd.Series): Trading signals (1=BUY, -1=SELL, 0=HOLD)
            
        Returns:
            pd.DataFrame: Trade execution details
        """
        # Initialize tracking variables
        trades = []
        position = 0  # Current position (positive = long, negative = short, 0 = flat)
        entry_price = 0
        entry_date = None
        cash = self.initial_capital
        portfolio_value = []
        
        # Position sizing: Use fixed percentage of initial capital
        max_position_value = self.initial_capital * 0.95  # 95% max to keep some cash buffer
        
        # Shift signals by 1 to execute next day (avoid look-ahead bias)
        execution_signals = signals.shift(1).fillna(0)
        
        for i, (date, row) in enumerate(data.iterrows()):
            signal = execution_signals.iloc[i]
            current_price = row['Open']  # Execute at next day's open
            
            # Calculate current portfolio value
            if position != 0:
                unrealized_pnl = position * (current_price - entry_price)
                current_portfolio_value = cash + (position * current_price)
            else:
                unrealized_pnl = 0
                current_portfolio_value = cash
            
            portfolio_value.append(current_portfolio_value)
            
            # Sanity check: portfolio value should never go negative
            if current_portfolio_value < 0:
                raise ValueError(f"Portfolio value went negative: {current_portfolio_value} on {date}")
            
            # Check for stop-loss
            if position != 0:
                if position > 0:  # Long position
                    stop_loss_price = entry_price * (1 - self.stop_loss_pct)
                    if current_price <= stop_loss_price:
                        # Stop-loss triggered
                        pnl = position * (current_price - entry_price)
                        cost = abs(position) * current_price * self.transaction_cost
                        cash += (position * current_price) - cost
                        
                        # Sanity check for single trade returns
                        trade_return = pnl / (position * entry_price)
                        if abs(trade_return) > 1.0:  # More than 100% return
                            print(f"WARNING: Unusually large trade return: {trade_return:.2%} on {date}")
                        
                        trades.append({
                            'date': date,
                            'action': 'STOP_LOSS_SELL',
                            'price': current_price,
                            'quantity': abs(position),
                            'pnl': pnl,
                            'cost': cost,
                            'portfolio_value': cash
                        })
                        
                        position = 0
                        entry_price = 0
                        entry_date = None
                        continue
                
                elif position < 0:  # Short position
                    stop_loss_price = entry_price * (1 + self.stop_loss_pct)
                    if current_price >= stop_loss_price:
                        # Stop-loss triggered
                        pnl = position * (current_price - entry_price)
                        cost = abs(position) * current_price * self.transaction_cost
                        cash -= (position * current_price) + cost
                        
                        # Sanity check for single trade returns
                        trade_return = pnl / (abs(position) * entry_price)
                        if abs(trade_return) > 1.0:  # More than 100% return
                            print(f"WARNING: Unusually large trade return: {trade_return:.2%} on {date}")
                        
                        trades.append({
                            'date': date,
                            'action': 'STOP_LOSS_BUY',
                            'price': current_price,
                            'quantity': abs(position),
                            'pnl': pnl,
                            'cost': cost,
                            'portfolio_value': cash
                        })
                        
                        position = 0
                        entry_price = 0
                        entry_date = None
                        continue
            
            # Process trading signals
            if signal == 1 and position <= 0:  # BUY signal
                if position < 0:  # Close short position first
                    pnl = position * (current_price - entry_price)
                    cost = abs(position) * current_price * self.transaction_cost
                    cash -= (position * current_price) + cost
                    
                    trades.append({
                        'date': date,
                        'action': 'CLOSE_SHORT',
                        'price': current_price,
                        'quantity': abs(position),
                        'pnl': pnl,
                        'cost': cost,
                        'portfolio_value': cash
                    })
                
                # Open long position with fixed sizing
                position_value = min(max_position_value, cash * 0.95)  # Use 95% of available cash, capped
                position_size = position_value / current_price
                cost = position_size * current_price * self.transaction_cost
                cash -= position_size * current_price + cost
                
                position = position_size
                entry_price = current_price
                entry_date = date
                
                trades.append({
                    'date': date,
                    'action': 'BUY',
                    'price': current_price,
                    'quantity': position_size,
                    'pnl': 0,
                    'cost': cost,
                    'portfolio_value': cash + (position * current_price)
                })
            
            elif signal == -1 and position >= 0:  # SELL signal
                if position > 0:  # Close long position first
                    pnl = position * (current_price - entry_price)
                    cost = position * current_price * self.transaction_cost
                    cash += position * current_price - cost
                    
                    # Sanity check for single trade returns
                    trade_return = pnl / (position * entry_price)
                    if abs(trade_return) > 1.0:  # More than 100% return
                        print(f"WARNING: Unusually large trade return: {trade_return:.2%} on {date}")
                    
                    trades.append({
                        'date': date,
                        'action': 'SELL',
                        'price': current_price,
                        'quantity': position,
                        'pnl': pnl,
                        'cost': cost,
                        'portfolio_value': cash
                    })
                
                # Open short position with fixed sizing
                position_value = min(max_position_value, cash * 0.95)  # Use 95% of available cash, capped
                position_size = position_value / current_price
                cost = position_size * current_price * self.transaction_cost
                cash += position_size * current_price - cost
                
                position = -position_size
                entry_price = current_price
                entry_date = date
                
                trades.append({
                    'date': date,
                    'action': 'SHORT',
                    'price': current_price,
                    'quantity': position_size,
                    'pnl': 0,
                    'cost': cost,
                    'portfolio_value': cash + (position * current_price)
                })
        
        # Close final position if any
        if position != 0:
            final_price = data['Open'].iloc[-1]
            pnl = position * (final_price - entry_price)
            cost = abs(position) * final_price * self.transaction_cost
            
            # Sanity check for final trade returns
            trade_return = pnl / (abs(position) * entry_price)
            if abs(trade_return) > 1.0:  # More than 100% return
                print(f"WARNING: Unusually large final trade return: {trade_return:.2%}")
            
            if position > 0:
                cash += position * final_price - cost
                action = 'FINAL_SELL'
            else:
                cash -= position * final_price + cost
                action = 'FINAL_BUY'
            
            trades.append({
                'date': data.index[-1],
                'action': action,
                'price': final_price,
                'quantity': abs(position),
                'pnl': pnl,
                'cost': cost,
                'portfolio_value': cash
            })
        
        # Create trades DataFrame
        trades_df = pd.DataFrame(trades)
        
        # Create portfolio value series
        portfolio_series = pd.Series(portfolio_value, index=data.index)
        
        return trades_df, portfolio_series
    
    def calculate_performance_metrics(self, portfolio_values: pd.Series, 
                                   benchmark_values: pd.Series = None) -> Dict:
        """
        Calculate comprehensive performance metrics.
        
        Sharpe Ratio Interpretation:
        - < 1: Poor risk-adjusted returns
        - 1-2: Good risk-adjusted returns  
        - 2-3: Very good risk-adjusted returns
        - > 3: Excellent risk-adjusted returns
        
        Args:
            portfolio_values (pd.Series): Daily portfolio values
            benchmark_values (pd.Series): Benchmark values (buy-and-hold)
            
        Returns:
            Dict: Performance metrics
        """
        # Calculate daily returns
        portfolio_returns = portfolio_values.pct_change().dropna()
        
        # Basic metrics
        total_return = (portfolio_values.iloc[-1] / portfolio_values.iloc[0]) - 1
        trading_days = len(portfolio_returns)
        years = trading_days / 252  # Assuming 252 trading days per year
        annualised_return = (1 + total_return) ** (1/years) - 1
        
        # Sanity check for unrealistic returns
        if abs(total_return) > 5.0:  # More than 500% total return
            print(f"WARNING: Unrealistic total return detected: {total_return:.2%}")
        if abs(annualised_return) > 2.0:  # More than 200% annual return
            print(f"WARNING: Unrealistic annual return detected: {annualised_return:.2%}")
        
        # Risk metrics
        daily_volatility = portfolio_returns.std()
        annualised_volatility = daily_volatility * np.sqrt(252)
        
        # Sharpe ratio (annualised)
        excess_returns = portfolio_returns - (self.risk_free_rate / 252)
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        
        # Maximum drawdown
        peak = portfolio_values.expanding().max()
        drawdown = (portfolio_values - peak) / peak
        max_drawdown = drawdown.min()
        
        # Trade statistics (if trades data available)
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        profit_factor = 0
        
        # Monthly returns for heatmap
        monthly_returns = portfolio_values.resample('ME').last().pct_change().dropna()
        
        metrics = {
            'total_return': total_return,
            'annualised_return': annualised_return,
            'annualised_volatility': annualised_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'trading_days': trading_days,
            'years': years,
            'monthly_returns': monthly_returns,
            'daily_returns': portfolio_returns
        }
        
        # Add benchmark comparison if provided
        if benchmark_values is not None:
            benchmark_returns = benchmark_values.pct_change().dropna()
            benchmark_total_return = (benchmark_values.iloc[-1] / benchmark_values.iloc[0]) - 1
            benchmark_annualised_return = (1 + benchmark_total_return) ** (1/years) - 1
            benchmark_volatility = benchmark_returns.std() * np.sqrt(252)
            
            # Calculate beta and alpha
            aligned_returns = pd.DataFrame({
                'portfolio': portfolio_returns,
                'benchmark': benchmark_returns
            }).dropna()
            
            if len(aligned_returns) > 1:
                covariance = aligned_returns.cov().iloc[0, 1]
                benchmark_variance = aligned_returns['benchmark'].var()
                beta = covariance / benchmark_variance
                
                # Alpha (annualised)
                alpha = annualised_return - (self.risk_free_rate + beta * (benchmark_annualised_return - self.risk_free_rate))
            else:
                beta = 1.0
                alpha = 0.0
            
            metrics.update({
                'benchmark_total_return': benchmark_total_return,
                'benchmark_annualised_return': benchmark_annualised_return,
                'benchmark_volatility': benchmark_volatility,
                'beta': beta,
                'alpha': alpha,
                'excess_return_vs_benchmark': annualised_return - benchmark_annualised_return
            })
        
        return metrics
    
    def run_backtest(self, data: pd.DataFrame, signals: pd.Series, 
                    benchmark: bool = True) -> Tuple[Dict, pd.DataFrame, pd.Series]:
        """
        Run complete backtest with benchmark comparison.
        
        Overfitting Warning:
        Backtests can overfit to historical data. A strategy that looks great
        historically may fail in live trading due to:
        - Changing market conditions
        - Data mining bias
        - Transaction cost underestimation
        - Liquidity constraints
        
        Args:
            data (pd.DataFrame): OHLCV data
            signals (pd.Series): Trading signals
            benchmark (bool): Whether to include buy-and-hold benchmark
            
        Returns:
            Tuple[Dict, pd.DataFrame, pd.Series]: (metrics, trades, portfolio_values)
        """
        # Execute trades
        trades, portfolio_values = self.execute_trades(data, signals)
        
        # Calculate benchmark if requested
        benchmark_values = None
        if benchmark:
            # Buy and hold benchmark (invest initial capital at start)
            benchmark_shares = self.initial_capital / data['Open'].iloc[0]
            benchmark_values = benchmark_shares * data['Open']
        
        # Calculate performance metrics
        metrics = self.calculate_performance_metrics(portfolio_values, benchmark_values)
        
        return metrics, trades, portfolio_values


if __name__ == "__main__":
    # Example usage
    import yfinance as yf
    from signals.strategy_engine import SignalGenerator
    
    # Download sample data
    ticker = yf.Ticker("^NSEI")
    data = ticker.history(period="1y")
    
    # Generate signals
    signal_gen = SignalGenerator()
    signals = signal_gen.moving_average_crossover(data)
    
    # Run backtest
    backtester = Backtester()
    metrics, trades, portfolio = backtester.run_backtest(data, signals)
    
    print("Backtest Results:")
    print(f"Total Return: {metrics['total_return']:.2%}")
    print(f"Annualised Return: {metrics['annualised_return']:.2%}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"Number of Trades: {len(trades)}")
    
    if 'excess_return_vs_benchmark' in metrics:
        print(f"Excess Return vs Benchmark: {metrics['excess_return_vs_benchmark']:.2%}")
