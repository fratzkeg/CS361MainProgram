# main.py Milestone1

import json
import os
from datetime import date

DATA_FILE = 'data.json'

def load_data():
    """Load accounts and expenses from disk, or initialize empty."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return {"accounts": [], "expenses": []}

def save_data(data):
    """Save accounts and expenses back to disk."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def pause():
    """Pause until the user presses Enter."""
    input("\nPress Enter to continue...")

def view_dashboard(data):
    """Story 3: Display account balances and recent expenses."""
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
    """Story 1: Add or delete financial accounts."""
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== Account Management (IH#5: Cancel/Back available) ===\n")
        print("1) Add Account")
        print("2) Delete Account")
        print("3) Back to Main Menu")
        choice = input("Select an option: ")
        if choice == '1':
            name = input("Account Name: ")
            acc_type = input("Account Type (e.g., Checking): ")
            balance = float(input("Initial Balance: $"))
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
                continue
            print("\nSelect account to delete:")
            for idx, acc in enumerate(data['accounts'], start=1):
                print(f"{idx}) {acc['name']} (${acc['balance']:.2f})")
            sel = int(input("Enter number: "))
            if 1 <= sel <= len(data['accounts']):
                removed = data['accounts'].pop(sel-1)
                save_data(data)
                print(f"\n✓ Removed account: {removed['name']}")
            else:
                print("\nInvalid selection.")
            pause()
        else:
            break

def record_expense(data):
    """Story 2: Record a new expense entry."""
    os.system('clear' if os.name == 'posix' else 'cls')
    print("=== Record Expense ===\n")
    exp_date = input(f"Date (YYYY-MM-DD) [default {date.today()}]: ") or str(date.today())
    amount = float(input("Amount: $"))
    category = input("Category: ")
    data['expenses'].append({
        "date": exp_date,
        "amount": amount,
        "category": category
    })
    save_data(data)
    print("\n✓ Expense recorded!")
    pause()

def main_menu():
    """Main program loop with explicit path (IH#6)."""
    data = load_data()
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=== Personal Finance Tracker ===\n")
        print("1) View Dashboard")
        print("2) Manage Accounts")
        print("3) Record Expense")
        print("4) Exit")
        choice = input("\nSelect: ")
        if choice == '1':
            view_dashboard(data)
        elif choice == '2':
            manage_accounts(data)
        elif choice == '3':
            record_expense(data)
        elif choice == '4':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice.")
            pause()

if __name__ == '__main__':
    main_menu()

