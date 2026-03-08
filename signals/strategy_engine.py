"""
Strategy Engine Module

I created different trading strategies that generate buy/sell signals based on 
technical indicators. This was really interesting to learn how traders actually 
make decisions based on these indicators.

IMPORTANT: I make sure all signals are generated at the end of the day (T)
and executed the next day at open (T+1) so we don't cheat by using future data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from indicators.technical import TechnicalIndicators


class SignalGenerator:
    """
    My system for generating trading signals using different strategies.
    I learned that it's important to be careful about not using future information.
    
    All signals are: 1 (BUY), -1 (SELL), or 0 (HOLD)
    Signals are decided at market close, but we trade the next day at open.
    """
    
    def __init__(self):
        """Initialize the SignalGenerator with technical indicators calculator."""
        self.tech_ind = TechnicalIndicators()
    
    def moving_average_crossover(self, data: pd.DataFrame, short: int = 50, 
                               long: int = 200) -> pd.Series:
        """
        Moving Average Crossover Strategy (Golden Cross/Death Cross)
        
        Strategy Logic:
        - Golden Cross: Short MA crosses above Long MA → BUY signal (1)
        - Death Cross: Short MA crosses below Long MA → SELL signal (-1)
        - Otherwise: HOLD signal (0)
        
        Look-ahead bias prevention:
        Uses only data available up to current day. Signals generated at close
        for execution next day at open.
        
        Args:
            data (pd.DataFrame): OHLCV data with Close prices
            short (int): Short moving average period (default 50)
            long (int): Long moving average period (default 200)
            
        Returns:
            pd.Series: Trading signals (1=BUY, -1=SELL, 0=HOLD)
        """
        # Calculate moving averages
        short_ma = self.tech_ind.sma(data['Close'], short)
        long_ma = self.tech_ind.sma(data['Close'], long)
        
        # Calculate crossover points
        ma_diff = short_ma - long_ma
        ma_diff_prev = ma_diff.shift(1)
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        # Golden Cross: negative to positive crossover
        signals[(ma_diff_prev <= 0) & (ma_diff > 0)] = 1
        
        # Death Cross: positive to negative crossover  
        signals[(ma_diff_prev >= 0) & (ma_diff < 0)] = -1
        
        return signals
    
    def rsi_mean_reversion(self, data: pd.DataFrame, oversold: float = 30, 
                          overbought: float = 70) -> pd.Series:
        """
        RSI Mean Reversion Strategy
        
        Strategy Logic:
        - Oversold: RSI crosses above oversold level → BUY signal (1)
        - Overbought: RSI crosses below overbought level → SELL signal (-1)
        - Otherwise: HOLD signal (0)
        
        Look-ahead bias prevention:
        RSI calculated only using historical data up to current day.
        
        Args:
            data (pd.DataFrame): OHLCV data with Close prices
            oversold (float): Oversold threshold (default 30)
            overbought (float): Overbought threshold (default 70)
            
        Returns:
            pd.Series: Trading signals (1=BUY, -1=SELL, 0=HOLD)
        """
        # Calculate RSI
        rsi = self.tech_ind.rsi(data['Close'])
        rsi_prev = rsi.shift(1)
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        # Buy signal: RSI crosses above oversold
        signals[(rsi_prev <= oversold) & (rsi > oversold)] = 1
        
        # Sell signal: RSI crosses below overbought
        signals[(rsi_prev >= overbought) & (rsi < overbought)] = -1
        
        return signals
    
    def macd_signal_cross(self, data: pd.DataFrame) -> pd.Series:
        """
        MACD Signal Line Crossover Strategy
        
        Strategy Logic:
        - Bullish crossover: MACD crosses above Signal → BUY signal (1)
        - Bearish crossover: MACD crosses below Signal → SELL signal (-1)
        - Otherwise: HOLD signal (0)
        
        Look-ahead bias prevention:
        MACD and Signal calculated using historical data only.
        
        Args:
            data (pd.DataFrame): OHLCV data with Close prices
            
        Returns:
            pd.Series: Trading signals (1=BUY, -1=SELL, 0=HOLD)
        """
        # Calculate MACD
        macd_data = self.tech_ind.macd(data['Close'])
        macd = macd_data['macd']
        signal = macd_data['signal']
        
        # Calculate previous values for crossover detection
        macd_prev = macd.shift(1)
        signal_prev = signal.shift(1)
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        # Bullish crossover: MACD crosses above Signal
        signals[(macd_prev <= signal_prev) & (macd > signal)] = 1
        
        # Bearish crossover: MACD crosses below Signal
        signals[(macd_prev >= signal_prev) & (macd < signal)] = -1
        
        return signals
    
    def bollinger_breakout(self, data: pd.DataFrame) -> pd.Series:
        """
        Bollinger Bands Breakout Strategy
        
        Strategy Logic:
        - Upper band breakout: Price closes above upper band → BUY signal (1)
        - Lower band breakdown: Price closes below lower band → SELL signal (-1)
        - Otherwise: HOLD signal (0)
        
        Look-ahead bias prevention:
        Bollinger Bands calculated using historical data only.
        
        Args:
            data (pd.DataFrame): OHLCV data with Close prices
            
        Returns:
            pd.Series: Trading signals (1=BUY, -1=SELL, 0=HOLD)
        """
        # Calculate Bollinger Bands
        bb_data = self.tech_ind.bollinger_bands(data['Close'])
        upper_band = bb_data['upper']
        lower_band = bb_data['lower']
        
        # Calculate previous values for breakout detection
        price_prev = data['Close'].shift(1)
        upper_prev = upper_band.shift(1)
        lower_prev = lower_band.shift(1)
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        # Upper band breakout: Price crosses above upper band
        signals[(price_prev <= upper_prev) & (data['Close'] > upper_band)] = 1
        
        # Lower band breakdown: Price crosses below lower band
        signals[(price_prev >= lower_prev) & (data['Close'] < lower_band)] = -1
        
        return signals
    
    def combine_signals(self, data: pd.DataFrame, weights: Dict[str, float] = None) -> pd.Series:
        """
        Combine multiple strategy signals using weighted average.
        
        Strategy Logic:
        - Combines signals from all four strategies
        - Uses weighted average to generate final signal
        - Threshold-based decision making
        
        Look-ahead bias prevention:
        Each individual strategy avoids look-ahead bias, so combined signal does too.
        
        Args:
            data (pd.DataFrame): OHLCV data
            weights (Dict[str, float]): Strategy weights (default: equal weights)
            
        Returns:
            pd.Series: Combined trading signals (1=BUY, -1=SELL, 0=HOLD)
        """
        # Default equal weights if not provided
        if weights is None:
            weights = {
                'ma_crossover': 0.25,
                'rsi_mean_reversion': 0.25,
                'macd_crossover': 0.25,
                'bollinger_breakout': 0.25
            }
        
        # Generate individual strategy signals
        ma_signals = self.moving_average_crossover(data)
        rsi_signals = self.rsi_mean_reversion(data)
        macd_signals = self.macd_signal_cross(data)
        bb_signals = self.bollinger_breakout(data)
        
        # Calculate weighted average
        combined_score = (
            ma_signals * weights['ma_crossover'] +
            rsi_signals * weights['rsi_mean_reversion'] +
            macd_signals * weights['macd_crossover'] +
            bb_signals * weights['bollinger_breakout']
        )
        
        # Convert to discrete signals using thresholds
        signals = pd.Series(0, index=data.index)
        signals[combined_score > 0.3] = 1    # BUY threshold
        signals[combined_score < -0.3] = -1  # SELL threshold
        
        return signals
    
    def generate_all_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals for all strategies and return them in a single DataFrame.
        
        Args:
            data (pd.DataFrame): OHLCV data
            
        Returns:
            pd.DataFrame: All strategy signals
        """
        signals_df = pd.DataFrame(index=data.index)
        
        signals_df['ma_crossover'] = self.moving_average_crossover(data)
        signals_df['rsi_mean_reversion'] = self.rsi_mean_reversion(data)
        signals_df['macd_crossover'] = self.macd_signal_cross(data)
        signals_df['bollinger_breakout'] = self.bollinger_breakout(data)
        signals_df['combined'] = self.combine_signals(data)
        
        return signals_df


if __name__ == "__main__":
    # Example usage
    import yfinance as yf
    
    # Download sample data
    ticker = yf.Ticker("^NSEI")
    data = ticker.history(period="6mo")
    
    # Initialize signal generator
    signal_gen = SignalGenerator()
    
    # Generate all signals
    signals = signal_gen.generate_all_signals(data)
    
    print("Signal Generation Results:")
    print(f"Data shape: {data.shape}")
    print(f"Signals shape: {signals.shape}")
    print(f"\nSignal counts for each strategy:")
    for col in signals.columns:
        buy_count = (signals[col] == 1).sum()
        sell_count = (signals[col] == -1).sum()
        hold_count = (signals[col] == 0).sum()
        print(f"{col}: BUY={buy_count}, SELL={sell_count}, HOLD={hold_count}")
    
    print(f"\nLast 10 signals:")
    print(signals.tail(10))
