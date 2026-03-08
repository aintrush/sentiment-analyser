"""
Price Data Fetcher Module

I created this module to handle downloading stock data from yfinance and caching it so we don't have to
keep calling the API every time. It also checks if the data looks good before we use it.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple


class PriceFetcher:
    """
    My class for getting stock market data using yfinance. I learned that caching is really important
    because APIs have rate limits and it makes everything run faster.
    
    Attributes:
        cache_dir (str): Where I store the cached data files
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Set up the PriceFetcher with a place to store cached data.
        
        Args:
            cache_dir (str): Folder where I'll save the CSV files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_filename(self, ticker: str, start_date: str, end_date: str) -> str:
        """
        Create a filename for cached data based on the stock and dates.
        
        Args:
            ticker (str): Stock symbol like 'AAPL' or '^NSEI'
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            str: The filename I'll use for caching
        """
        return f"{ticker}_{start_date}_{end_date}.csv".replace("^", "")
    
    def _validate_data(self, df: pd.DataFrame) -> Tuple[bool, list]:
        """
        Check if the downloaded stock data looks okay. I learned that financial data can have
        lots of problems that we need to catch before using it.
        
        Args:
            df (pd.DataFrame): DataFrame with stock data
            
        Returns:
            Tuple[bool, list]: (is_data_good, list_of_problems_found)
        """
        issues = []
        
        # Check if DataFrame is empty
        if df.empty:
            issues.append("DataFrame is empty")
            return False, issues
        
        # Make sure we have all the columns we need
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issues.append(f"Missing columns: {missing_columns}")
        
        # Look for missing values in the data
        null_counts = df[required_columns].isnull().sum()
        if null_counts.any():
            for col, count in null_counts.items():
                if count > 0:
                    issues.append(f"{count} missing values in {col}")
        
        # Check if there are days with no trading volume
        zero_volume_days = (df['Volume'] == 0).sum()
        if zero_volume_days > 0:
            issues.append(f"{zero_volume_days} days with zero volume")
        
        # Make sure the price data makes sense (High should be >= Low)
        invalid_prices = (df['High'] < df['Low']).sum()
        if invalid_prices > 0:
            issues.append(f"{invalid_prices} days with High < Low")
        
        # Prices shouldn't be negative
        negative_prices = (df[['Open', 'High', 'Low', 'Close']] < 0).any().any()
        if negative_prices:
            issues.append("Negative price values detected")
        
        return len(issues) == 0, issues
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fix up the data by filling missing values and making sure dates are in the right format.
        I learned that financial data often has gaps that need to be handled carefully.
        
        Args:
            df (pd.DataFrame): The raw data that needs cleaning
            
        Returns:
            pd.DataFrame: Cleaned data ready to use
        """
        # Don't mess up the original data - make a copy
        df_clean = df.copy()
        
        # Fill missing values with the previous day's data (this is what people usually do)
        df_clean = df_clean.ffill()
        
        # If we still have missing values at the start, fill them with the next day's data
        df_clean = df_clean.bfill()
        
        # Make sure the dates are in datetime format
        if not isinstance(df_clean.index, pd.DatetimeIndex):
            df_clean.index = pd.to_datetime(df_clean.index)
        
        # Sort by date so everything is in order
        df_clean = df_clean.sort_index()
        
        return df_clean
    
    def fetch_data(self, ticker: str, start_date: str, end_date: str, 
                   use_cache: bool = True) -> pd.DataFrame:
        """
        Get stock data for a given stock and time period. I'll try to use cached data first
        to avoid hitting the API limits, but I'll download fresh data if needed.
        
        Args:
            ticker (str): Stock symbol like 'AAPL' or '^NSEI'
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            use_cache (bool): Whether to try using saved data first
            
        Returns:
            pd.DataFrame: Clean stock data with dates as index
            
        Raises:
            ValueError: If something goes wrong with getting the data
        """
        cache_file = os.path.join(self.cache_dir, 
                                  self._get_cache_filename(ticker, start_date, end_date))
        
        # First, let's see if we already have this data saved
        if use_cache and os.path.exists(cache_file):
            try:
                df_cached = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                is_valid, issues = self._validate_data(df_cached)
                if is_valid:
                    print(f"Loaded {ticker} data from cache")
                    return self._clean_data(df_cached)
                else:
                    print(f"Cached data has problems: {issues}")
            except Exception as e:
                print(f"Error reading saved data: {e}")
        
        # If we don't have cached data or it's bad, download fresh data
        print(f"Downloading {ticker} data from yfinance...")
        try:
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=start_date, end=end_date)
            
            if df.empty:
                raise ValueError(f"Couldn't find data for {ticker}")
            
            # Check if the downloaded data looks okay
            is_valid, issues = self._validate_data(df)
            if not is_valid:
                print(f"Data has some issues: {issues}")
            
            # Clean up the data
            df_clean = self._clean_data(df)
            
            # Save to cache
            if use_cache:
                df_clean.to_csv(cache_file)
                print(f"Data cached to {cache_file}")
            
            return df_clean
            
        except Exception as e:
            raise ValueError(f"Failed to download data for {ticker}: {e}")
    
    def get_available_data_range(self, ticker: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get the available date range for a ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (start_date, end_date) or (None, None)
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            start_date = info.get('startDate')
            if start_date:
                start_date = datetime.fromtimestamp(start_date).strftime('%Y-%m-%d')
            
            # For end date, use today or the last trading day
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            return start_date, end_date
        except Exception as e:
            print(f"Error getting data range for {ticker}: {e}")
            return None, None


if __name__ == "__main__":
    # Example usage
    fetcher = PriceFetcher()
    
    # Example: Fetch NIFTY 50 data for the last year
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    try:
        data = fetcher.fetch_data('^NSEI', start_date, end_date)
        print(f"Successfully fetched {len(data)} days of data")
        print(f"Data shape: {data.shape}")
        print(f"Columns: {list(data.columns)}")
        print(f"Date range: {data.index[0]} to {data.index[-1]}")
        print("\nFirst few rows:")
        print(data.head())
    except Exception as e:
        print(f"Error: {e}")
