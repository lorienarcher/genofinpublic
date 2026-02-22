import ccxt
import pandas as pd

# Function to fetch missing data and append it to the CSV
def update_csv_with_recent_data(csv_file, symbol, timeframe, exchange):
    # Load existing data
    df = pd.read_csv(csv_file)
    df['Time'] = pd.to_datetime(df['Time'])  # Update to use 'Time' column

    # Get the last timestamp in the CSV
    last_timestamp = int(df['Time'].iloc[-1].timestamp() * 1000)

    # Fetch new data from the exchange
    since = last_timestamp + 1  # Start fetching after the last timestamp
    all_new_data = []

    while True:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        if not ohlcv:
            break

        all_new_data.extend(ohlcv)
        since = ohlcv[-1][0] + 1  # Update the `since` to the last fetched timestamp + 1 ms

    if not all_new_data:
        print("No new data to update.")
        return

    # Convert new data to a DataFrame, excluding Volume
    new_data = pd.DataFrame(all_new_data, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
    new_data = new_data[['Time', 'Open', 'High', 'Low', 'Close']]  # Drop the 'Volume' column
    new_data['Time'] = pd.to_datetime(new_data['Time'], unit='ms')

    # Append the new data to the existing DataFrame and save to CSV
    updated_df = pd.concat([df, new_data], ignore_index=True)
    updated_df.to_csv(csv_file, index=False)
    print(f"Updated {csv_file} with {len(new_data)} new rows.")

# Initialize ccxt Binance Futures exchange
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},  # Use futures market
})

# Update the CSV file with the missing data
csv_file = "btc_usdt_1m.csv"
symbol = "BTC/USDT"
timeframe = "1m"

update_csv_with_recent_data(csv_file, symbol, timeframe, exchange)
