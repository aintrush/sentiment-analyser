"""
Technical Indicators Module

I implemented these technical analysis indicators myself using just pandas and numpy.
Each one has documentation explaining how it works and what traders use it for.
This was a great learning experience to understand the math behind trading signals.
"""

import pandas as pd
import numpy as np
from typing import Union


class TechnicalIndicators:
    """
    My collection of technical indicators that I coded from scratch.
    I wanted to understand how these really work instead of just using a library.
    
    All the methods take price data and return the calculated indicators.
    """
    
    @staticmethod
    def sma(data: pd.Series, window: int) -> pd.Series:
        """
        Simple Moving Average (SMA)
        
        Formula: SMA = (Sum of prices over window period) / window period
        
        What it measures:
        The average price over a time period, which helps smooth out the 
        day-to-day noise so we can see the bigger trend.
        
        Trading interpretation:
        - Price above SMA suggests bullish momentum
        - Price below SMA suggests bearish momentum
        - SMA crossovers (short-term crossing long-term) signal trend changes
        - The longer the window, the smoother the line but more lag in signals
        
        Args:
            data (pd.Series): Price series (typically Close prices)
            window (int): Number of periods for the moving average
            
        Returns:
            pd.Series: SMA values
        """
        return data.rolling(window=window).mean()
    
    @staticmethod
    def ema(data: pd.Series, window: int) -> pd.Series:
        """
        Exponential Moving Average (EMA)
        
        Formula: EMA = (Close × α) + (Previous EMA × (1 - α))
        where α = 2 / (window + 1)
        
        What it measures:
        Similar to SMA but gives more weight to recent prices, making it
        more responsive to new information while still smoothing volatility.
        
        Trading interpretation:
        - More responsive to recent price changes than SMA
        - EMA crossovers provide earlier signals than SMA crossovers
        - Often used as dynamic support/resistance levels
        - Multiple EMAs (like 12/26) can show momentum shifts
        
        Args:
            data (pd.Series): Price series (typically Close prices)
            window (int): Number of periods for the moving average
            
        Returns:
            pd.Series: EMA values
        """
        alpha = 2 / (window + 1)
        return data.ewm(alpha=alpha, adjust=False).mean()
    
    @staticmethod
    def rsi(data: pd.Series, window: int = 14) -> pd.Series:
        """
        Relative Strength Index (RSI) using Wilder's smoothing method
        
        Formula:
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
        Average Gain = (Previous Average Gain × (window - 1) + Current Gain) / window
        Average Loss = (Previous Average Loss × (window - 1) + Current Loss) / window
        
        What it measures:
        Momentum oscillator that measures the speed and change of price movements.
        Ranges from 0 to 100, showing overbought/oversold conditions.
        
        Trading interpretation:
        - Above 70: Overbought condition (potential sell signal)
        - Below 30: Oversold condition (potential buy signal)
        - 50 line: Centerline, above indicates bullish momentum
        - Divergence with price suggests potential trend reversal
        - Failure swings (higher highs in price but lower highs in RSI) warn of weakness
        
        Args:
            data (pd.Series): Price series (typically Close prices)
            window (int): Period for RSI calculation (default 14)
            
        Returns:
            pd.Series: RSI values (0-100)
        """
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Wilder's smoothing method
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        # First values use simple average, then use Wilder's smoothing
        for i in range(window, len(gain)):
            if i == window:
                continue
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (window - 1) + gain.iloc[i]) / window
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (window - 1) + loss.iloc[i]) / window
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        Moving Average Convergence Divergence (MACD)
        
        Formula:
        MACD Line = EMA(fast) - EMA(slow)
        Signal Line = EMA(MACD Line, signal)
        Histogram = MACD Line - Signal Line
        
        What it measures:
        Trend-following momentum indicator that shows the relationship between
        two moving averages of a security's price. Measures both trend and momentum.
        
        Trading interpretation:
        - MACD line crossing above signal line: Bullish signal
        - MACD line crossing below signal line: Bearish signal
        - Histogram shows momentum strength and direction
        - Zero line crossovers indicate trend changes
        - Divergence between MACD and price warns of potential reversals
        - Histogram growing/shrinking shows momentum acceleration/deceleration
        
        Args:
            data (pd.Series): Price series (typically Close prices)
            fast (int): Fast EMA period (default 12)
            slow (int): Slow EMA period (default 26)
            signal (int): Signal line EMA period (default 9)
            
        Returns:
            pd.DataFrame: Columns ['macd', 'signal', 'histogram']
        """
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        })
    
    @staticmethod
    def bollinger_bands(data: pd.Series, window: int = 20, num_std: float = 2) -> pd.DataFrame:
        """
        Bollinger Bands
        
        Formula:
        Middle Band = SMA(window)
        Upper Band = SMA(window) + (num_std × Standard Deviation)
        Lower Band = SMA(window) - (num_std × Standard Deviation)
        
        What it measures:
        Volatility indicator that creates a price channel around a moving average.
        Bands widen during high volatility and narrow during low volatility.
        
        Trading interpretation:
        - Price touching upper band: Potential overbought condition
        - Price touching lower band: Potential oversold condition
        - Bands narrowing (squeeze): Low volatility, potential breakout coming
        - Bands widening: High volatility, strong trend in progress
        - Price walking the band: Strong trend continuation signal
        - Reversal after band extreme: Potential mean reversion
        
        Args:
            data (pd.Series): Price series (typically Close prices)
            window (int): Period for SMA and standard deviation (default 20)
            num_std (float): Number of standard deviations (default 2)
            
        Returns:
            pd.DataFrame: Columns ['middle', 'upper', 'lower']
        """
        sma = TechnicalIndicators.sma(data, window)
        std = data.rolling(window=window).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        return pd.DataFrame({
            'middle': sma,
            'upper': upper_band,
            'lower': lower_band
        })
    
    @staticmethod
    def vwap(ohlc_data: pd.DataFrame) -> pd.Series:
        """
        Volume-Weighted Average Price (VWAP) - daily rolling
        
        Formula: VWAP = Cumulative(Typical Price × Volume) / Cumulative Volume
        where Typical Price = (High + Low + Close) / 3
        
        What it measures:
        The average price weighted by volume, providing a true average price
        based on both price levels and trading volume throughout the day.
        
        Trading interpretation:
        - Price above VWAP: Bullish sentiment (buyers in control)
        - Price below VWAP: Bearish sentiment (sellers in control)
        - VWAP as support/resistance: Institutional traders often use VWAP levels
        - VWAP crossovers: Potential trend changes
        - Distance from VWAP: Shows strength of move (larger distance = stronger trend)
        - VWAP especially useful for intraday trading and institutional analysis
        
        Args:
            ohlc_data (pd.DataFrame): DataFrame with OHLCV columns
            
        Returns:
            pd.Series: VWAP values
        """
        if not all(col in ohlc_data.columns for col in ['High', 'Low', 'Close', 'Volume']):
            raise ValueError("DataFrame must contain High, Low, Close, and Volume columns")
        
        typical_price = (ohlc_data['High'] + ohlc_data['Low'] + ohlc_data['Close']) / 3
        
        # For daily VWAP, we reset cumulative values each day
        # Group by date to get daily VWAP
        daily_groups = typical_price.groupby(typical_price.index.date)
        volume_groups = ohlc_data['Volume'].groupby(ohlc_data.index.date)
        
        vwap_values = []
        for date in typical_price.index.date:
            daily_tp = daily_groups.get_group(date)
            daily_vol = volume_groups.get_group(date)
            
            cumulative_tp_vol = (daily_tp * daily_vol).cumsum()
            cumulative_volume = daily_vol.cumsum()
            
            daily_vwap = cumulative_tp_vol / cumulative_volume
            vwap_values.extend(daily_vwap.tolist())
        
        return pd.Series(vwap_values, index=typical_price.index)
    
    @staticmethod
    def calculate_all_indicators(ohlc_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators and return them in a single DataFrame.
        
        Args:
            ohlc_data (pd.DataFrame): DataFrame with OHLCV columns
            
        Returns:
            pd.DataFrame: All calculated indicators
        """
        indicators = pd.DataFrame(index=ohlc_data.index)
        
        # Moving averages
        indicators['sma_50'] = TechnicalIndicators.sma(ohlc_data['Close'], 50)
        indicators['sma_200'] = TechnicalIndicators.sma(ohlc_data['Close'], 200)
        indicators['ema_12'] = TechnicalIndicators.ema(ohlc_data['Close'], 12)
        indicators['ema_26'] = TechnicalIndicators.ema(ohlc_data['Close'], 26)
        
        # RSI
        indicators['rsi'] = TechnicalIndicators.rsi(ohlc_data['Close'])
        
        # MACD
        macd_data = TechnicalIndicators.macd(ohlc_data['Close'])
        indicators = pd.concat([indicators, macd_data], axis=1)
        
        # Bollinger Bands
        bb_data = TechnicalIndicators.bollinger_bands(ohlc_data['Close'])
        indicators = pd.concat([indicators, bb_data], axis=1)
        
        # VWAP
        indicators['vwap'] = TechnicalIndicators.vwap(ohlc_data)
        
        return indicators


if __name__ == "__main__":
    # Example usage
    import yfinance as yf
    
    # Download some sample data
    ticker = yf.Ticker("^NSEI")
    data = ticker.history(period="3mo")
    
    # Calculate indicators
    tech_ind = TechnicalIndicators()
    
    # Calculate individual indicators
    data['sma_20'] = tech_ind.sma(data['Close'], 20)
    data['ema_20'] = tech_ind.ema(data['Close'], 20)
    data['rsi'] = tech_ind.rsi(data['Close'])
    
    # Calculate MACD
    macd_data = tech_ind.macd(data['Close'])
    data = pd.concat([data, macd_data], axis=1)
    
    # Calculate Bollinger Bands
    bb_data = tech_ind.bollinger_bands(data['Close'])
    data = pd.concat([data, bb_data], axis=1)
    
    # Calculate VWAP
    data['vwap'] = tech_ind.vwap(data)
    
    print("Technical Indicators Calculated:")
    print(f"Data shape: {data.shape}")
    print(f"Columns: {list(data.columns)}")
    print("\nLast 5 rows:")
    print(data.tail())
