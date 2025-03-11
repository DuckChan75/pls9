import os
import requests
import re
import json
import time
import telebot

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Your bot token
CHANNEL_ID = os.getenv('CHANNEL_ID')  # Your channel ID
INITIAL_PX_PRICE = float(os.getenv('INITIAL_PX_PRICE', 0.30))  # Initial price of $PX

bot = telebot.TeleBot(BOT_TOKEN)
chat_id = CHANNEL_ID
previous_price = INITIAL_PX_PRICE

def calculate_loss_percentage(initial_price, current_price):
    loss = initial_price - current_price
    loss_percentage = (loss / initial_price) * 100
    return loss_percentage

def format_price(price, coin_name):
    if coin_name == "px": 
        return round(price, 4) 
    elif coin_name == "ton": 
        return round(price, 2) 
    else:
        return int(price)  

while True:
    s = requests.get("https://coinmarketcap.com/", timeout=10)
    px = requests.get("https://coinmarketcap.com/currencies/not-pixel/", timeout=10)
    ton = requests.get("https://coinmarketcap.com/currencies/toncoin/", timeout=10)

    if s.status_code != 200 or px.status_code != 200 or ton.status_code != 200:
        print("Failed to retrieve data")
        time.sleep(60)
        continue

    data = s.text
    cd = px.text
    cd2 = ton.text

    match = re.search(r'"highlightsData":\{"trendingList":(\[.*?\])', data)

    if match:
        try:
            trending_list = json.loads(match.group(1))
            for coin in trending_list:
                name = coin.get("name", "Unknown Coin").replace(" ", "_").lower()  #
                price = coin.get("priceChange", {}).get("price", "N/A")
                globals()[name] = price  
        except json.JSONDecodeError:
            print("Error parsing trending list JSON")
    else:
        print("Highlights data not found.")

    match = re.search(r'"statistics":(\{.*?\})', cd2)
    name_match = re.search(r'"name":"(.*?)"', cd2)

    if match:
        try:
            statistics_json = match.group(1)
            statistics_dict = json.loads(statistics_json)
            price = statistics_dict.get("price", "N/A")
            coin_name = name_match.group(1).replace(" ", "_").lower() if name_match else "unknown_coin"  
            globals()[coin_name] = price
            x = price

        except json.JSONDecodeError:
            print("Error parsing statistics JSON")

    match = re.search(r'"statistics":(\{.*?\})', cd)
    name_match = re.search(r'"name":"(.*?)"', cd)

    if match:
        try:
            statistics_json = match.group(1)
            statistics_dict = json.loads(statistics_json)
            price = statistics_dict.get("price", "N/A")
            coin_name = name_match.group(1).replace(" ", "_").lower() if name_match else "unknown_coin"  
            globals()[coin_name] = price 

            if price != "N/A" and price != 0:
                try:
                    loss_percentage = ((previous_price - float(price)) / previous_price) * 100
                    print(f"{coin_name.capitalize()} - Loss Percentage: {loss_percentage:.2f}%")
                except ValueError:
                    print(f"Invalid price for {coin_name}")
            
        except json.JSONDecodeError:
            print("Error parsing statistics JSON")
    else:
        print("Statistics data not found.")

    try:
        initial_price = INITIAL_PX_PRICE
        current_price = coinmarketcap
        loss_percentage = calculate_loss_percentage(initial_price, current_price)

        formatted_bitcoin = format_price(float(bitcoin), "bitcoin")
        formatted_ethereum = format_price(float(ethereum), "ethereum")
        formatted_solana = format_price(float(solana), "solana")
        formatted_xrp = format_price(float(xrp), "xrp")
        formatted_cardano = format_price(float(cardano), "cardano")
        formatted_px = format_price(float(coinmarketcap), "px")
        formatted_ton = format_price(float(x), "ton")  

        message_text = f"""
$PX {formatted_px}$  |  -{loss_percentage:.2f}%

$TON {formatted_ton}$ 
"""

        sent = bot.send_message(chat_id=chat_id, text=str(message_text), parse_mode="Markdown")

    except NameError:
        print("One or more coin prices not found yet.")

    time.sleep(60)
