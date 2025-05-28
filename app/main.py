#!/usr/bin/env python3
import json
import os
from datetime import date, timedelta
import requests
import uuid

# Developer/debug mode toggle
# Set DEBUG=1 (or "true"/"yes") in your environment to see request payloads.
DEBUG = os.getenv('DEBUG', '0').lower() in ('1', 'true', 'yes')

DATA_FILE = 'data.json'

def load_data():
    """Load data or initialize if file is missing or invalid."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            pass
    return {"accounts": [], "expenses": []}

def save_data(data):
    """Save accounts and expenses back to disk."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def pause():
    input("\nPress Enter to continue...")

def view_dashboard(data):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== Dashboard (IH#4: Persistent Nav) ===\n")
    print("Account Balances:")
    for acc in data['accounts']:
        print(f" - {acc['name']} ({acc['type']}): ${acc['balance']:.2f}")
    print("\nRecent Expenses:")
    for exp in data['expenses'][-5:]:
        print(f" - {exp['date']} | {exp['category']}: ${exp['amount']:.2f}")
    pause()

def manage_accounts(data):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=== Account Management (IH#5: Cancel/Back available) ===\n")
        print("1) Add Account")
        print("2) Delete Account")
        print("3) Back to Main Menu")
        choice = input("Select an option: ").strip()
        if choice == '' or choice == '3':
            return
        if choice == '1':
            name = input("Account Name (Enter to cancel): ").strip()
            if not name:
                return
            acc_type = input("Account Type (e.g., Checking) (Enter to cancel): ").strip()
            if not acc_type:
                return
            bal_str = input("Initial Balance ($) (Enter to cancel): ").strip()
            if not bal_str:
                return
            try:
                balance = float(bal_str)
            except ValueError:
                print("\nInvalid number. Returning to menu.")
                pause()
                return
            data['accounts'].append({
                "name": name,
                "type": acc_type,
                "balance": balance
            })
            save_data(data)
            print("\n✓ Account added!")
            pause()
        elif choice == '2':
            if not data['accounts']:
                print("\nNo accounts to delete.")
                pause()
                return
            print("\nSelect account to delete (Enter to cancel):")
            for idx, acc in enumerate(data['accounts'], start=1):
                print(f"{idx}) {acc['name']} (${acc['balance']:.2f})")
            sel = input("Enter number: ").strip()
            if not sel:
                return
            try:
                sel_i = int(sel)
                if 1 <= sel_i <= len(data['accounts']):
                    removed = data['accounts'].pop(sel_i - 1)
                    save_data(data)
                    print(f"\n✓ Removed account: {removed['name']}")
                else:
                    print("\nInvalid selection.")
            except ValueError:
                print("\nInvalid input.")
            pause()
        else:
            print("\nInvalid choice.")
            pause()

def record_expense(data):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== Record Expense ===\n")
    default_date = date.today().isoformat()
    exp_date = input(f"Date (YYYY-MM-DD) [default {default_date}]: ").strip()
    if not exp_date:
        exp_date = default_date

    amt_str = input("Amount ($) (Enter to cancel): ").strip()
    if not amt_str:
        return
    try:
        amount = float(amt_str)
    except ValueError:
        print("\nInvalid number. Returning to menu.")
        pause()
        return

    category = input("Category (Enter to cancel): ").strip()
    if not category:
        return

    data['expenses'].append({
        "date": exp_date,
        "amount": amount,
        "category": category
    })
    save_data(data)
    print("\n✓ Expense recorded!")
    pause()

def calculate_daily_limit(data):
    """Call the Flask /daily-limit microservice and display results."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== Daily Spending Limit Calculator ===\n")

    # Derive totalBudget from sum of account balances
    total_budget = sum(acc['balance'] for acc in data['accounts'])
    print(f"Derived totalBudget from accounts: ${total_budget:.2f}")

    # Prompt for reserve (default 0)
    reserve_str = input("Enter reserve amount ($) [default 0]: ").strip()
    try:
        reserve = float(reserve_str) if reserve_str else 0.0
    except ValueError:
        print("\nInvalid number. Using 0.")
        reserve = 0.0

    # Build expenses list for the service
    expenses_list = [
        {"date": exp["date"], "amount": exp["amount"]}
        for exp in data["expenses"]
    ]

    # Prompt for endDate (default = last day of this month)
    end_date_input = input("Enter end date (YYYY-MM-DD) [default end of this month]: ").strip()
    if end_date_input:
        end_date = end_date_input
    else:
        today = date.today()
        if today.month == 12:
            last_day = date(today.year, 12, 31)
        else:
            first_next = date(today.year, today.month + 1, 1)
            last_day = first_next - timedelta(days=1)
        end_date = last_day.isoformat()

    current_date = date.today().isoformat()

    # Assemble payload
    payload = {
        "totalBudget": total_budget,
        "reserve": reserve,
        "expenses": expenses_list,
        "endDate": end_date,
        "currentDate": current_date
    }

    # Generate and send correlation header
    corr_id = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": corr_id
    }

    if DEBUG:
        print("\n--- DEBUG: Request payload ---")
        print(json.dumps(payload, indent=2))
        print(f"--- DEBUG: X-Correlation-ID = {corr_id} ---\n")

    try:
        resp = requests.post(
            "http://localhost:5000/daily-limit",
            json=payload,
            headers=headers
        )
        resp.raise_for_status()
        result = resp.json()

        print("\n=== Results from Microservice ===")
        print(f"Correlation ID:       {result.get('correlationId')}")
        print(f"Daily Spending Limit: ${result['dailyLimit']:.2f}")
        print(f"Remaining Budget:     ${result['remainingBudget']:.2f}")
        print(f"Remaining Days:       {result['remainingDays']}")
        print(f"Status:               {result['status']}")
        print(f"Message:              {result['message']}")

    except requests.exceptions.RequestException as e:
        print(f"\nError calling microservice: {e}")
    except KeyError:
        print("\nUnexpected response format:", resp.text)

    pause()

def main_menu():
    data = load_data()
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=== Personal Finance Tracker ===\n")
        print("1) View Dashboard")
        print("2) Manage Accounts")
        print("3) Record Expense")
        print("4) Calculate Daily Spending Limit")
        print("5) Exit")
        choice = input("\nSelect: ").strip()

        if choice == '1':
            view_dashboard(data)
        elif choice == '2':
            manage_accounts(data)
        elif choice == '3':
            record_expense(data)
        elif choice == '4':
            calculate_daily_limit(data)
        elif choice == '' or choice == '5':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice.")
            pause()

if __name__ == '__main__':
    main_menu()
