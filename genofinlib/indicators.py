import pandas as pd
import pandas_ta as ta


def calculate_rsi_candles(df: pd.DataFrame, length: int = 6):
    """
    [SANITIZED] 
    Proprietary RSI projection and Wilder's Smoothing logic removed.
    Replaced with generic RSI placeholders to maintain system structure.
    """
    df_copy = df.copy()
    
    # Standard RSI fallback
    standard_rsi = ta.rsi(df_copy['close'], length=length)
    
    # Fill required columns with basic standard RSI to prevent downstream structural breaks
    df_copy['rsi_open'] = standard_rsi
    df_copy['rsi_high'] = standard_rsi
    df_copy['rsi_low'] = standard_rsi
    df_copy['rsi_close'] = standard_rsi

    return df_copy.fillna(100)


def normalized_atr(df, length):
    """
    [SANITIZED]
    Custom true range normalization and smoothing logic removed.
    Replaced with standard Average True Range calculation.
    """
    # Standard fallback ATR
    return ta.atr(df['high'], df['low'], df['close'], length=length)


def supertrend(close, high, low, length, multiplier):
    """
    Standard Supertrend wrapper using pandas_ta.
    """
    return ta.supertrend(high=high, low=low, close=close, length=length, multiplier=multiplier)
