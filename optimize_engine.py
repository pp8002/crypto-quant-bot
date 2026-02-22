import pandas as pd
import itertools
from strategy_engine import calculate_atr, calculate_donchian_channels, detect_signals_and_stops
from data_engine import fetch_crypto_data

def run_backtest_silent(df, initial_capital=10000):
    """A silent version of our backtest engine that just returns the final metrics."""
    capital = initial_capital
    position = None 
    entry_price = 0
    stop_loss = 0
    trades = 0

    for index, row in df.iterrows():
        # Manage Active Positions
        if position == 'LONG':
            if row['low'] <= stop_loss:
                capital += capital * ((stop_loss - entry_price) / entry_price)
                position = None
                trades += 1
            else:
                stop_loss = max(stop_loss, row['long_stop_loss'])

        elif position == 'SHORT':
            if row['high'] >= stop_loss:
                capital += capital * ((entry_price - stop_loss) / entry_price)
                position = None
                trades += 1
            else:
                stop_loss = min(stop_loss, row['short_stop_loss'])

        # Look for New Entries
        if position is None:
            if row['long_signal']:
                position = 'LONG'
                entry_price = row['close']
                stop_loss = row['long_stop_loss']
            elif row['short_signal']:
                position = 'SHORT'
                entry_price = row['close']
                stop_loss = row['short_stop_loss']

    return capital, trades

if __name__ == "__main__":
    print("--- ⚙️ Initializing Grid Search Optimization ---")
    
    # 1. Pull 90 days of data (more data = better optimization)
    btc_data = fetch_crypto_data(days_back=90)
    
    # 2. Define the Grid (The parameters we want to test)
    # Donchian Ceilings: 20 hours to 80 hours (looking for bigger trends)
    donchian_periods = [20, 40, 60, 80] 
    # ATR Multipliers: 2.0x to 5.0x (giving Bitcoin more breathing room)
    atr_multipliers = [2.0, 3.0, 4.0, 5.0] 
    
    # Generate all possible combinations
    combinations = list(itertools.product(donchian_periods, atr_multipliers))
    print(f"🔍 Brute-forcing {len(combinations)} different mathematical models...\n")
    
    best_capital = 0
    best_params = None
    results = []

    # 3. The Brute Force Loop
    for donchian, atr_mult in combinations:
        # Create a fresh copy of the data for each test
        df = btc_data.copy()
        
        # Apply the math with the current combination's settings
        df = calculate_atr(df)
        df = calculate_donchian_channels(df, period=donchian)
        df = detect_signals_and_stops(df, atr_multiplier=atr_mult)
        
        # Run the silent simulation
        final_capital, total_trades = run_backtest_silent(df)
        
        results.append({
            'Donchian_Period': donchian,
            'ATR_Multiplier': atr_mult,
            'Final_Balance': final_capital,
            'Total_Trades': total_trades
        })
        
        # Keep track of the winner
        if final_capital > best_capital:
            best_capital = final_capital
            best_params = (donchian, atr_mult)

    # 4. Print the Leaderboard
    results_df = pd.DataFrame(results)
    # Sort by who made the most money
    results_df = results_df.sort_values(by='Final_Balance', ascending=False)
    
    print("🏆 OPTIMIZATION COMPLETE! Here are the Top 5 Models:")
    print(results_df.head())
    
    print(f"\n💡 THE OPTIMAL HEARTBEAT:")
    print(f"To mine the absolute most profit, Bitcoin requires a {best_params[0]}-hour breakout ceiling and a {best_params[1]}x ATR trailing stop.")