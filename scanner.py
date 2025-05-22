import asyncio
import re
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor
from timeit import default_timer
from utils import format_price
from colorama import Fore, Style, init
from logger import log_snipe

init(autoreset=True)

# Load config
with open("config.json") as f:
    config = json.load(f)
MIN_PROFIT_PERCENT = config.get("min_profit_percent", 20.0) / 100
LOWEST_PRICE = 5
MAX_PRICE = config.get("budget", 1000000)

REFORGES = [
    " ✦", "⚚ ", " ✪", "✪", "Stiff ", "Lucky ", "Jerry's ", "Dirty ", "Fabled ", "Suspicious ", "Gilded ",
    "Warped ", "Withered ", "Bulky ", "Stellar ", "Heated ", "Ambered ", "Fruitful ", "Magnetic ",
    "Fleet ", "Mithraic ", "Auspicious ", "Refined ", "Headstrong ", "Precise ", "Spiritual ", "Moil ",
    "Blessed ", "Toil ", "Bountiful ", "Candied ", "Submerged ", "Reinforced ", "Cubic ", "Undead ",
    "Ridiculous ", "Necrotic ", "Spiked ", "Jaded ", "Loving ", "Perfect ", "Renowned ", "Giant ",
    "Empowered ", "Ancient ", "Sweet ", "Silky ", "Bloody ", "Shaded ", "Gentle ", "Odd ", "Fast ",
    "Fair ", "Epic ", "Sharp ", "Heroic ", "Spicy ", "Legendary ", "Deadly ", "Fine ", "Grand ", "Hasty ",
    "Neat ", "Rapid ", "Unreal ", "Awkward ", "Rich ", "Clean ", "Fierce ", "Heavy ", "Light ", "Mythic ",
    "Pure ", "Smart ", "Titanic ", "Wise ", "Bizarre ", "Itchy ", "Ominous ", "Pleasant ", "Pretty ",
    "Shiny ", "Simple ", "Strange ", "Vivid ", "Godly ", "Demonic ", "Forceful ", "Hurtful ", "Keen ",
    "Strong ", "Superior ", "Unpleasant ", "Zealous "
]

results = []
prices = []
now = 0
toppage = 0

def safe_request(url, retries=3):
    for i in range(retries):
        try:
            return requests.get(url, timeout=10).json()
        except requests.exceptions.RequestException as e:
            if i == retries - 1:
                print(f"[ERROR] Failed after {retries} attempts: {e}")
                return {"lastUpdated": 0, "totalPages": 0}
            time.sleep(1)

c = safe_request("https://api.hypixel.net/skyblock/auctions?page=0")
now = c['lastUpdated']
toppage = c['totalPages']

def fetch(session, page):
    global toppage
    base_url = "https://api.hypixel.net/skyblock/auctions?page="
    try:
        with session.get(base_url + page, timeout=10) as response:
            data = response.json()
    except Exception as e:
        print(f"[ERROR] Fetch failed on page {page}: {e}")
        return {"auctions": [], "success": False}

    toppage = data.get('totalPages', toppage)
    if data.get('success'):
        for auction in data['auctions']:
            if not auction['claimed'] and auction['bin'] and "Furniture" not in auction.get("item_lore", ""):
                index = re.sub(r"\[[^\]]*\]", "", auction['item_name']) + auction['tier']
                for reforge in REFORGES:
                    index = index.replace(reforge, "")
                if index in prices:
                    if prices[index][0] > auction['starting_bid']:
                        prices[index][1] = prices[index][0]
                        prices[index][0] = auction['starting_bid']
                    elif prices[index][1] > auction['starting_bid']:
                        prices[index][1] = auction['starting_bid']
                else:
                    prices[index] = [auction['starting_bid'], float("inf")]

                if (LOWEST_PRICE < prices[index][0] < MAX_PRICE and
                    prices[index][1] > LOWEST_PRICE and
                    auction['start'] + 60000 > now):
                    results.append([auction['uuid'], auction['item_name'], auction['starting_bid'], index])
    return data

async def get_data_asynchronous():
    pages = [str(x) for x in range(toppage)]
    with ThreadPoolExecutor(max_workers=10) as executor:
        with requests.Session() as session:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, fetch, *(session, page))
                for page in pages if int(page) < toppage
            ]
            for response in await asyncio.gather(*tasks):
                pass

def start_sniper():
    global results, prices
    results = []
    prices = {}

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    future = asyncio.ensure_future(get_data_asynchronous())
    loop.run_until_complete(future)

    clean_results = []
    for entry in results:
        uuid, name, price, index = entry
        second_price = prices[index][1]
        if price >= second_price or second_price == float("inf"):
            continue

        # Profit logic
        suggested_price = min(int(second_price * 0.93), second_price - 1)
        profit = suggested_price - price

        if profit <= 0 or profit / price < MIN_PROFIT_PERCENT:
            continue

        clean_results.append([[uuid, name, price, index], second_price])

    if clean_results:
        print("\n========== SNIPES FOUND ==========\n")
        for i, result in enumerate(clean_results):
            uuid, name, price, index = result[0]
            second_price = result[1]

            # Suggest undercut price (up to 7% undercut or -1)
            suggested_price = min(int(second_price * 0.93), second_price - 1)
            profit = suggested_price - price

            print(f"{Fore.YELLOW}Auction {i+1}:{Style.RESET_ALL}")
            print(f"Auction UUID: {uuid}")
            print(f"Item Name: {name}")
            print(f"Item Price: {format_price(price)}")
            print(f"Second Lowest BIN: {format_price(second_price)}")
            print(f"{Fore.CYAN}/viewauction {uuid}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}💡 Recommended BIN Price: {format_price(suggested_price)}")
            print(f"📈 Profit if flipped: {format_price(profit)}{Style.RESET_ALL}")
            print("----------------------------------")

            # ✅ Log the snipe
            log_snipe(name, price, suggested_price, second_price, uuid)

        print("\nReturning to main menu...\n")
    else:
        print("No good flips found right now.")
        time.sleep(2)

def sniper_loop():
    while True:
        start_sniper()
        time.sleep(30)
