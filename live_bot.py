import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from data_engine import fetch_crypto_data
from strategy_engine import calculate_atr, calculate_donchian_channels, detect_signals_and_stops

# 1. Initialize
load_dotenv()
API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

broker = TradingClient(API_KEY, API_SECRET, paper=True) 

SYMBOL = "BTC/USD"
TRADE_QTY = 0.1 

def send_telegram_msg(message):
    """Sends a notification to your phone via Telegram."""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={message}"
        try:
            requests.get(url)
        except Exception as e:
            print(f"Telegram Failed: {e}")

def get_current_state():
    try:
        position = broker.get_open_position(SYMBOL)
        if float(position.qty) > 0: return "LONG"
        elif float(position.qty) < 0: return "SHORT"
    except Exception:
        return "FLAT"

def execute_trade(side, qty):
    alert_msg = f"🚀 FIRE THE WEAPONS: Executing {side} for {qty} {SYMBOL}..."
    print(f"\n{alert_msg}")
    send_telegram_msg(alert_msg) # Added Telegram Alert here!
    
    order_data = MarketOrderRequest(
        symbol=SYMBOL, qty=qty, side=side, time_in_force=TimeInForce.GTC
    )
    broker.submit_order(order_data=order_data)
    
    confirm_msg = "✅ Order successfully filled by Alpaca!"
    print(confirm_msg)
    send_telegram_msg(confirm_msg) # Added Telegram Alert here!

def run_state_machine():
    startup_msg = "--- 🤖 Crypto Quant State Machine Initialized ---"
    print(startup_msg)
    send_telegram_msg(startup_msg) # Tell your phone the bot is awake!
    
    while True:
        try:
            state = get_current_state()
            timestamp = pd.Timestamp.now(tz='UTC')
            print(f"\n[{timestamp}] Waking up. Current State: {state}")
            
            df = fetch_crypto_data(days_back=30)
            df = calculate_atr(df)
            df = calculate_donchian_channels(df, period=60)
            df = detect_signals_and_stops(df, atr_multiplier=5.0)
            
            latest_candle = df.iloc[-1]
            current_price = latest_candle['close']
            
            status_report = (
                f"🤖 Bot Status Report\n"
                f"BTC: ${current_price:,.2f}\n"
                f"60-Hr Ceiling: ${latest_candle['donchian_high']:,.2f}\n"
                f"Squeeze: {latest_candle['squeeze_on']}"
            )
            print(status_report)
            send_telegram_msg(status_report)

            if state == "FLAT":
                if latest_candle['long_signal']:
                    execute_trade(OrderSide.BUY, TRADE_QTY)
                elif latest_candle['short_signal']:
                    execute_trade(OrderSide.SELL, TRADE_QTY)
                else:
                    print("No anomaly detected. Remaining in cash.")
                    no_trade_msg = "No anomaly detected. Remaining in cash."
                    print(no_trade_msg)
                    send_telegram_msg(no_trade_msg)
            elif state == "LONG":
                if current_price <= latest_candle['long_stop_loss']:
                    execute_trade(OrderSide.SELL, TRADE_QTY)
            elif state == "SHORT":
                if current_price >= latest_candle['short_stop_loss']:
                    execute_trade(OrderSide.BUY, TRADE_QTY)
            
            print("💤 Sleeping for 1 hour...")
            time.sleep(3600)
            
        except Exception as e:
            error_msg = f"⚠️ Warning: Connection glitch. {e}"
            print(error_msg)
            send_telegram_msg(error_msg)
            time.sleep(60)

if __name__ == "__main__":
    run_state_machine()