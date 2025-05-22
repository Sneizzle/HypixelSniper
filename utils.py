import os
import json
import time
import pandas as pd
import matplotlib.pyplot as plt
from colorama import Fore, Style, init
from sell_tracker import record_sale

init(autoreset=True)

CONFIG_PATH = "config.json"
LOG_FILE = "snipes_log.txt"
SALES_LOG = "sales_log.txt"
AUCTIONS_LOG = "auctions_log.txt"

def parse_human_input(text):
    text = text.lower().replace(",", "").replace("m", "e6").replace("k", "e3")
    parts = text.split()
    total = 0
    for part in parts:
        try:
            total += int(float(eval(part)))
        except:
            continue
    return total


if not os.path.exists(CONFIG_PATH):
    config = {"budget": 1000000}
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)
else:
    with open(CONFIG_PATH, "r") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            config = {"budget": 1000000}
            with open(CONFIG_PATH, "w") as fw:
                json.dump(config, fw, indent=4)

def save_config():
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def format_price(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}m".rstrip("0").rstrip(".")
    elif n >= 1_000:
        return f"{n/1_000:.1f}k".rstrip("0").rstrip(".")
    else:
        return str(n)

def main_menu():
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

        if choice == "1":
            show_trends()
        elif choice == "2":
            show_portfolio()
        elif choice == "3":
            start_scanner()
        elif choice == "4":
            configure_scanner()
        elif choice == "5":
            log_auction_listing()
        elif choice == "6":
            mark_auction_as_sold()
        elif choice == "7":
            print("Goodbye!")
            time.sleep(1)
            break


        else:
            print("Invalid input. Try again.")
            time.sleep(1)

def show_trends():
    clear()
    print(f"{Fore.MAGENTA}📈 Real Trends (Last 14 Days)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if not os.path.exists(LOG_FILE):
        print(f"{Fore.YELLOW}No flip suggestions found yet.")
        input("\nPress Enter to return to menu...")
        return

    try:
        df = pd.read_csv(LOG_FILE)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        recent = df[df["Timestamp"] > pd.Timestamp.now() - pd.Timedelta("14D")]

        top = recent.groupby("Item Name").agg(
            Flips=("UUID", "count"),
            AvgProfit=("Suggested BIN", lambda x: (x - recent.loc[x.index, "Snipe Price"]).mean())
        ).sort_values(by="Flips", ascending=False).head(10)

        print(f"{Fore.CYAN}Top 10 Most Suggested Flips:")
        for item, row in top.iterrows():
            print(f"  {Fore.YELLOW}{item}{Style.RESET_ALL} — Flips: {row['Flips']} — Avg. Profit: {Fore.GREEN}{format_price(int(row['AvgProfit']))}")

        try:
            top["AvgProfit"].plot(kind="bar", title="Avg. Profit by Item (Last 14 Days)")
            plt.tight_layout()
            plt.show()
        except:
            print("(Plot failed to render.)")

    except Exception as e:
        print(f"{Fore.RED}Error showing trends: {e}")

    input("\nPress Enter to return to menu...")

def log_auction_listing():
    clear()
    print(f"{Fore.YELLOW}📃 Log an Auction Listing")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if not os.path.exists(LOG_FILE):
        print("No flip suggestions available.")
        time.sleep(1)
        return

    try:
        df = pd.read_csv(LOG_FILE)
        recent = df.tail(15).reset_index(drop=True)

        print(f"{Fore.CYAN}Recent Suggested Flips:")
        for i, row in recent.iterrows():
            print(f"{i + 1}. {row['Item Name']} — Bought for {format_price(row['Snipe Price'])}")

        choice = input("\nSelect item number to log auction (or press Enter to cancel): ").strip()
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(recent):
            print("Cancelled.")
            time.sleep(1)
            return

        selected = recent.iloc[int(choice) - 1]

        print(f"\n💡 Suggested BIN: {format_price(int(selected['Suggested BIN']))} (2nd lowest BIN: {format_price(int(selected['Second Lowest BIN']))})")
        listed = int(parse_human_input(input("What price are you listing it for? ").strip()))

        from sell_tracker import record_auction
        record_auction(selected["Item Name"], listed)

        input("\n[✔] Auction logged! Press Enter to return to menu...")

    except Exception as e:
        print(f"{Fore.RED}Failed to log auction: {e}")
        input("\nPress Enter to return...")


def show_portfolio():
    clear()
    print(f"{Fore.MAGENTA}💼 Your Flip Portfolio")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if not os.path.exists(AUCTIONS_LOG):
        print("No auctions logged yet.")
        input("\nPress Enter to return to menu...")
        return

    try:
        auctions = pd.read_csv(AUCTIONS_LOG)
        snipes = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=["Item Name", "Snipe Price", "Suggested BIN", "Second Lowest BIN", "Timestamp"])
        sales = pd.read_csv(SALES_LOG) if os.path.exists(SALES_LOG) else pd.DataFrame(columns=["Item Name", "Buy Price", "Sell Price", "Profit", "Timestamp"])

        # Merge auctions with snipes and sales
        combined = auctions.merge(snipes, how="left", on="Item Name")
        combined = combined.merge(sales, how="left", on="Item Name", suffixes=("", "_Sold"))

        # Safely parse timestamps
        if "Timestamp" in combined.columns:
            combined["Timestamp"] = pd.to_datetime(combined["Timestamp"], errors="coerce")
        else:
            combined["Timestamp"] = pd.NaT

        combined = combined.sort_values(by="Timestamp", ascending=False)

        for _, row in combined.iterrows():
            if pd.notnull(row["Timestamp"]):
                label = row["Timestamp"].strftime('%A')
            else:
                label = "Unknown Date"

            print(f"{Fore.YELLOW}{label} — {row['Item Name']}")

            # Snipe / Buy price
            if pd.notnull(row.get("Snipe Price")):
                print(f"  Bought for: {format_price(int(row['Snipe Price']))}")
            else:
                print(f"  Bought for: Unknown")

            # BIN info
            if pd.notnull(row.get("Suggested BIN")):
                print(f"  Suggested BIN: {format_price(int(row['Suggested BIN']))}")
                print(f"  2nd Lowest BIN: {format_price(int(row['Second Lowest BIN']))}")

            # Listed price
            if pd.notnull(row.get("Listed Price")):
                print(f"  Listed Price: {format_price(int(row['Listed Price']))}")
            else:
                print(f"  Listed Price: Unknown")

            # Sold status
            if row.get("Sold") == "Yes" and pd.notnull(row.get("Sell Price")):
                expected_profit = (
                    int(row["Suggested BIN"] - row["Snipe Price"])
                    if pd.notnull(row.get("Suggested BIN")) and pd.notnull(row.get("Snipe Price"))
                    else None
                )
                actual_profit = (
                    int(row["Sell Price"] - row["Snipe Price"])
                    if pd.notnull(row.get("Snipe Price"))
                    else int(row["Sell Price"] - row["Listed Price"])
                    if pd.notnull(row.get("Listed Price"))
                    else None
                )

                print(f"  SOLD FOR: {Fore.GREEN}{format_price(int(row['Sell Price']))}{Style.RESET_ALL}")
                if expected_profit is not None:
                    print(f"  Expected Profit: {Fore.YELLOW}{format_price(expected_profit)}")
                if actual_profit is not None:
                    print(f"  Actual Profit: {Fore.GREEN}{format_price(actual_profit)}")
            else:
                print(f"{Fore.CYAN}  Not yet sold")

            print("----------------------------------")

    except Exception as e:
        print(f"{Fore.RED}Error reading portfolio: {e}")

    input("\nPress Enter to return to menu...")


def log_manual_sale():
    clear()
    print(f"{Fore.YELLOW}📤 Log a Sale")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if not os.path.exists(LOG_FILE):
        print("No flip suggestions available.")
        time.sleep(1)
        return

    try:
        df = pd.read_csv(LOG_FILE)
        recent = df.tail(15).reset_index(drop=True)

        print(f"{Fore.CYAN}Recent Suggested Flips:")
        for i, row in recent.iterrows():
            print(f"{i + 1}. {row['Item Name']} — Bought for {format_price(row['Snipe Price'])}")

        choice = input("\nSelect item number to mark as sold (or press Enter to cancel): ").strip()
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(recent):
            print("Cancelled.")
            time.sleep(1)
            return

        selected = recent.iloc[int(choice) - 1]
        sell = int(parse_human_input(input("Sold for: ").strip()))
        record_sale(selected["Item Name"], selected["Snipe Price"], sell)

        input("\nPress Enter to return to menu...")
    except Exception as e:
        print(f"{Fore.RED}Failed to log sale: {e}")
        input("\nPress Enter to return...")

def mark_auction_as_sold():
    clear()
    print(f"{Fore.YELLOW}💰 Mark Auction as Sold")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if not os.path.exists(AUCTIONS_LOG):
        print("No auctions logged yet.")
        time.sleep(1)
        return

    try:
        df = pd.read_csv(AUCTIONS_LOG)
        unsold = df[df["Sold"] != "Yes"].reset_index()

        if unsold.empty:
            print("No unsold auctions available.")
            input("\nPress Enter to return...")
            return

        print(f"{Fore.CYAN}Unsold Auctions:")
        for i, row in unsold.iterrows():
            print(f"{i + 1}. {row['Item Name']} — Listed for {format_price(row['Listed Price'])}")

        choice = input("\nSelect auction number to mark as sold (or press Enter to cancel): ").strip()
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(unsold):
            print("Cancelled.")
            time.sleep(1)
            return

        selected = unsold.iloc[int(choice) - 1]
        actual_price = int(parse_human_input(input("Final sold price: ").strip()))

        # Get snipe price (actual buy price) from snipes_log.txt
        try:
            snipes_df = pd.read_csv(LOG_FILE)
            matching = snipes_df[snipes_df["Item Name"] == selected["Item Name"]]
            if not matching.empty:
                buy_price = int(matching.iloc[-1]["Snipe Price"])
            else:
                buy_price = int(selected["Listed Price"])
        except:
            buy_price = int(selected["Listed Price"])

        # Record the sale with correct buy price
        from sell_tracker import record_sale
        record_sale(selected["Item Name"], buy_price, actual_price)

        # Mark the auction as sold
        df.at[selected["index"], "Sold"] = "Yes"
        df.to_csv(AUCTIONS_LOG, index=False)

        print(f"[✔] Marked {selected['Item Name']} as sold for {actual_price:,}")

        input("\nPress Enter to return...")

    except Exception as e:
        print(f"{Fore.RED}Error marking sale: {e}")
        input("\nPress Enter to return...")

def start_scanner():
    clear()
    print(f"{Fore.GREEN}Starting scanner with budget {config['budget']:,} coins...")
    try:
        import scanner
        scanner.start_sniper()
    except Exception as e:
        print(f"{Fore.RED}Scanner failed: {e}")
    input("\nPress Enter to return to the main menu...")

def configure_scanner():
    while True:
        clear()
        print(f"{Fore.MAGENTA}Scanner Configuration")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"1. Budget: {config['budget']:,} coins")
        print("2. Back to Main Menu")
        choice = input("\nSelect setting to change: ").strip()

        if choice == "1":
            raw = input("Enter new budget (e.g. 5.2m 400k): ").strip()
            parsed = parse_human_input(raw)
            if parsed > 0:
                config['budget'] = parsed
                save_config()
            else:
                print("Invalid input.")
                time.sleep(1)
        elif choice == "2":
            break
        else:
            print("Invalid choice.")
            time.sleep(1)

if __name__ == "__main__":
    main_menu()
