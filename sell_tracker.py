import os
import csv
from datetime import datetime

SALES_LOG    = "sales_log.txt"
AUCTIONS_LOG = "auctions_log.txt"


# ────────────────────────────────────────────────────────────────────────────────
#  PATCH: Make sure auctions_log.txt always has the correct header & schema
# ────────────────────────────────────────────────────────────────────────────────
def _ensure_auctions_log_schema() -> None:
    """
    Guarantee that auctions_log.txt has the header:
        Timestamp,Item Name,Listed Price,Sold
    If the header is missing the 'Sold' column, patch it in and make sure every
    existing data row also has a value in that column (default 'No').
    """
    # File does not exist yet → it will be created with the right header later
    if not os.path.exists(AUCTIONS_LOG):
        return

    with open(AUCTIONS_LOG, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Empty file → just write correct header
    if not lines:
        lines = ["Timestamp,Item Name,Listed Price,Sold\n"]

    header_parts = lines[0].rstrip("\n").split(",")
    if header_parts[-1].lower() != "sold":
        # Patch header
        header_parts.append("Sold")
        lines[0] = ",".join(header_parts) + "\n"

        # Patch every existing data row (give it a default 'No' flag)
        for i in range(1, len(lines)):
            cols = lines[i].rstrip("\n").split(",")
            if len(cols) == 3:            # old row (no Sold flag yet)
                cols.append("No")
                lines[i] = ",".join(cols) + "\n"

        # Write fixed file
        with open(AUCTIONS_LOG, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("[INFO] Patched auctions_log.txt – added missing 'Sold' column.")


# Ensure schema before anything else touches the file
_ensure_auctions_log_schema()


# ────────────────────────────────────────────────────────────────────────────────
#  Create log files with correct headers if they don't exist
# ────────────────────────────────────────────────────────────────────────────────
if not os.path.exists(AUCTIONS_LOG):
    with open(AUCTIONS_LOG, "w", newline="", encoding="utf-8") as f:
        f.write("Timestamp,Item Name,Listed Price,Sold\n")

if not os.path.exists(SALES_LOG):
    with open(SALES_LOG, "w", newline="", encoding="utf-8") as f:
        f.write("Timestamp,Item Name,Buy Price,Sell Price,Profit\n")


# ────────────────────────────────────────────────────────────────────────────────
#  Public helper functions
# ────────────────────────────────────────────────────────────────────────────────
def record_auction(item_name: str, listed_price: int) -> None:
    """
    Log a newly listed auction.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(AUCTIONS_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, item_name, listed_price, "No"])


def record_sale(item_name: str, buy_price: int, sell_price: int) -> None:
    """
    Log a completed sale and profit.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    profit = sell_price - buy_price
    with open(SALES_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, item_name, buy_price, sell_price, profit])
    print(f"\n[✔] Logged: {item_name} → Sold for {sell_price:,} (Profit: {profit:,})")
