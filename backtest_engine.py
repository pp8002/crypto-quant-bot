import pandas as pd
from strategy_engine import calculate_atr, calculate_donchian_channels, detect_signals_and_stops
from data_engine import fetch_crypto_data

def run_backtest(df, initial_capital=10000):
    """Simulates trading the Secret Sauce over historical data."""
    capital = initial_capital
    position = None  # Can be 'LONG' or 'SHORT'
    entry_price = 0
    stop_loss = 0
    trade_log = []

    print(f"🏦 Starting Backtest with ${initial_capital:,.2f}...\n")

    for index, row in df.iterrows():
        # --- 1. MANAGE ACTIVE POSITIONS ---
        if position == 'LONG':
            # Check if we got stopped out
            if row['low'] <= stop_loss:
                profit_pct = (stop_loss - entry_price) / entry_price
                profit_usd = capital * profit_pct
                capital += profit_usd
                trade_log.append({'Type': 'LONG', 'Entry': entry_price, 'Exit': stop_loss, 'Profit %': profit_pct*100})
                position = None
            else:
                # THE RATCHET: Move stop loss UP if the new trailing stop is higher
                stop_loss = max(stop_loss, row['long_stop_loss'])

        elif position == 'SHORT':
            # Check if we got stopped out
            if row['high'] >= stop_loss:
                profit_pct = (entry_price - stop_loss) / entry_price
                profit_usd = capital * profit_pct
                capital += profit_usd
                trade_log.append({'Type': 'SHORT', 'Entry': entry_price, 'Exit': stop_loss, 'Profit %': profit_pct*100})
                position = None
            else:
                # THE RATCHET: Move stop loss DOWN if the new trailing stop is lower
                stop_loss = min(stop_loss, row['short_stop_loss'])

        # --- 2. LOOK FOR NEW ENTRIES (Only if we have no active position) ---
        if position is None:
            if row['long_signal']:
                position = 'LONG'
                entry_price = row['close']
                stop_loss = row['long_stop_loss']
            elif row['short_signal']:
                position = 'SHORT'
                entry_price = row['close']
                stop_loss = row['short_stop_loss']

    # --- 3. PRINT RESULTS ---
    print(f"🏁 Backtest Complete!")
    print(f"Total Trades Taken: {len(trade_log)}")
    print(f"Final Account Balance: ${capital:,.2f}")
    
    if len(trade_log) > 0:
        winning_trades = len([t for t in trade_log if t['Profit %'] > 0])
        win_rate = (winning_trades / len(trade_log)) * 100
        print(f"Win Rate: {win_rate:.2f}%")
        
        print("\n--- Last 5 Trades ---")
        trades_df = pd.DataFrame(trade_log)
        print(trades_df.tail())

if __name__ == "__main__":
    # 1. Pull Data
    btc_data = fetch_crypto_data(days_back=60)
    
   # 2. Apply the Math Engine
    df = calculate_atr(btc_data)
    
    # Injecting the optimized 60-hour ceiling
    df = calculate_donchian_channels(df, period=60)
    
    # Injecting the optimized 5.0x ATR safety net
    df = detect_signals_and_stops(df, atr_multiplier=5.0)
    
    # 3. Run the Simulation
    run_backtest(df)