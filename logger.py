import os
from datetime import datetime

LOG_FILE = "snipes_log.txt"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        f.write("Item Name,Snipe Price,Suggested BIN,Second Lowest BIN,Timestamp,UUID\n")

def log_snipe(item_name, snipe_price, suggested_price, second_bin, uuid):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{item_name},{snipe_price},{suggested_price},{second_bin},{timestamp},{uuid}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"[LOGGED] {item_name} → {suggested_price} at {timestamp}")
