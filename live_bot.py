import os
import time
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from data_engine import fetch_crypto_data
from strategy_engine import calculate_atr, calculate_donchian_channels, detect_signals_and_stops

# 1. Initialize the Alpaca Live Broker
load_dotenv()
API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")

# paper=True ensures this connects strictly to your sandbox simulation
broker = TradingClient(API_KEY, API_SECRET, paper=True) 

SYMBOL = "BTC/USD"
TRADE_QTY = 0.1  # The amount of Bitcoin to trade (adjust based on your paper balance)

def get_current_state():
    """Asks Alpaca for our physical portfolio state to prevent double-buying."""
    try:
        position = broker.get_open_position(SYMBOL)
        if float(position.qty) > 0:
            return "LONG"
        elif float(position.qty) < 0:
            return "SHORT"
    except Exception:
        # If Alpaca throws an error, it means the position doesn't exist (we are flat)
        return "FLAT"

def execute_trade(side, qty):
    """Sends the physical API command to Alpaca to execute a market order."""
    print(f"\n🚀 FIRE THE WEAPONS: Executing {side} for {qty} {SYMBOL}...")
    order_data = MarketOrderRequest(
        symbol=SYMBOL,
        qty=qty,
        side=side,
        time_in_force=TimeInForce.GTC
    )
    broker.submit_order(order_data=order_data)
    print("✅ Order successfully filled by Alpaca!")

def run_state_machine():
    """The 24/7 heartbeat of the trading bot."""
    print("--- 🤖 Crypto Quant State Machine Initialized ---")
    
    while True:
        try:
            # 1. Check current physical state
            state = get_current_state()
            print(f"\n[{pd.Timestamp.now(tz='UTC')}] Waking up. Current State: {state}")
            
            # 2. Pull the newest data and calculate the optimized math
            df = fetch_crypto_data(days_back=30)
            df = calculate_atr(df)
            df = calculate_donchian_channels(df, period=60)
            df = detect_signals_and_stops(df, atr_multiplier=5.0)
            
            # 3. Get the absolute latest closed hourly candle
            latest_candle = df.iloc[-1]
            current_price = latest_candle['close']
            print(f"Bitcoin Price: ${current_price:,.2f} | 60-Hr Ceiling: ${latest_candle['donchian_high']:,.2f} | Squeeze: {latest_candle['squeeze_on']}")
            
            # --- THE LOGIC ROUTER ---
            if state == "FLAT":
                if latest_candle['long_signal']:
                    execute_trade(OrderSide.BUY, TRADE_QTY)
                elif latest_candle['short_signal']:
                    execute_trade(OrderSide.SELL, TRADE_QTY)
                else:
                    print("No anomaly detected. Remaining in cash.")
                    
            elif state == "LONG":
                print(f"Trailing Stop Safety Net: ${latest_candle['long_stop_loss']:,.2f}")
                if current_price <= latest_candle['long_stop_loss']:
                    print("🚨 TREND BROKEN: Trailing stop hit!")
                    execute_trade(OrderSide.SELL, TRADE_QTY) # Sell to close
                    
            elif state == "SHORT":
                print(f"Trailing Stop Safety Net: ${latest_candle['short_stop_loss']:,.2f}")
                if current_price >= latest_candle['short_stop_loss']:
                    print("🚨 TREND BROKEN: Trailing stop hit!")
                    execute_trade(OrderSide.BUY, TRADE_QTY) # Buy to cover
            
            # 4. Go back to sleep for 60 minutes
            print("💤 Sleeping for 1 hour...")
            time.sleep(3600)
            
        except Exception as e:
            print(f"⚠️ Warning: Connection glitch. {e}")
            time.sleep(60) # If the Wi-Fi drops, wait a minute and try again

if __name__ == "__main__":
    import pandas as pd # Imported here just for the timestamp printing
    run_state_machine()