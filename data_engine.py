import os
import pandas as pd
from dotenv import load_dotenv
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame

# 1. Load Environment Variables
load_dotenv()
API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")

# 2. Initialize the Crypto Data Client
# Note: Crypto data doesn't strictly require keys, but passing them massively increases your rate limit.
client = CryptoHistoricalDataClient(api_key=API_KEY, secret_key=API_SECRET)

def fetch_crypto_data(symbol="BTC/USD", days_back=30):
    """Fetches hourly candlestick data for our breakout strategy."""
    print(f"📡 Pulling {days_back} days of 1-Hour data for {symbol}...")
    
    # Calculate the exact start date based on how many days back we want
    start_time = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=days_back)
    
    # 3. Create the Request Object
    request_params = CryptoBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TimeFrame.Hour, 
        start=start_time
    )
    
    # 4. Fetch the Data
    bars = client.get_crypto_bars(request_params)
    
    # Convert Alpaca's raw response into a clean Pandas DataFrame
    df = bars.df
    return df

if __name__ == "__main__":
    print("--- Crypto Data Engine Initialized ---")
    btc_data = fetch_crypto_data()
    
    print("\n✅ Data Successfully Ingested! Here are the 5 most recent hourly candles:")
    print(btc_data.tail())