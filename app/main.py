#!/usr/bin/env python3
import json
import os
from datetime import date, timedelta
import requests
import uuid

# Developer/debug mode toggle (print JSON payloads when DEBUG=1)
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
    print("=== Dashboard ===\n")
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
        print("=== Account Management ===\n")
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

# --------------------------------------------
# Call Microservice A: /daily-limit (port 5000)
# --------------------------------------------
def calculate_daily_limit(data):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== Daily Spending Limit ===\n")

    total_budget = sum(acc['balance'] for acc in data['accounts'])
    print(f"Derived totalBudget from accounts: ${total_budget:.2f}")

    reserve_str = input("Enter reserve amount ($) [default 0]: ").strip()
    try:
        reserve = float(reserve_str) if reserve_str else 0.0
    except ValueError:
        print("\nInvalid number. Using 0.")
        reserve = 0.0

    expenses_list = [
        {"date": exp["date"], "amount": exp["amount"]}
        for exp in data["expenses"]
    ]

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

    payload = {
        "totalBudget": total_budget,
        "reserve": reserve,
        "expenses": expenses_list,
        "endDate": end_date,
        "currentDate": current_date
    }

    corr_id = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": corr_id
    }

    if DEBUG:
        print("\n--- DEBUG: /daily-limit payload ---")
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

        print("\n=== Results from /daily-limit ===")
        print(f"Correlation ID:       {result.get('correlationId')}")
        print(f"Daily Spending Limit: ${result['dailyLimit']:.2f}")
        print(f"Remaining Budget:     ${result['remainingBudget']:.2f}")
        print(f"Remaining Days:       {result['remainingDays']}")
        print(f"Status:               {result['status']}")
        print(f"Message:              {result['message']}")

    except requests.exceptions.RequestException as e:
        print(f"\nError calling /daily-limit: {e}")
    except (KeyError, ValueError):
        print("\nUnexpected response format:", resp.text)

    pause()

# --------------------------------------------
# Call Microservice B: /aggregate-expenses (port 5001)
# --------------------------------------------
def aggregate_expenses_service(data):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== Expense Aggregation ===\n")

    payload = {
        "expenses": [
            {"date": exp["date"], "amount": exp["amount"], "category": exp["category"]}
            for exp in data["expenses"]
        ]
    }
    corr_id = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": corr_id
    }

    if DEBUG:
        print("\n--- DEBUG: /aggregate-expenses payload ---")
        print(json.dumps(payload, indent=2))
        print(f"--- DEBUG: X-Correlation-ID = {corr_id} ---\n")

    try:
        resp = requests.post(
            "http://localhost:5001/aggregate-expenses",
            json=payload,
            headers=headers
        )
        resp.raise_for_status()
        result = resp.json()

        print("\n=== Results from /aggregate-expenses ===")
        for cat, total in result.items():
            if cat == "correlationId":
                print(f"Correlation ID: {total}")
            else:
                print(f" - {cat}: ${total:.2f}")

    except requests.exceptions.RequestException as e:
        print(f"\nError calling /aggregate-expenses: {e}")
    except Exception:
        print("\nUnexpected response format:", resp.text)

    pause()

# --------------------------------------------
# Call Microservice C: /project-balance (port 5002)
# --------------------------------------------
def project_balance_service(data):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== Future Balance Projection ===\n")

    use_accounts = input("Derive current balance from accounts? (Y/n): ").strip().lower()
    if use_accounts in ('', 'y', 'yes'):
        current_balance = sum(acc['balance'] for acc in data['accounts'])
    else:
        bal_str = input("Enter current balance ($): ").strip()
        try:
            current_balance = float(bal_str)
        except ValueError:
            print("\nInvalid number. Using 0.")
            current_balance = 0.0

    daily_limit_str = input("Enter daily spending limit ($): ").strip()
    try:
        daily_limit = float(daily_limit_str)
    except ValueError:
        print("\nInvalid number. Using 0.")
        daily_limit = 0.0

    end_date_input = input("Enter projection end date (YYYY-MM-DD): ").strip()
    if not end_date_input:
        print("\nEnd date is required. Aborting.")
        pause()
        return
    projection_end = end_date_input

    payload = {
        "currentBalance": current_balance,
        "dailyLimit": daily_limit,
        "projectionEndDate": projection_end
    }
    corr_id = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": corr_id
    }

    if DEBUG:
        print("\n--- DEBUG: /project-balance payload ---")
        print(json.dumps(payload, indent=2))
        print(f"--- DEBUG: X-Correlation-ID = {corr_id} ---\n")

    try:
        resp = requests.post(
            "http://localhost:5002/project-balance",
            json=payload,
            headers=headers
        )
        resp.raise_for_status()
        result = resp.json()

        print("\n=== Results from /project-balance ===")
        print(f"Correlation ID: {result.get('correlationId')}")
        for entry in result.get("projection", []):
            print(f" - {entry['date']}: ${entry['projectedBalance']:.2f}")

    except requests.exceptions.RequestException as e:
        print(f"\nError calling /project-balance: {e}")
    except Exception:
        print("\nUnexpected response format:", resp.text)

    pause()

# --------------------------------------------
# Call Microservice D: /alerts (port 5003)
# --------------------------------------------
def budget_alerts_service(data):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== Budget Alerts ===\n")

    total_budget = sum(acc['balance'] for acc in data['accounts'])
    expenses_sum = sum(exp['amount'] for exp in data['expenses'])
    reserve_str = input("Enter reserve amount for alert check ($) [default 0]: ").strip()
    try:
        reserve_balance = float(reserve_str) if reserve_str else 0.0
    except ValueError:
        print("\nInvalid number. Using 0.")
        reserve_balance = 0.0

    remaining_budget = total_budget - reserve_balance - expenses_sum
    print(f"Derived remainingBudget: ${remaining_budget:.2f}")

    warn_thresh_str = input("Enter warning threshold for budget ($): ").strip()
    try:
        warn_thresh = float(warn_thresh_str)
    except ValueError:
        print("\nInvalid number. Using 0.")
        warn_thresh = 0.0

    res_thresh_str = input("Enter reserve threshold ($): ").strip()
    try:
        res_thresh = float(res_thresh_str)
    except ValueError:
        print("\nInvalid number. Using 0.")
        res_thresh = 0.0

    payload = {
        "remainingBudget": remaining_budget,
        "warningThreshold": warn_thresh,
        "reserveBalance": reserve_balance,
        "reserveThreshold": res_thresh
    }
    corr_id = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": corr_id
    }

    if DEBUG:
        print("\n--- DEBUG: /alerts payload ---")
        print(json.dumps(payload, indent=2))
        print(f"--- DEBUG: X-Correlation-ID = {corr_id} ---\n")

    try:
        resp = requests.post(
            "http://localhost:5003/alerts",
            json=payload,
            headers=headers
        )
        resp.raise_for_status()
        result = resp.json()

        print("\n=== Results from /alerts ===")
        print(f"Correlation ID: {result.get('correlationId')}")
        alerts = result.get("alerts", [])
        if not alerts:
            print("No alerts at this time.")
        else:
            for a in alerts:
                print(f" - {a['alert']}: {a['message']}")

    except requests.exceptions.RequestException as e:
        print(f"\nError calling /alerts: {e}")
    except Exception:
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
        print("5) Aggregate Expenses")
        print("6) Project Future Balances")
        print("7) Budget Alerts")
        print("8) Exit")
        choice = input("\nSelect: ").strip()

        if choice == '1':
            view_dashboard(data)
        elif choice == '2':
            manage_accounts(data)
        elif choice == '3':
            record_expense(data)
        elif choice == '4':
            calculate_daily_limit(data)
        elif choice == '5':
            aggregate_expenses_service(data)
        elif choice == '6':
            project_balance_service(data)
        elif choice == '7':
            budget_alerts_service(data)
        elif choice == '' or choice == '8':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice.")
            pause()

if __name__ == '__main__':
    main_menu()
