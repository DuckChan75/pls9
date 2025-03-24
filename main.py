import os
import requests
import re
import time
import telebot
from datetime import datetime

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Your Telegram bot token
CHANNEL_ID = os.getenv('CHANNEL_ID')  # Your channel ID
INITIAL_PX_PRICE = 0.30  # Starting price for % calculations
SECONDARY_PX_PRICE = 0.20  # Secondary reference price

bot = telebot.TeleBot(BOT_TOKEN)

def format_price(price, coin):
    """Formats price with correct decimal places"""
    return f"{price:.4f}" if coin == "px" else f"{price:.2f}"

def sync_to_53rd_second():
    """Aligns execution with the next :53 second mark"""
    now = datetime.now()
    current_second = now.second
    if current_second < 53:
        time.sleep(53 - current_second)
    else:
        time.sleep(60 - current_second + 53)

def fetch_prices():
    """Gets current prices from CoinMarketCap"""
    try:
        # Fetch PX price
        px_response = requests.get(
            "https://coinmarketcap.com/currencies/not-pixel/", 
            timeout=10
        )
        px_price = float(re.search(r'"price":"([\d.]+)"', px_response.text).group(1))
        
        # Fetch TON price
        ton_response = requests.get(
            "https://coinmarketcap.com/currencies/toncoin/", 
            timeout=10
        )
        ton_price = float(re.search(r'"price":"([\d.]+)"', ton_response.text).group(1))
        
        return px_price, ton_price
    except Exception as e:
        print(f"Error fetching prices: {e}")
        return None, None

def calculate_percentage(initial, current):
    """Calculates percentage change"""
    return ((current - initial) / initial) * 100

def create_message(px_price, ton_price):
    """Generates the formatted message"""
    high_loss = calculate_percentage(INITIAL_PX_PRICE, px_price)
    mid_loss = calculate_percentage(SECONDARY_PX_PRICE, px_price)
    
    return f"""
$PX *{format_price(px_price, 'px')}$*
From 0.3$ = {high_loss:.2f}%
From 0.2$ = {mid_loss:.2f}%

$TON *{format_price(ton_price, 'ton')}$*
"""

def main():
    while True:
        sync_to_53rd_second()  # Wait until :53
        
        px, ton = fetch_prices()
        if px and ton:  # Only proceed if we got both prices
            message = create_message(px, ton)
            bot.send_message(CHANNEL_ID, message, parse_mode="Markdown")
        
        time.sleep(1)  # Brief pause before next cycle

if __name__ == "__main__":
    main()
