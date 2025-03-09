import os
import requests
import time
from datetime import datetime, timedelta

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Your bot token
CHANNEL_ID = os.getenv('CHANNEL_ID')  # Your channel ID
CMC_API_KEY = os.getenv('CMC_API_KEY')  # CoinMarketCap API key
INITIAL_PX_PRICE = float(os.getenv('INITIAL_PX_PRICE', 0.30))  # Initial price of $PX

# Validate API key
if not CMC_API_KEY:
    raise ValueError("CMC_API_KEY environment variable is missing!")

# Function to fetch the price of a cryptocurrency using CoinMarketCap API
def fetch_crypto_price(symbol):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': CMC_API_KEY
    }
    params = {
        'symbol': symbol  # Fetch price by symbol (e.g., PX, TON)
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['data'][symbol]['quote']['USD']['price']
    else:
        print(f"Error fetching {symbol} price: {response.status_code} - {response.text}")
        return None

# Function to calculate percentage change
def calculate_percentage_change(current_price, initial_price):
    return ((current_price - initial_price) / initial_price) * 100

# Function to send message to the channel
def send_message_to_channel(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHANNEL_ID,
        'text': message
    }
    response = requests.post(url, json=payload)
    return response.json()

# Function to wait until the next round minute
def wait_until_next_minute():
    now = datetime.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    wait_time = (next_minute - now).total_seconds()
    time.sleep(wait_time)

# Main loop to send the price every minute
def main():
    previous_px_price = None  # Track previous price for $PX
    previous_ton_price = None  # Track previous price for $TON

    # Wait until the next round minute to start
    wait_until_next_minute()

    while True:
        # Fetch prices
        px_price = fetch_crypto_price('PX')
        ton_price = fetch_crypto_price('TON')

        if px_price is not None and ton_price is not None:
            # Calculate percentage loss for $PX
            px_loss_percentage = calculate_percentage_change(px_price, INITIAL_PX_PRICE)

            # Prepare the message
            message = (
                f"$PX {px_price:.4f}$ | {px_loss_percentage:.2f}%\n\n"
                f"$TON {ton_price:.2f}$"
            )

            # Send the message
            send_message_to_channel(message)

            # Check for price change alert (5% threshold)
            if previous_px_price is not None:
                px_price_change = calculate_percentage_change(px_price, previous_px_price)
                if abs(px_price_change) >= 5:
                    alert_message = f"🚨 $PX Price Alert: {px_price_change:.2f}%!"
                    send_message_to_channel(alert_message)

            # Update previous prices
            previous_px_price = px_price
            previous_ton_price = ton_price
        else:
            print("Failed to fetch prices")

        # Wait until the next round minute
        wait_until_next_minute()

if __name__ == "__main__":
    main()
