# utils.py  ──────────────────────────────────────────────────────────────────────
import os
import re
import json
import time
import pandas as pd
import matplotlib.pyplot as plt
from colorama import Fore, Style, init

# ────────────────────────────────────────────────────────────────────────────────
#  0.  Log–file repair helpers (run once at import)
# ────────────────────────────────────────────────────────────────────────────────
LOG_FILE      = "snipes_log.txt"
SALES_LOG     = "sales_log.txt"
AUCTIONS_LOG  = "auctions_log.txt"

_EXPECTED_HEADERS = {
    LOG_FILE:     ["Item Name", "Snipe Price", "Suggested BIN", "Second Lowest BIN", "Timestamp", "UUID"],
    SALES_LOG:    ["Timestamp", "Item Name", "Buy Price", "Sell Price", "Profit"],
    AUCTIONS_LOG: ["Timestamp", "Item Name", "Listed Price", "Sold"],
}

def _repair_csv(path: str, cols: list[str], pad: str | None = None) -> None:
    """
    • Ensures the file exists.
    • Makes the header exactly ','.join(cols).
    • Splits a header+first-row line that was accidentally glued together.
    • Optionally pads short data rows with `pad` until they reach len(cols).
    """
    header_line = ",".join(cols)
    # 1. Create the file if it doesn't exist
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(header_line + "\n")
        return

    with open(path, "r", encoding="utf-8") as f:
        raw_lines = f.read().splitlines()

    if not raw_lines:
        raw_lines = [header_line]

    first = raw_lines[0]
    # 2. Is the header glued to the first data row? Split at first timestamp.
    if first.startswith(header_line) and first != header_line:
        # Look for YYYY-MM-DD HH:MM:SS
        m = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", first)
        if m:
            data_part = first[len(header_line):].lstrip(",")
            raw_lines = [header_line, data_part, *raw_lines[1:]]
        else:
            # Unknown garble – just force-replace header
            raw_lines[0] = header_line
    # 3. Header missing or wrong → replace
    elif first != header_line:
        raw_lines[0] = header_line

    # 4. Pad short rows if requested
    if pad is not None:
        fixed = [raw_lines[0]]
        for ln in raw_lines[1:]:
            parts = ln.split(",")
            if len(parts) < len(cols):
                parts += [pad] * (len(cols) - len(parts))
            fixed.append(",".join(parts))
        raw_lines = fixed

    # 5. Re-write
    with open(path, "w", encoding="utf-8") as f:
        f.writelines([ln.rstrip("\r\n") + "\n" for ln in raw_lines])

# Run the repair for all three logs (pad 'No' for missing Sold flag)
_repair_csv(LOG_FILE,     _EXPECTED_HEADERS[LOG_FILE])
_repair_csv(SALES_LOG,    _EXPECTED_HEADERS[SALES_LOG])
_repair_csv(AUCTIONS_LOG, _EXPECTED_HEADERS[AUCTIONS_LOG], pad="No")


# ────────────────────────────────────────────────────────────────────────────────
#  1.  Normal imports that rely on clean CSVs
# ────────────────────────────────────────────────────────────────────────────────
from sell_tracker import record_sale            # after repair = safe to import
init(autoreset=True)


# ────────────────────────────────────────────────────────────────────────────────
#  2.  Configuration & small utilities
# ────────────────────────────────────────────────────────────────────────────────
CONFIG_PATH = "config.json"

def parse_human_input(text: str) -> int:
    text = text.lower().replace(",", "").replace("m", "e6").replace("k", "e3")
    total = 0
    for part in text.split():
        try:
            total += int(float(eval(part)))
        except Exception:
            continue
    return total

if not os.path.exists(CONFIG_PATH):
    config = {"budget": 1_000_000, "min_profit_percent": 20.0}
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)
else:
    with open(CONFIG_PATH, "r") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            config = {"budget": 1_000_000, "min_profit_percent": 20.0}
            with open(CONFIG_PATH, "w") as fw:
                json.dump(config, fw, indent=4)

def save_config() -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def format_price(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}m".rstrip("0").rstrip(".")
    if n >= 1_000:
        return f"{n/1_000:.1f}k".rstrip("0").rstrip(".")
    return str(n)


# ────────────────────────────────────────────────────────────────────────────────
#  3.  MAIN MENU
# ────────────────────────────────────────────────────────────────────────────────
def main_menu() -> None:
    from sell_tracker import record_auction     # local import avoids circulars
    import scanner                              # lazy-import for speed

    while True:
        clear()
        print(f"{Fore.CYAN}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("  Welcome to SkyblockSniper ✨")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("\n1. 📈 Trends")
        print("2. 💼 Portfolio")
        print("3. 🔍 Start Scanner")
        print("4. ⚙️ Scanner Config")
        print("5. 📃 Log an Auction")
        print("6. 💰 Mark as Sold")
        print("7. ❌ Exit\n")

        choice = input("Select an option: ").strip()

        if   choice == "1": show_trends()
        elif choice == "2": show_portfolio()
        elif choice == "3":
            clear()
            print(f"{Fore.GREEN}Starting scanner with budget {config['budget']:,} coins...")
            try:
                scanner.start_sniper()
            except Exception as e:
                print(f"{Fore.RED}Scanner failed: {e}")
            input("\nPress Enter to return to the main menu...")
        elif choice == "4": configure_scanner()
        elif choice == "5": log_auction_listing(record_auction)
        elif choice == "6": mark_auction_as_sold()
        elif choice == "7":
            print("Goodbye!")
            time.sleep(1)
            break
        else:
            print("Invalid input.")
            time.sleep(1)


# ────────────────────────────────────────────────────────────────────────────────
#  4.  INDIVIDUAL MENU ACTIONS
# ────────────────────────────────────────────────────────────────────────────────
def show_trends() -> None:
    clear()
    print(f"{Fore.MAGENTA}📈 Real Trends (Last 14 Days)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    df = pd.read_csv(LOG_FILE, parse_dates=["Timestamp"])
    recent = df[df["Timestamp"] > pd.Timestamp.now() - pd.Timedelta("14D")]

    if recent.empty:
        print(f"{Fore.YELLOW}No flip suggestions found yet.")
        input("\nPress Enter to return to menu...")
        return

    top = (recent
           .groupby("Item Name")
           .agg(Flips=("UUID", "count"),
                AvgProfit=("Suggested BIN",
                           lambda x: (x - recent.loc[x.index, "Snipe Price"]).mean()))
           .sort_values(by="Flips", ascending=False)
           .head(10))

    print(f"{Fore.CYAN}Top 10 Most Suggested Flips:")
    for item, row in top.iterrows():
        print(f"  {Fore.YELLOW}{item}{Style.RESET_ALL} — Flips: {row['Flips']} — "
              f"Avg. Profit: {Fore.GREEN}{format_price(int(row['AvgProfit']))}")

    try:
        top["AvgProfit"].plot(kind="bar", title="Avg. Profit by Item (Last 14 Days)")
        plt.tight_layout()
        plt.show()
    except Exception:
        print("(Plot failed to render.)")

    input("\nPress Enter to return to menu...")


def log_auction_listing(record_auction) -> None:
    clear()
    print(f"{Fore.YELLOW}📃 Log an Auction Listing")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    df = pd.read_csv(LOG_FILE)
    if df.empty:
        print("No flip suggestions available.")
        time.sleep(1)
        return

    recent = df.tail(15).reset_index(drop=True)
    print(f"{Fore.CYAN}Recent Suggested Flips:")
    for i, row in recent.iterrows():
        print(f"{i+1}. {row['Item Name']} — Bought for {format_price(row['Snipe Price'])}")

    idx = input("\nSelect item number to log auction (or press Enter to cancel): ").strip()
    if not idx.isdigit() or not (1 <= int(idx) <= len(recent)):
        print("Cancelled.")
        time.sleep(1)
        return

    sel = recent.iloc[int(idx)-1]
    print(f"\n💡 Suggested BIN: {format_price(int(sel['Suggested BIN']))} "
          f"(2nd lowest BIN: {format_price(int(sel['Second Lowest BIN']))})")
    listed = int(parse_human_input(input("What price are you listing it for? ").strip() or "0"))
    if listed <= 0:
        print("Invalid input.")
        time.sleep(1)
        return

    record_auction(sel["Item Name"], listed)
    input("\n[✔] Auction logged! Press Enter to return to menu...")


def show_portfolio() -> None:
    clear()
    print(f"{Fore.MAGENTA}💼 Your Flip Portfolio")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    auctions = pd.read_csv(AUCTIONS_LOG)
    snipes   = pd.read_csv(LOG_FILE)
    sales    = pd.read_csv(SALES_LOG)

    combined = (auctions
                .merge(snipes, how="left", on="Item Name")
                .merge(sales,   how="left", on="Item Name", suffixes=("", "_Sold")))

    if "Timestamp" in combined.columns:
        combined["Timestamp"] = pd.to_datetime(combined["Timestamp"], errors="coerce")
        combined = combined.sort_values(by="Timestamp", ascending=False)

    if combined.empty:
        print("No portfolio entries yet.")
        input("\nPress Enter to return to menu...")
        return

    for _, row in combined.iterrows():
        date_lbl = (row["Timestamp"].strftime('%Y-%m-%d %H:%M')
                    if pd.notnull(row["Timestamp"]) else "Unknown Date")
        print(f"{Fore.YELLOW}{date_lbl} — {row['Item Name']}")

        if pd.notnull(row.get("Snipe Price")):
            print(f"  Bought for: {format_price(int(row['Snipe Price']))}")
        elif pd.notnull(row.get("Listed Price")):
            print(f"  Bought for: {format_price(int(row['Listed Price']))}")
        else:
            print(f"  Bought for: Unknown")

        if pd.notnull(row.get("Suggested BIN")):
            print(f"  Suggested BIN: {format_price(int(row['Suggested BIN']))}")
            print(f"  2nd Lowest BIN: {format_price(int(row['Second Lowest BIN']))}")

        if pd.notnull(row.get("Listed Price")):
            print(f"  Listed Price: {format_price(int(row['Listed Price']))}")

        if row.get("Sold") == "Yes" and pd.notnull(row.get("Sell Price")):
            expected = (int(row["Suggested BIN"] - row["Snipe Price"])
                        if pd.notnull(row.get("Suggested BIN")) and pd.notnull(row.get("Snipe Price"))
                        else None)
            actual = int(row["Sell Price"] - (row.get("Snipe Price") or row.get("Listed Price")))
            print(f"  SOLD FOR: {Fore.GREEN}{format_price(int(row['Sell Price']))}{Style.RESET_ALL}")
            if expected is not None:
                print(f"  Expected Profit: {Fore.YELLOW}{format_price(expected)}")
            print(f"  Actual Profit:   {Fore.GREEN}{format_price(actual)}")
        else:
            print(f"{Fore.CYAN}  Not yet sold")

        print("----------------------------------")

    input("\nPress Enter to return to menu...")


def mark_auction_as_sold() -> None:
    from sell_tracker import record_sale     # late import to avoid circulars

    clear()
    print(f"{Fore.YELLOW}💰 Mark Auction as Sold")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    df = pd.read_csv(AUCTIONS_LOG)
    if "Sold" not in df.columns:
        # last-ditch defence
        df.rename(columns={c: "Sold" for c in df.columns if c.lower().startswith("sold")}, inplace=True)

    unsold = df[df["Sold"] != "Yes"].reset_index()
    if unsold.empty:
        print("No unsold auctions available.")
        input("\nPress Enter to return...")
        return

    print(f"{Fore.CYAN}Unsold Auctions:")
    for i, row in unsold.iterrows():
        print(f"{i+1}. {row['Item Name']} — Listed for {format_price(int(row['Listed Price']))}")

    idx = input("\nSelect auction number to mark as sold (or press Enter to cancel): ").strip()
    if not idx.isdigit() or not (1 <= int(idx) <= len(unsold)):
        print("Cancelled.")
        time.sleep(1)
        return

    sel = unsold.iloc[int(idx)-1]
    sold_price = int(parse_human_input(input("Final sold price: ").strip() or "0"))
    if sold_price <= 0:
        print("Invalid input.")
        time.sleep(1)
        return

    # Resolve real buy price
    snipes = pd.read_csv(LOG_FILE)
    match  = snipes[snipes["Item Name"] == sel["Item Name"]]
    buy_price = int(match.iloc[-1]["Snipe Price"]) if not match.empty else int(sel["Listed Price"])

    record_sale(sel["Item Name"], buy_price, sold_price)

    # Flag as sold
    df.at[sel["index"], "Sold"] = "Yes"
    df.to_csv(AUCTIONS_LOG, index=False)
    print(f"[✔] Marked {sel['Item Name']} as sold for {sold_price:,}")
    input("\nPress Enter to return...")


def configure_scanner() -> None:
    while True:
        clear()
        print(f"{Fore.MAGENTA}Scanner Configuration")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"1. Budget: {config['budget']:,} coins")
        print("2. Back to Main Menu")
        choice = input("\nSelect setting to change: ").strip()

        if choice == "1":
            raw = input("Enter new budget (e.g. 5.2m 400k): ").strip()
            new_budget = parse_human_input(raw)
            if new_budget > 0:
                config["budget"] = new_budget
                save_config()
            else:
                print("Invalid input.")
                time.sleep(1)
        elif choice == "2":
            break
        else:
            print("Invalid choice.")
            time.sleep(1)


# ────────────────────────────────────────────────────────────────────────────────
#  5.  Boot
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main_menu()