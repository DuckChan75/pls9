import os
import requests
import re
import json
import time
import telebot
from datetime import datetime

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Your bot token
CHANNEL_ID = os.getenv('CHANNEL_ID')  # Your channel ID
INITIAL_PX_PRICE = float(os.getenv('INITIAL_PX_PRICE', 0.30))  # Initial price of $PX
SECONDARY_PX_PRICE = float(os.getenv('SECONDARY_PX_PRICE', 0.20))  # Secondary price of $PX

bot = telebot.TeleBot(BOT_TOKEN)
chat_id = CHANNEL_ID

def calculate_loss_percentage(initial_price, current_price):
    loss = initial_price - current_price
    loss_percentage = (loss / initial_price) * 100
    return loss_percentage

def format_price(price, coin_name):
    if coin_name == "px": 
        return f"{price:.4f}"  # Format to 4 decimal places for $PX
    elif coin_name == "ton": 
        return f"{price:.2f}"  # Format to 2 decimal places for $TON
    else:
        return str(price)  # Default format

def send_message_at_53rd_second():
    now = datetime.now()
    current_second = now.second
    if current_second < 53:
        delay = 53 - current_second
    else:
        delay = 60 - current_second + 53
    time.sleep(delay)

def get_coin_price(html_content):
    """Extract price from the statistics JSON in the HTML content"""
    match = re.search(r'"statistics":(\{.*?\})', html_content)
    if match:
        try:
            statistics = json.loads(match.group(1))
            return float(statistics.get("price", 0))
        except (json.JSONDecodeError, ValueError):
            pass
    return None

while True:
    try:
        # Fetch data
        px_response = requests.get("https://coinmarketcap.com/currencies/not-pixel/", timeout=10)
        ton_response = requests.get("https://coinmarketcap.com/currencies/toncoin/", timeout=10)

        if px_response.status_code != 200 or ton_response.status_code != 200:
            print("Failed to retrieve data")
            time.sleep(60)
            continue

        # Get current prices
        px_price = get_coin_price(px_response.text)
        ton_price = get_coin_price(ton_response.text)

        if px_price is None or ton_price is None:
            print("Couldn't extract prices from the responses")
            time.sleep(60)
            continue

        # Calculate loss percentages
        loss_initial = calculate_loss_percentage(INITIAL_PX_PRICE, px_price)
        loss_secondary = calculate_loss_percentage(SECONDARY_PX_PRICE, px_price)

        # Format the message
        message_text = f"""
$PX *{format_price(px_price, "px")}$*
From 0.3$ = -{loss_initial:.2f}% 
From 0.2$ = -{loss_secondary:.2f}%

$TON *{format_price(ton_price, "ton")}$*
"""

        # Send at the 53rd second
        send_message_at_53rd_second()

        # Send to Telegram
        bot.send_message(chat_id=chat_id, text=message_text, parse_mode="Markdown")

    except Exception as e:
        print(f"An error occurred: {e}")

    time.sleep(1)
