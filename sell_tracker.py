import os
import csv
from datetime import datetime

SALES_LOG = "sales_log.txt"
AUCTIONS_LOG = "auctions_log.txt"

if not os.path.exists(AUCTIONS_LOG):
    with open(AUCTIONS_LOG, "w", newline="", encoding="utf-8") as f:
        f.write("Timestamp,Item Name,Listed Price\n")

def record_auction(item_name, listed_price):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(AUCTIONS_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, item_name, listed_price, "No"])
    print(f"\n[✔] Logged Auction: {item_name} → Listed for {listed_price:,} at {timestamp}")



# Ensure log file has headers
if not os.path.exists(SALES_LOG):
    with open(SALES_LOG, "w", newline="", encoding="utf-8") as f:
        f.write("Timestamp,Item Name,Buy Price,Sell Price,Profit\n")

def record_sale(item_name, buy_price, sell_price):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    profit = sell_price - buy_price
    with open(SALES_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, item_name, buy_price, sell_price, profit])
    print(f"\n[✔] Logged: {item_name} → Sold for {sell_price:,} (Profit: {profit:,})")
