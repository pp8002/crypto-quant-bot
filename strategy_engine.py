import pandas as pd
import numpy as np
from data_engine import fetch_crypto_data

def calculate_atr(df, period=14):
    """Calculates the Average True Range (ATR) to measure volatility."""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift(1))
    low_close = np.abs(df['low'] - df['close'].shift(1))
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    
    df['atr'] = true_range.rolling(window=period).mean()
    return df

def calculate_donchian_channels(df, period=20):
    """Calculates the Donchian Channels (Rolling Highs and Lows)."""
    df['donchian_high'] = df['high'].rolling(window=period).max()
    df['donchian_low'] = df['low'].rolling(window=period).min()
    return df

def detect_signals_and_stops(df, atr_sma_period=30, atr_multiplier=2.0):
    """
    Upgraded Secret Sauce: Longs, Shorts, and Trailing Exits
    """
    # 1. The Squeeze Detector
    df['atr_sma'] = df['atr'].rolling(window=atr_sma_period).mean()
    df['squeeze_on'] = df['atr'] < df['atr_sma']
    
    # 2. THE ENTRY BRAIN (Dual Directional)
    # Long: Squeeze is on AND price pierces the Donchian High ceiling
    df['long_signal'] = (df['squeeze_on'].shift(1) == True) & (df['close'] > df['donchian_high'].shift(1))
    
    # Short: Squeeze is on AND price pierces the Donchian Low floor
    df['short_signal'] = (df['squeeze_on'].shift(1) == True) & (df['close'] < df['donchian_low'].shift(1))
    
    # 3. THE EXIT BRAIN (Dynamic Safety Nets)
    # Long Stop Loss: Trails safely below the current price action
    df['long_stop_loss'] = df['close'] - (df['atr'] * atr_multiplier)
    
    # Short Stop Loss: Trails safely above the current price action
    df['short_stop_loss'] = df['close'] + (df['atr'] * atr_multiplier)
    
    return df

if __name__ == "__main__":
    print("--- Strategy Engine Initialized ---")
    
    # Pulling 60 days of data so we have enough history to calculate the moving averages
    btc_data = fetch_crypto_data(days_back=60)
    
    print("🧮 Calculating Volatility (ATR)...")
    df = calculate_atr(btc_data)
    
    print("📈 Calculating Donchian Channels...")
    df = calculate_donchian_channels(df)
    
    print("🔥 Injecting the Secret Sauce (Squeeze & Breakout Logic)...")
    df = detect_signals_and_stops(df)
    
    # Check if the bot found any historical signals
    recent_signals = df[df['long_signal'] == True]
    
    if len(recent_signals) > 0:
        print(f"\n🚨 FOUND {len(recent_signals)} HISTORICAL BREAKOUT SIGNALS! Here are the 3 most recent:")
        print(recent_signals[['close', 'atr', 'donchian_high', 'squeeze_on', 'long_signal', 'long_stop_loss']].tail(3))
    else:
        print("\n⏳ No breakout signals detected in this timeframe. The market has not squeezed.")