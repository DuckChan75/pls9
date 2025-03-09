import os
import requests
import time
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Telegram bot token
CHANNEL_ID = os.getenv('CHANNEL_ID')  # Telegram channel ID
CMC_API_KEY = os.getenv('CMC_API_KEY')  # CoinMarketCap API key
INITIAL_PX_PRICE = float(os.getenv('INITIAL_PX_PRICE', 0.30))  # Initial price of $PX

# CoinMarketCap symbols for the cryptocurrencies
COIN_SYMBOLS = ["PX", "TON"]

# Function to fetch the price of a cryptocurrency using CoinMarketCap API
def fetch_crypto_price(symbol):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"symbol": symbol, "convert": "USD"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["data"][symbol]["quote"]["USD"]["price"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {symbol} price: {e}")
        return None

# Function to calculate percentage change
def calculate_percentage_change(current_price, previous_price):
    if previous_price is None or previous_price == 0:
        return 0
    return ((current_price - previous_price) / previous_price) * 100

# Function to determine emoji indicator based on percentage change
def get_emoji_indicator(percentage_change):
    if abs(percentage_change) < 0.01:
        return "➖"  # Stable
    elif abs(percentage_change) < 1:
        return "📈" if percentage_change > 0 else "📉"  # Small change
    elif abs(percentage_change) < 5:
        return "🚀" if percentage_change > 0 else "🛑"  # Medium change
    else:
        return "🔥" if percentage_change > 0 else "💥"  # Large change

# Function to send message to the channel
def send_message_to_channel(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": message}

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending message: {e}")
        return None

# Function to wait until the last second of the current minute
def wait_until_last_second():
    now = datetime.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    last_second = next_minute - timedelta(seconds=1)  # XX:59
    wait_time = (last_second - now).total_seconds()
    if wait_time > 0:
        time.sleep(wait_time)

# Main loop to send the price every minute
def main():
    previous_prices = {coin: None for coin in COIN_SYMBOLS}  # Track previous prices
    last_sent_message = None  # To prevent duplicate messages

    while True:
        wait_until_last_second()  # Wait until the last second of the current minute

        # Fetch prices
        prices = {}
        for symbol in COIN_SYMBOLS:
            prices[symbol] = fetch_crypto_price(symbol)

        if all(prices.values()):  # Ensure all prices were fetched successfully
            # Calculate percentage changes
            changes = {}
            for symbol, current_price in prices.items():
                previous_price = previous_prices[symbol]
                changes[symbol] = calculate_percentage_change(current_price, previous_price)

            # Prepare the message
            message_lines = []
            for symbol, current_price in prices.items():
                if symbol == "PX":
                    loss_percentage = calculate_percentage_change(current_price, INITIAL_PX_PRICE)
                    message_lines.append(f"$PX {current_price:.4f}$ | {loss_percentage:.2f}% {get_emoji_indicator(changes[symbol])}")
                else:
                    message_lines.append(f"$TON {current_price:.2f}$ {get_emoji_indicator(changes[symbol])}")

            message = "\n\n".join(message_lines)

            # Send the message only if it's different from the last one
            if message != last_sent_message:
                send_message_to_channel(message)
                last_sent_message = message  # Update last sent message

            # Update previous prices
            previous_prices.update(prices)
        else:
            logger.error("Failed to fetch prices, retrying in 10 seconds...")
            time.sleep(10)  # Wait before retrying

if __name__ == "__main__":
    main()
