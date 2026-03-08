"""
Complete Backtesting Workflow

This is my complete backtesting script that tests all the trading strategies I created.
It downloads NIFTY 50 data, runs backtests on each strategy, and makes nice charts
to compare how they all performed.

Features:
- Downloads 2 years of NIFTY 50 data
- Tests 4 individual strategies + my combined strategy
- Performance comparison table
- Equity curves visualization
- Drawdown analysis
- Monthly returns heatmap
- CSV export of results
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project directories to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.price_fetcher import PriceFetcher
from signals.strategy_engine import SignalGenerator
from backtesting.backtest import Backtester


def setup_plot_style():
    """Configure matplotlib and seaborn for professional financial charts."""
    plt.style.use('default')
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.alpha'] = 0.3
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 9
    
    # Set seaborn style
    sns.set_palette("husl")


def create_performance_comparison_table(results: dict) -> pd.DataFrame:
    """
    Create a clean performance comparison table for all strategies.
    
    Args:
        results (dict): Dictionary containing backtest results for each strategy
        
    Returns:
        pd.DataFrame: Formatted performance comparison table
    """
    comparison_data = []
    
    for strategy_name, result in results.items():
        metrics = result['metrics']
        
        comparison_data.append({
            'Strategy': strategy_name,
            'Total Return (%)': f"{metrics['total_return'] * 100:.2f}",
            'Annual Return (%)': f"{metrics['annualised_return'] * 100:.2f}",
            'Volatility (%)': f"{metrics['annualised_volatility'] * 100:.2f}",
            'Sharpe Ratio': f"{metrics['sharpe_ratio']:.2f}",
            'Max Drawdown (%)': f"{metrics['max_drawdown'] * 100:.2f}",
            'Trades': len(result['trades']),
            'Win Rate (%)': f"{(result['trades']['pnl'] > 0).mean() * 100:.1f}" if len(result['trades']) > 0 else "0.0"
        })
        
        # Add benchmark comparison
        if 'excess_return_vs_benchmark' in metrics:
            comparison_data[-1]['Excess vs Buy&Hold (%)'] = f"{metrics['excess_return_vs_benchmark'] * 100:.2f}"
    
    df = pd.DataFrame(comparison_data)
    
    # Add benchmark row
    if results:  # If we have results, add benchmark
        benchmark_metrics = list(results.values())[0]['metrics']
        benchmark_data = {
            'Strategy': 'Buy & Hold (Benchmark)',
            'Total Return (%)': f"{benchmark_metrics.get('benchmark_total_return', 0) * 100:.2f}",
            'Annual Return (%)': f"{benchmark_metrics.get('benchmark_annualised_return', 0) * 100:.2f}",
            'Volatility (%)': f"{benchmark_metrics.get('benchmark_volatility', 0) * 100:.2f}",
            'Sharpe Ratio': 'N/A',
            'Max Drawdown (%)': 'N/A',
            'Trades': '1',
            'Win Rate (%)': 'N/A'
        }
        df = pd.concat([df, pd.DataFrame([benchmark_data])], ignore_index=True)
    
    return df


def create_equity_curves_chart(results: dict, data: pd.DataFrame):
    """
    Create equity curves chart comparing all strategies.
    
    Args:
        results (dict): Backtest results for all strategies
        data (pd.DataFrame): Original price data
    """
    setup_plot_style()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot equity curves
    for strategy_name, result in results.items():
        portfolio_values = result['portfolio']
        normalized_values = (portfolio_values / portfolio_values.iloc[0] - 1) * 100
        ax.plot(portfolio_values.index, normalized_values, 
                label=strategy_name, linewidth=2, alpha=0.8)
    
    # Add benchmark
    if results:
        benchmark_shares = 100000 / data['Open'].iloc[0]
        benchmark_values = benchmark_shares * data['Open']
        normalized_benchmark = (benchmark_values / benchmark_values.iloc[0] - 1) * 100
        ax.plot(benchmark_values.index, normalized_benchmark, 
                label='Buy & Hold', linewidth=2, alpha=0.8, linestyle='--', color='black')
    
    ax.set_title('Strategy Performance - Equity Curves', fontsize=14, fontweight='bold')
    ax.set_ylabel('Returns (%)')
    ax.set_xlabel('Date')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    return fig


def create_drawdown_chart(results: dict):
    """
    Create drawdown analysis chart.
    
    Args:
        results (dict): Backtest results for all strategies
    """
    setup_plot_style()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for strategy_name, result in results.items():
        portfolio_values = result['portfolio']
        peak = portfolio_values.expanding().max()
        drawdown = (portfolio_values - peak) / peak * 100
        
        ax.fill_between(drawdown.index, drawdown, 0, 
                       alpha=0.3, label=strategy_name)
        ax.plot(drawdown.index, drawdown, alpha=0.8, linewidth=1.5)
    
    ax.set_title('Strategy Drawdown Analysis', fontsize=14, fontweight='bold')
    ax.set_ylabel('Drawdown (%)')
    ax.set_xlabel('Date')
    ax.legend(loc='lower left')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    return fig


def create_monthly_returns_heatmap(results: dict):
    """
    Create monthly returns heatmap for the best performing strategy.
    
    Args:
        results (dict): Backtest results for all strategies
    """
    setup_plot_style()
    
    # Find best performing strategy (highest Sharpe ratio)
    best_strategy = max(results.keys(), 
                       key=lambda x: results[x]['metrics']['sharpe_ratio'])
    
    monthly_returns = results[best_strategy]['metrics']['monthly_returns']
    
    # Reshape to year-month format for heatmap
    monthly_returns.index = pd.to_datetime(monthly_returns.index)
    monthly_returns_df = monthly_returns.to_frame('returns')
    monthly_returns_df['year'] = monthly_returns_df.index.year
    monthly_returns_df['month'] = monthly_returns_df.index.month
    
    # Create pivot table
    pivot_table = monthly_returns_df.pivot(index='year', columns='month', values='returns')
    pivot_table.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Convert to percentage
    pivot_table = pivot_table * 100
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 8))
    
    sns.heatmap(pivot_table, annot=True, fmt='.1f', cmap='RdYlGn', 
                center=0, ax=ax, cbar_kws={'label': 'Returns (%)'})
    
    ax.set_title(f'Monthly Returns Heatmap - {best_strategy}', 
                fontsize=14, fontweight='bold')
    ax.set_ylabel('Year')
    ax.set_xlabel('Month')
    
    plt.tight_layout()
    return fig


def save_results_to_csv(results: dict, filename: str = 'backtest_results.csv'):
    """
    Save detailed backtest results to CSV file.
    
    Args:
        results (dict): Backtest results for all strategies
        filename (str): Output filename
    """
    all_results = []
    
    for strategy_name, result in results.items():
        # Create summary for each strategy
        metrics = result['metrics']
        trades = result['trades']
        
        summary = {
            'strategy': strategy_name,
            'total_return': metrics['total_return'],
            'annualised_return': metrics['annualised_return'],
            'volatility': metrics['annualised_volatility'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'max_drawdown': metrics['max_drawdown'],
            'num_trades': len(trades),
            'final_portfolio_value': result['portfolio'].iloc[-1]
        }
        
        # Add benchmark comparison if available
        if 'excess_return_vs_benchmark' in metrics:
            summary.update({
                'benchmark_return': metrics['benchmark_total_return'],
                'excess_return': metrics['excess_return_vs_benchmark'],
                'alpha': metrics['alpha'],
                'beta': metrics['beta']
            })
        
        # Add trade statistics
        if len(trades) > 0:
            winning_trades = trades[trades['pnl'] > 0]
            losing_trades = trades[trades['pnl'] < 0]
            
            summary.update({
                'win_rate': len(winning_trades) / len(trades),
                'avg_win': winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0,
                'avg_loss': losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0,
                'profit_factor': abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else np.inf,
                'total_pnl': trades['pnl'].sum(),
                'total_costs': trades['cost'].sum()
            })
        
        all_results.append(summary)
    
    # Save to CSV
    df = pd.DataFrame(all_results)
    df.to_csv(filename, index=False)
    print(f"✓ Results saved to {filename}")


def main():
    """Main function to run complete backtesting workflow."""
    print("Algorithmic Market Sentiment Analyser - Backtesting Engine")
    print("="*60)
    
    # Initialize components
    fetcher = PriceFetcher()
    signal_gen = SignalGenerator()
    backtester = Backtester()
    
    # Download 2 years of NIFTY 50 data
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')  # 2 years
    
    print(f"\nDownloading NIFTY 50 data for backtesting...")
    print(f"Period: {start_date} to {end_date}")
    
    try:
        # Fetch data
        data = fetcher.fetch_data('^NSEI', start_date, end_date)
        print(f"✓ Successfully fetched {len(data)} days of data")
        
        # Generate signals for all strategies
        print("Generating trading signals...")
        signals = signal_gen.generate_all_signals(data)
        print("✓ All signals generated successfully")
        
        # Define strategies to test
        strategies = {
            'MA Crossover (50/200)': signals['ma_crossover'],
            'RSI Mean Reversion (30/70)': signals['rsi_mean_reversion'],
            'MACD Signal Cross': signals['macd_crossover'],
            'Bollinger Breakout': signals['bollinger_breakout'],
            'Combined Strategy': signals['combined']
        }
        
        # Run backtests for all strategies
        print("\nRunning backtests...")
        results = {}
        
        for strategy_name, strategy_signals in strategies.items():
            print(f"  Testing: {strategy_name}")
            metrics, trades, portfolio = backtester.run_backtest(data, strategy_signals)
            
            results[strategy_name] = {
                'metrics': metrics,
                'trades': trades,
                'portfolio': portfolio
            }
        
        print("✓ All backtests completed successfully")
        
        # Create performance comparison table
        print("\n" + "="*60)
        print("PERFORMANCE COMPARISON")
        print("="*60)
        
        comparison_table = create_performance_comparison_table(results)
        print(comparison_table.to_string(index=False))
        
        # Save results to CSV
        save_results_to_csv(results)
        
        # Create visualizations
        print("\nGenerating visualizations...")
        
        # Equity curves
        equity_fig = create_equity_curves_chart(results, data)
        equity_fig.savefig('equity_curves.png', dpi=300, bbox_inches='tight')
        print("✓ Equity curves saved as 'equity_curves.png'")
        
        # Drawdown chart
        drawdown_fig = create_drawdown_chart(results)
        drawdown_fig.savefig('drawdown_analysis.png', dpi=300, bbox_inches='tight')
        print("✓ Drawdown analysis saved as 'drawdown_analysis.png'")
        
        # Monthly returns heatmap
        heatmap_fig = create_monthly_returns_heatmap(results)
        heatmap_fig.savefig('monthly_returns_heatmap.png', dpi=300, bbox_inches='tight')
        print("✓ Monthly returns heatmap saved as 'monthly_returns_heatmap.png'")
        
        # Display charts
        plt.show()
        
        # Print summary
        print(f"\n" + "="*60)
        print("BACKTESTING SUMMARY")
        print("="*60)
        
        # Find best strategy
        best_strategy = max(results.keys(), 
                          key=lambda x: results[x]['metrics']['sharpe_ratio'])
        best_metrics = results[best_strategy]['metrics']
        
        print(f"\nBest Performing Strategy: {best_strategy}")
        print(f"  Total Return: {best_metrics['total_return']:.2%}")
        print(f"  Annual Return: {best_metrics['annualised_return']:.2%}")
        print(f"  Sharpe Ratio: {best_metrics['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {best_metrics['max_drawdown']:.2%}")
        print(f"  Number of Trades: {len(results[best_strategy]['trades'])}")
        
        if 'excess_return_vs_benchmark' in best_metrics:
            print(f"  Excess Return vs Buy&Hold: {best_metrics['excess_return_vs_benchmark']:.2%}")
        
        print(f"\nAll files saved successfully!")
        print("Files created:")
        print("  - backtest_results.csv")
        print("  - equity_curves.png")
        print("  - drawdown_analysis.png")
        print("  - monthly_returns_heatmap.png")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
