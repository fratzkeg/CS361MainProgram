# main.py

import json
import os
from datetime import date

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
    os.system('clear' if os.name == 'posix' else 'cls')
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
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== Account Management (IH#5: Cancel/Back available) ===\n")
        print("1) Add Account")
        print("2) Delete Account")
        print("3) Back to Main Menu")
        choice = input("Select an option: ").strip()
        if choice == '' or choice == '3':
            return
        if choice == '1':
            # Add Account
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
            # Delete Account
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
    os.system('clear' if os.name == 'posix' else 'cls')
    print("=== Record Expense ===\n")
    exp_date = input("Date (YYYY-MM-DD) (Enter to cancel): ").strip()
    if not exp_date:
        return
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

def main_menu():
    data = load_data()
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== Personal Finance Tracker ===\n")
        print("1) View Dashboard")
        print("2) Manage Accounts")
        print("3) Record Expense")
        print("4) Exit")
        choice = input("\nSelect: ").strip()
        if choice == '1':
            view_dashboard(data)
        elif choice == '2':
            manage_accounts(data)
        elif choice == '3':
            record_expense(data)
        elif choice == '' or choice == '4':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice.")
            pause()

if __name__ == '__main__':
    main_menu()
