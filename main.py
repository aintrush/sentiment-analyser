"""
Algorithmic Market Sentiment Analyser - Main Demo

This is my main demo script that shows what the sentiment analyser can do.
It downloads NIFTY 50 data, calculates all the technical indicators I implemented,
and creates a cool 4-panel chart to visualize everything.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project directories to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.price_fetcher import PriceFetcher
from indicators.technical import TechnicalIndicators


def setup_plot_style():
    """I set up matplotlib to make the charts look professional and clean."""
    plt.style.use('default')
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.alpha'] = 0.3
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 9


def create_four_panel_chart(data, indicators):
    """
    Create a professional 4-panel chart with price, MACD, RSI, and Volume.
    
    Args:
        data (pd.DataFrame): OHLCV data
        indicators (pd.DataFrame): Technical indicators
    """
    setup_plot_style()
    
    # Create figure with 4 subplots
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle('NIFTY 50 - Technical Analysis Dashboard', fontsize=16, fontweight='bold')
    
    # Panel 1: Price + Bollinger Bands + Moving Averages
    ax1 = plt.subplot(4, 1, 1)
    ax1.plot(data.index, data['Close'], label='Close Price', color='black', linewidth=1.5)
    ax1.plot(indicators.index, indicators['upper'], label='Upper BB', color='red', alpha=0.7, linewidth=1)
    ax1.plot(indicators.index, indicators['middle'], label='20 SMA', color='blue', alpha=0.8, linewidth=1.5)
    ax1.plot(indicators.index, indicators['lower'], label='Lower BB', color='green', alpha=0.7, linewidth=1)
    ax1.plot(indicators.index, indicators['sma_50'], label='50 SMA', color='orange', alpha=0.8, linewidth=1.2)
    ax1.plot(indicators.index, indicators['sma_200'], label='200 SMA', color='purple', alpha=0.8, linewidth=1.2)
    
    ax1.fill_between(indicators.index, indicators['upper'], indicators['lower'], 
                     alpha=0.1, color='gray', label='BB Range')
    
    ax1.set_title('Price Action with Bollinger Bands & Moving Averages', fontweight='bold')
    ax1.set_ylabel('Price (INR)')
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: MACD
    ax2 = plt.subplot(4, 1, 2)
    ax2.plot(indicators.index, indicators['macd'], label='MACD', color='blue', linewidth=1.5)
    ax2.plot(indicators.index, indicators['signal'], label='Signal', color='red', linewidth=1.5)
    
    # Histogram bars
    colors = ['green' if x >= 0 else 'red' for x in indicators['histogram']]
    ax2.bar(indicators.index, indicators['histogram'], color=colors, alpha=0.6, width=1)
    
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.set_title('MACD (12, 26, 9)', fontweight='bold')
    ax2.set_ylabel('MACD Value')
    ax2.legend(loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: RSI
    ax3 = plt.subplot(4, 1, 3)
    ax3.plot(indicators.index, indicators['rsi'], label='RSI', color='purple', linewidth=2)
    ax3.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Overbought (70)')
    ax3.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Oversold (30)')
    ax3.axhline(y=50, color='black', linestyle='-', alpha=0.3, label='Neutral (50)')
    
    ax3.set_title('RSI (14)', fontweight='bold')
    ax3.set_ylabel('RSI')
    ax3.set_ylim(0, 100)
    ax3.legend(loc='upper left', fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # Panel 4: Volume
    ax4 = plt.subplot(4, 1, 4)
    
    # Color volume bars based on price movement
    colors = ['green' if data['Close'].iloc[i] >= data['Open'].iloc[i] else 'red' 
              for i in range(len(data))]
    
    ax4.bar(data.index, data['Volume'], color=colors, alpha=0.7, width=1)
    
    # Add VWAP line
    ax4_twin = ax4.twinx()
    ax4_twin.plot(indicators.index, indicators['vwap'], label='VWAP', 
                  color='blue', linewidth=2, alpha=0.8)
    ax4_twin.set_ylabel('VWAP (INR)', color='blue')
    ax4_twin.tick_params(axis='y', labelcolor='blue')
    
    ax4.set_title('Volume & VWAP', fontweight='bold')
    ax4.set_ylabel('Volume')
    ax4.legend(loc='upper left', fontsize=8)
    ax4_twin.legend(loc='upper right', fontsize=8)
    ax4.grid(True, alpha=0.3)
    
    # Format x-axis for all subplots
    for ax in [ax1, ax2, ax3, ax4]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.95)
    
    return fig


def print_summary_statistics(data, indicators):
    """Print summary statistics for the analysis."""
    print("\n" + "="*60)
    print("MARKET SENTIMENT ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"\nData Period: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
    print(f"Trading Days: {len(data)}")
    
    # Price statistics
    print(f"\nPrice Statistics:")
    print(f"  Current Price: {data['Close'].iloc[-1]:.2f}")
    print(f"  52-Week High: {data['High'].max():.2f}")
    print(f"  52-Week Low: {data['Low'].min():.2f}")
    print(f"  Average Daily Volume: {data['Volume'].mean():,.0f}")
    
    # Moving averages
    current_sma_50 = indicators['sma_50'].iloc[-1]
    current_sma_200 = indicators['sma_200'].iloc[-1]
    current_price = data['Close'].iloc[-1]
    
    print(f"\nMoving Averages:")
    print(f"  50-day SMA: {current_sma_50:.2f}")
    print(f"  200-day SMA: {current_sma_200:.2f}")
    print(f"  Price vs 50 SMA: {current_price - current_sma_50:+.2f} ({((current_price/current_sma_50 - 1)*100):+.1f}%)")
    print(f"  Price vs 200 SMA: {current_price - current_sma_200:+.2f} ({((current_price/current_sma_200 - 1)*100):+.1f}%)")
    
    # RSI
    current_rsi = indicators['rsi'].iloc[-1]
    print(f"\nRSI (14): {current_rsi:.1f}")
    if current_rsi > 70:
        print("  Signal: OVERBOUGHT")
    elif current_rsi < 30:
        print("  Signal: OVERSOLD")
    else:
        print("  Signal: NEUTRAL")
    
    # MACD
    current_macd = indicators['macd'].iloc[-1]
    current_signal = indicators['signal'].iloc[-1]
    current_hist = indicators['histogram'].iloc[-1]
    
    print(f"\nMACD:")
    print(f"  MACD Line: {current_macd:.4f}")
    print(f"  Signal Line: {current_signal:.4f}")
    print(f"  Histogram: {current_hist:.4f}")
    if current_macd > current_signal:
        print("  Signal: BULLISH crossover")
    else:
        print("  Signal: BEARISH crossover")
    
    # Bollinger Bands
    current_bb_upper = indicators['upper'].iloc[-1]
    current_bb_lower = indicators['lower'].iloc[-1]
    current_bb_middle = indicators['middle'].iloc[-1]
    bb_position = (current_price - current_bb_lower) / (current_bb_upper - current_bb_lower)
    
    print(f"\nBollinger Bands (20, 2):")
    print(f"  Upper Band: {current_bb_upper:.2f}")
    print(f"  Middle Band: {current_bb_middle:.2f}")
    print(f"  Lower Band: {current_bb_lower:.2f}")
    print(f"  Price Position: {bb_position*100:.1f}% in band")
    
    if bb_position > 0.9:
        print("  Signal: NEAR UPPER BAND (potential overbought)")
    elif bb_position < 0.1:
        print("  Signal: NEAR LOWER BAND (potential oversold)")
    else:
        print("  Signal: WITHIN NORMAL RANGE")
    
    # VWAP
    current_vwap = indicators['vwap'].iloc[-1]
    print(f"\nVWAP: {current_vwap:.2f}")
    print(f"  Price vs VWAP: {current_price - current_vwap:+.2f} ({((current_price/current_vwap - 1)*100):+.1f}%)")
    if current_price > current_vwap:
        print("  Signal: ABOVE VWAP (bullish sentiment)")
    else:
        print("  Signal: BELOW VWAP (bearish sentiment)")
    
    print("\n" + "="*60)


def main():
    """Main function to run the sentiment analyser demo."""
    print("Algorithmic Market Sentiment Analyser")
    print("="*40)
    
    # Initialize components
    fetcher = PriceFetcher()
    tech_indicators = TechnicalIndicators()
    
    # Download 2 years of NIFTY 50 data
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')  # 2 years
    
    print(f"\nDownloading NIFTY 50 data...")
    print(f"Period: {start_date} to {end_date}")
    
    try:
        # Fetch data
        data = fetcher.fetch_data('^NSEI', start_date, end_date)
        print(f"✓ Successfully fetched {len(data)} days of data")
        
        # Calculate all indicators
        print("Calculating technical indicators...")
        indicators = tech_indicators.calculate_all_indicators(data)
        print("✓ All indicators calculated successfully")
        
        # Print summary statistics
        print_summary_statistics(data, indicators)
        
        # Create visualization
        print("\nGenerating 4-panel chart...")
        fig = create_four_panel_chart(data, indicators)
        
        # Save the chart
        chart_filename = "nifty_50_analysis.png"
        fig.savefig(chart_filename, dpi=300, bbox_inches='tight')
        print(f"✓ Chart saved as '{chart_filename}'")
        
        # Display the chart
        plt.show()
        
        print(f"\nAnalysis complete! Chart saved and displayed.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
