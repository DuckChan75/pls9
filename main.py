import os
import requests
import time
from datetime import datetime, timedelta

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Telegram bot token
CHANNEL_ID = os.getenv('CHANNEL_ID')  # Telegram channel ID
CMC_API_KEY = os.getenv('CMC_API_KEY')  # CoinMarketCap API key
INITIAL_PX_PRICE = float(os.getenv('INITIAL_PX_PRICE', 0.30))  # Initial price of $PX

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
        print(f"Error fetching {symbol} price: {e}")
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
        print(f"Error sending message: {e}")
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
    previous_px_price = None  # Previous price of $PX
    previous_ton_price = None  # Previous price of $TON
    last_sent_message = None  # To prevent duplicate messages

    while True:
        wait_until_last_second()  # Wait until the last second of the current minute

        # Fetch prices
        px_price = fetch_crypto_price("PX")  # Replace with correct symbol if needed
        ton_price = fetch_crypto_price("TON")  # Replace with correct symbol if needed

        if px_price is not None and ton_price is not None:
            # Calculate percentage loss for $PX (compared to initial price)
            px_loss_percentage = calculate_percentage_change(px_price, INITIAL_PX_PRICE)

            # Calculate percentage change for $PX
            px_change_percentage = calculate_percentage_change(px_price, previous_px_price) if previous_px_price else 0
            px_emoji = get_emoji_indicator(px_change_percentage)

            # Calculate percentage change for $TON
            ton_change_percentage = calculate_percentage_change(ton_price, previous_ton_price) if previous_ton_price else 0
            ton_emoji = get_emoji_indicator(ton_change_percentage)

            # Prepare the message
            message = (
                f"$PX {px_price:.4f}$ | {px_loss_percentage:.2f}% {px_emoji}\n\n"
                f"$TON {ton_price:.2f}$ {ton_emoji}"
            )

            # Send the message only if it's different from the last one
            if message != last_sent_message:
                send_message_to_channel(message)
                last_sent_message = message  # Update last sent message

            # Update previous prices
            previous_px_price = px_price
            previous_ton_price = ton_price
        else:
            print("Failed to fetch prices, retrying in 10 seconds...")
            time.sleep(10)  # Wait before retrying

if __name__ == "__main__":
    main()
