"""
Banking API Simulation Service

A Flask-based mock banking API service that simulates banking data for testing
and integration with the Alchemist banking customer support agent.
"""
import os
import json
import uuid
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set API key from environment (or use a default for development)
API_KEY = os.getenv("BANKING_API_KEY", "test-api-key-1234567890")

# Helper function to generate realistic banking data

def generate_account_number(account_type):
    """Generate a realistic account number based on account type."""
    prefix_map = {
        "checking": "CHK",
        "savings": "SAV",
        "money_market": "MMK",
        "cd": "CDA",
        "ira": "IRA",
        "credit_card": "CRD",
        "mortgage": "MTG",
        "auto_loan": "ALN",
        "personal_loan": "PLN",
        "student_loan": "SLN",
        "line_of_credit": "LOC"
    }
    
    prefix = prefix_map.get(account_type, "ACC")
    digits = ''.join(random.choices(string.digits, k=10))
    return f"{prefix}-{digits[:4]}-{digits[4:10]}"

def generate_routing_number():
    """Generate a realistic bank routing number."""
    # First digit is Federal Reserve Bank number (1-12)
    frb = random.randint(1, 12)
    # Next 3 digits represent the ABA institution identifier
    aba = random.randint(100, 999)
    # Next 4 digits represent the branch identifier
    branch = random.randint(1000, 9999)
    # Last digit is the checksum
    base = f"{frb:01d}{aba:03d}{branch:04d}"
    
    # Calculate checksum using ABA algorithm
    weights = [3, 7, 1, 3, 7, 1, 3, 7]
    checksum = sum(int(base[i]) * weights[i] for i in range(8))
    checksum_digit = (10 - (checksum % 10)) % 10
    
    return f"{base}{checksum_digit}"

def generate_card_number(card_type="visa"):
    """Generate a realistic credit card number based on card type."""
    prefixes = {
        "visa": ["4"],
        "mastercard": ["51", "52", "53", "54", "55"],
        "amex": ["34", "37"],
        "discover": ["6011", "644", "645", "646", "647", "648", "649", "65"]
    }
    
    lengths = {
        "visa": 16,
        "mastercard": 16,
        "amex": 15,
        "discover": 16
    }
    
    prefix = random.choice(prefixes.get(card_type.lower(), prefixes["visa"]))
    length = lengths.get(card_type.lower(), 16)
    
    # Generate random digits for the rest of the card
    remaining_length = length - len(prefix)
    digits = ''.join(random.choices(string.digits, k=remaining_length))
    
    card_number = prefix + digits
    
    # Format the card number for readability
    if card_type.lower() == "amex":
        formatted = f"{card_number[:4]} {card_number[4:10]} {card_number[10:]}"
    else:
        formatted = f"{card_number[:4]} {card_number[4:8]} {card_number[8:12]} {card_number[12:]}"
    
    return {
        "number": card_number,  # Full number (normally would be masked)
        "masked": f"{'*' * (len(card_number) - 4)}{card_number[-4:]}",  # Last 4 digits only
        "formatted": formatted,  # Formatted with spaces
        "expiry": f"{random.randint(1, 12):02d}/{(datetime.now().year + random.randint(1, 5)) % 100:02d}",  # MM/YY
        "cvv": f"{random.randint(100, 999):03d}"  # 3-digit CVV
    }

def generate_address():
    """Generate a realistic US address."""
    street_names = ["Main", "Oak", "Pine", "Maple", "Cedar", "Elm", "Washington", "Park", "Lake", "Hill"]
    street_types = ["St", "Ave", "Blvd", "Dr", "Ln", "Rd", "Way", "Pl", "Ct"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", 
             "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Seattle", "Denver"]
    states = {
        "CA": ["90001", "90210", "94105", "95014"], 
        "NY": ["10001", "10016", "10036", "11201"],
        "TX": ["75001", "77001", "78701", "79901"],
        "IL": ["60007", "60601", "60614", "61701"],
        "FL": ["32801", "33101", "33401", "34102"]
    }
    
    street_num = random.randint(1, 9999)
    street_name = random.choice(street_names)
    street_type = random.choice(street_types)
    state = random.choice(list(states.keys()))
    zipcode = random.choice(states[state])
    city = random.choice(cities)
    
    return {
        "street": f"{street_num} {street_name} {street_type}",
        "city": city,
        "state": state,
        "zipcode": zipcode,
        "formatted": f"{street_num} {street_name} {street_type}, {city}, {state} {zipcode}"
    }

def generate_transaction_id():
    """Generate a unique transaction ID."""
    return f"TXN-{uuid.uuid4().hex[:16].upper()}"

def generate_transactions(account_type, current_balance, num_transactions=10, max_days=90):
    """Generate a realistic transaction history for an account."""
    balance_after = current_balance
    transactions = []
    
    # More detailed transaction descriptions by account type
    descriptions = {
        "checking": [
            {"name": "GROCERY OUTLET", "category": "Groceries"}, 
            {"name": "WHOLE FOODS", "category": "Groceries"},
            {"name": "TRADER JOE'S", "category": "Groceries"},
            {"name": "DIRECT DEPOSIT - PAYROLL", "category": "Income"},
            {"name": "UBER EATS", "category": "Dining"},
            {"name": "DOORDASH", "category": "Dining"},
            {"name": "OLIVE GARDEN", "category": "Dining"},
            {"name": "CHEESECAKE FACTORY", "category": "Dining"},
            {"name": "NETFLIX SUBSCRIPTION", "category": "Entertainment"},
            {"name": "SPOTIFY PREMIUM", "category": "Entertainment"},
            {"name": "AMAZON PRIME", "category": "Shopping"},
            {"name": "AMAZON.COM", "category": "Shopping"},
            {"name": "TARGET", "category": "Shopping"},
            {"name": "WALMART", "category": "Shopping"},
            {"name": "SHELL OIL", "category": "Auto & Transport"},
            {"name": "CHEVRON", "category": "Auto & Transport"},
            {"name": "UBER", "category": "Auto & Transport"},
            {"name": "LYFT", "category": "Auto & Transport"},
            {"name": "AT&T WIRELESS", "category": "Bills & Utilities"},
            {"name": "VERIZON WIRELESS", "category": "Bills & Utilities"},
            {"name": "PG&E", "category": "Bills & Utilities"},
            {"name": "WATER BILL", "category": "Bills & Utilities"},
            {"name": "RENT PAYMENT", "category": "Home"}, 
            {"name": "HOA DUES", "category": "Home"},
            {"name": "TRANSFER TO SAVINGS", "category": "Transfer"},
            {"name": "ATM WITHDRAWAL", "category": "Cash & ATM"},
            {"name": "CVS PHARMACY", "category": "Health"}, 
            {"name": "WALGREENS", "category": "Health"}, 
            {"name": "LA FITNESS", "category": "Health & Fitness"}, 
            {"name": "PLANET FITNESS", "category": "Health & Fitness"}
        ],
        "savings": [
            {"name": "INTEREST PAYMENT", "category": "Income"},
            {"name": "TRANSFER FROM CHECKING", "category": "Transfer"},
            {"name": "AUTOMATIC SAVINGS PLAN", "category": "Transfer"},
            {"name": "DIRECT DEPOSIT", "category": "Income"},
            {"name": "ATM WITHDRAWAL", "category": "Cash & ATM"},
            {"name": "TRANSFER TO CHECKING", "category": "Transfer"},
            {"name": "ANNUAL BONUS", "category": "Income"}
        ],
        "credit_card": [
            {"name": "BEST BUY", "category": "Shopping"},
            {"name": "APPLE STORE", "category": "Shopping"},
            {"name": "AMAZON.COM", "category": "Shopping"},
            {"name": "COSTCO WHOLESALE", "category": "Shopping"},
            {"name": "SOUTHWEST AIRLINES", "category": "Travel"},
            {"name": "DELTA AIRLINES", "category": "Travel"},
            {"name": "HILTON HOTELS", "category": "Travel"},
            {"name": "MARRIOTT", "category": "Travel"},
            {"name": "PAYMENT THANK YOU", "category": "Payment"},
            {"name": "STARBUCKS", "category": "Dining"},
            {"name": "PEET'S COFFEE", "category": "Dining"},
            {"name": "MCDONALD'S", "category": "Dining"},
            {"name": "THE HOME DEPOT", "category": "Home Improvement"},
            {"name": "LOWE'S", "category": "Home Improvement"},
            {"name": "IKEA", "category": "Home"},
            {"name": "UBER", "category": "Auto & Transport"},
            {"name": "LYFT", "category": "Auto & Transport"},
            {"name": "SPOTIFY PREMIUM", "category": "Entertainment"},
            {"name": "NETFLIX", "category": "Entertainment"},
            {"name": "HULU", "category": "Entertainment"}
        ],
        "mortgage": [
            {"name": "MORTGAGE PAYMENT", "category": "Payment"},
            {"name": "EXTRA PRINCIPAL PAYMENT", "category": "Payment"},
            {"name": "ESCROW DISBURSEMENT - INSURANCE", "category": "Insurance"},
            {"name": "ESCROW DISBURSEMENT - PROPERTY TAX", "category": "Taxes"},
            {"name": "LATE FEE", "category": "Fee"}
        ],
        "auto_loan": [
            {"name": "AUTO LOAN PAYMENT", "category": "Payment"},
            {"name": "EXTRA PRINCIPAL PAYMENT", "category": "Payment"},
            {"name": "LATE FEE", "category": "Fee"}
        ]
    }
    
    # Use default checking descriptions if account type not found
    account_descriptions = descriptions.get(account_type, descriptions["checking"])
    
    # Generate transactions
    for i in range(num_transactions):
        # Determine if credit or debit
        if account_type == "credit_card":
            is_debit = (i % 5 != 0)  # More debits than credits for credit account
        elif account_type in ["savings", "money_market", "cd", "ira"]:
            is_debit = (i % 4 == 0)  # More credits than debits for savings/investment
        elif account_type in ["mortgage", "auto_loan", "personal_loan", "student_loan"]:
            is_debit = False  # Only payments (credits) for loans
        else:
            is_debit = (i % 2 == 0)  # Even mix for checking
            
        # Calculate amount
        if is_debit:
            # Realistic transaction amounts vary by account type
            if account_type == "credit_card":
                amount = round(random.uniform(5, 750) * -1, 2)
            else:
                amount = round(random.uniform(10, 500) * -1, 2)
        else:
            if account_type in ["mortgage", "auto_loan", "personal_loan", "student_loan"]:
                # For loans, payment amounts are more consistent
                base_amount = current_balance * 0.02 if current_balance > 0 else 500
                variation = random.uniform(0.9, 1.1)
                amount = round(base_amount * variation, 2)
            else:
                amount = round(random.uniform(50, 2000), 2)
            
        # Adjust for credit account payment
        if account_type == "credit_card" and not is_debit:
            txn_info = {"name": "PAYMENT THANK YOU", "category": "Payment"}
        else:
            txn_info = random.choice(account_descriptions)
        
        # Calculate balance after
        prev_balance = balance_after
        balance_after = round(prev_balance + amount, 2)
        
        # Generate date
        days_ago = random.randint(1, max_days)
        txn_date = datetime.now() - timedelta(days=days_ago)
        date_str = txn_date.strftime("%Y-%m-%d")
        
        # Create transaction
        transactions.append({
            "transaction_id": generate_transaction_id(),
            "date": date_str,
            "description": txn_info["name"],
            "category": txn_info["category"],
            "amount": amount,
            "balance_after": balance_after,
            "status": "completed",
            "timestamp": txn_date.isoformat()
        })
    
    # Sort transactions by date (newest first)
    transactions.sort(key=lambda x: x["date"], reverse=True)
    
    # Fix the balance after for each transaction to make it consistent
    running_balance = current_balance
    for i, txn in enumerate(transactions):
        if i == 0:
            txn["balance_after"] = current_balance
        else:
            running_balance = round(running_balance - txn["amount"], 2)
            txn["balance_after"] = running_balance
    
    return transactions

# Generate a single account with realistic details
def generate_account(account_type, balance=None):
    """Generate a single account with realistic details"""
    if balance is None:
        if account_type == "checking":
            balance = round(random.uniform(500, 10000), 2)
        elif account_type == "savings":
            balance = round(random.uniform(1000, 50000), 2)
        elif account_type == "money_market":
            balance = round(random.uniform(5000, 100000), 2)
        elif account_type == "cd":
            balance = round(random.uniform(10000, 50000), 2)
        elif account_type == "ira":
            balance = round(random.uniform(20000, 150000), 2)
        elif account_type in ["credit_card", "line_of_credit"]:
            balance = round(random.uniform(0, 3000), 2)  # Outstanding balance
        elif account_type == "mortgage":
            balance = round(random.uniform(100000, 500000), 2)  # Remaining balance
        elif account_type == "auto_loan":
            balance = round(random.uniform(5000, 35000), 2)  # Remaining balance
        elif account_type == "personal_loan":
            balance = round(random.uniform(3000, 20000), 2)  # Remaining balance
        elif account_type == "student_loan":
            balance = round(random.uniform(10000, 70000), 2)  # Remaining balance
        else:
            balance = round(random.uniform(1000, 5000), 2)
    
    account = {
        "account_id": str(uuid.uuid4()),
        "account_number": generate_account_number(account_type),
        "account_type": account_type,
        "balance": balance,
        "currency": "USD",
        "status": "active",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "opened_date": (datetime.now() - timedelta(days=random.randint(30, 3650))).strftime("%Y-%m-%d")
    }
    
    # Add account-type specific details
    if account_type == "checking":
        account["is_interest_bearing"] = random.choice([True, False])
        if account["is_interest_bearing"]:
            account["interest_rate"] = round(random.uniform(0.01, 0.05), 3)
        account["monthly_fee"] = random.choice([0.00, 5.00, 10.00, 15.00])
        account["minimum_balance"] = random.choice([0.00, 500.00, 1500.00])
        account["routing_number"] = generate_routing_number()
        
    elif account_type == "savings":
        account["interest_rate"] = round(random.uniform(0.05, 0.5), 3)
        account["withdrawal_limit"] = random.choice([3, 6, 9])
        account["monthly_fee"] = random.choice([0.00, 3.00, 5.00])
        
    elif account_type == "money_market":
        account["interest_rate"] = round(random.uniform(0.5, 1.5), 3)
        account["minimum_balance"] = random.choice([1000.00, 2500.00, 5000.00])
        account["monthly_fee"] = random.choice([0.00, 10.00, 15.00])
        
    elif account_type == "cd":
        account["interest_rate"] = round(random.uniform(1.0, 3.0), 3)
        account["term_months"] = random.choice([3, 6, 12, 24, 36, 60])
        account["maturity_date"] = (datetime.now() + timedelta(days=30*account["term_months"])).strftime("%Y-%m-%d")
        account["early_withdrawal_penalty"] = f"{random.choice([30, 60, 90, 180])} days of interest"
        
    elif account_type == "ira":
        account["ira_type"] = random.choice(["Traditional", "Roth", "SEP", "SIMPLE"])
        account["year_to_date_contribution"] = round(random.uniform(0, 6000), 2)
        account["ytd_earnings"] = round(random.uniform(-2000, 5000), 2)
        
    elif account_type == "credit_card":
        account["credit_limit"] = round(random.uniform(1000, 25000), 2)
        account["available_credit"] = round(account["credit_limit"] - account["balance"], 2)
        account["interest_rate"] = round(random.uniform(12.99, 24.99), 2)
        account["minimum_payment"] = max(35.00, round(account["balance"] * 0.02, 2))
        account["payment_due_date"] = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        account["card"] = generate_card_number(random.choice(["visa", "mastercard", "amex", "discover"]))
        
    elif account_type == "mortgage":
        account["original_loan_amount"] = round(account["balance"] * random.uniform(1.05, 1.5), 2)
        account["interest_rate"] = round(random.uniform(2.5, 5.5), 3)
        account["term_years"] = random.choice([15, 30])
        account["monthly_payment"] = round(account["balance"] * (account["interest_rate"]/100/12) / (1 - (1 + account["interest_rate"]/100/12) ** (-account["term_years"]*12)), 2)
        account["property_address"] = generate_address()["formatted"]
        
    elif account_type in ["auto_loan", "personal_loan", "student_loan"]:
        account["original_loan_amount"] = round(account["balance"] * random.uniform(1.1, 1.3), 2)
        account["interest_rate"] = round(random.uniform(3.5, 9.9), 3)
        account["term_months"] = random.choice([24, 36, 48, 60, 72])
        account["monthly_payment"] = round(account["balance"] * (account["interest_rate"]/100/12) / (1 - (1 + account["interest_rate"]/100/12) ** (-account["term_months"])), 2)
        account["next_payment_date"] = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        
    elif account_type == "line_of_credit":
        account["credit_limit"] = round(random.uniform(5000, 50000), 2)
        account["available_credit"] = round(account["credit_limit"] - account["balance"], 2)
        account["interest_rate"] = round(random.uniform(7.99, 15.99), 2)
        account["minimum_payment"] = max(25.00, round(account["balance"] * 0.02, 2))
        
    return account

# Generate mock customer data with multiple accounts of each type
def generate_customer(customer_id=None):
    """Generate a mock customer with multiple accounts"""
    if customer_id is None:
        customer_id = ''.join(random.choices(string.digits, k=6))
    
    # Generate a random name
    first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "William", "Elizabeth", 
                   "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
                   "Daniel", "Lisa", "Matthew", "Nancy", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
                   "Steven", "Emily", "Andrew", "Donna", "Paul", "Michelle", "Joshua", "Melissa", "Kenneth", "Deborah"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", 
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
                  "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
                  "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
                  "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"]
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    # Generate address
    address = generate_address()
    
    # Generate email domains
    email_domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "hotmail.com", "aol.com"]
    email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(email_domains)}"
    
    # Generate phone number
    phone = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
    
    # Generate date of birth (21-80 years old)
    dob_year = datetime.now().year - random.randint(21, 80)
    dob_month = random.randint(1, 12)
    dob_day = random.randint(1, 28)  # Simplified to avoid month length issues
    dob = f"{dob_year}-{dob_month:02d}-{dob_day:02d}"
    
    # Generate customer since date (1-20 years ago)
    since_year = datetime.now().year - random.randint(1, 20)
    since_month = random.randint(1, 12)
    since_day = random.randint(1, 28)
    customer_since = f"{since_year}-{since_month:02d}-{since_day:02d}"
    
    # Create customer base data
    customer = {
        "customer_id": customer_id,
        "name": f"{first_name} {last_name}",
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "address": address["formatted"],
        "address_details": address,
        "dob": dob,
        "customer_since": customer_since,
        "preferred_language": random.choice(["English", "Spanish", "French", "Chinese", "Hindi"]),
        "accounts": {}
    }
    
    # Decide what account types this customer has
    has_checking = random.random() > 0.1  # 90% have checking
    has_savings = random.random() > 0.3   # 70% have savings
    has_credit_card = random.random() > 0.4  # 60% have credit card
    has_mortgage = random.random() > 0.7  # 30% have mortgage
    has_auto_loan = random.random() > 0.8  # 20% have auto loan
    has_investments = random.random() > 0.7  # 30% have investments
    
    # Generate accounts by type (potentially multiple per type)
    accounts_by_type = {}
    
    # Almost everyone has at least one checking account
    if has_checking:
        num_checking = random.choices([1, 2], weights=[0.8, 0.2])[0]  # 80% have 1, 20% have 2
        accounts_by_type["checking"] = [generate_account("checking") for _ in range(num_checking)]
    
    # Savings accounts
    if has_savings:
        num_savings = random.choices([1, 2], weights=[0.9, 0.1])[0]  # 90% have 1, 10% have 2
        accounts_by_type["savings"] = [generate_account("savings") for _ in range(num_savings)]
    
    # Credit cards
    if has_credit_card:
        num_cards = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]  # 60% have 1, 30% have 2, 10% have 3
        accounts_by_type["credit_card"] = [generate_account("credit_card") for _ in range(num_cards)]
    
    # Mortgage
    if has_mortgage:
        accounts_by_type["mortgage"] = [generate_account("mortgage")]
    
    # Auto loan
    if has_auto_loan:
        accounts_by_type["auto_loan"] = [generate_account("auto_loan")]
    
    # Investments and other accounts
    if has_investments:
        # Randomly choose which investment accounts they have
        if random.random() > 0.5:  # 50% of investors have money market
            accounts_by_type["money_market"] = [generate_account("money_market")]
        
        if random.random() > 0.6:  # 40% of investors have CDs
            num_cds = random.choices([1, 2], weights=[0.7, 0.3])[0]
            accounts_by_type["cd"] = [generate_account("cd") for _ in range(num_cds)]
        
        if random.random() > 0.4:  # 60% of investors have IRAs
            accounts_by_type["ira"] = [generate_account("ira")]
    
    # Personal loan (less common)
    if random.random() > 0.9:  # 10% have personal loan
        accounts_by_type["personal_loan"] = [generate_account("personal_loan")]
    
    # Add all accounts to customer
    customer["accounts"] = accounts_by_type
    
    # Return the complete customer data
    return customer

# Generate mock customer database with multiple customers
def generate_customers(num_customers=5):
    """Generate a database of mock customers"""
    customers = {}
    
    # Use fixed customer IDs for predictability in testing
    customer_ids = ["123456", "234567", "345678", "456789", "567890", "678901", "789012", "890123", "901234"]
    
    # Generate the specified number of customers
    for i in range(min(num_customers, len(customer_ids))):
        customer_id = customer_ids[i]
        customers[customer_id] = generate_customer(customer_id)
    
    return customers

# Generate the customer database
CUSTOMERS = generate_customers(8)

# Helper functions for account operations
def find_account_by_id(account_id):
    """Find an account by its ID across all customers."""
    for customer_id, customer in CUSTOMERS.items():
        for account_type, accounts in customer["accounts"].items():
            for account in accounts:
                if account["account_id"] == account_id:
                    return customer_id, account_type, account
    return None, None, None

def get_all_accounts(customer_id):
    """Get all accounts for a customer."""
    if customer_id not in CUSTOMERS:
        return []
    
    all_accounts = []
    for account_type, accounts in CUSTOMERS[customer_id]["accounts"].items():
        all_accounts.extend(accounts)
    
    return all_accounts

def get_accounts_by_type(customer_id, account_type):
    """Get all accounts of a specific type for a customer."""
    if customer_id not in CUSTOMERS or account_type not in CUSTOMERS[customer_id]["accounts"]:
        return []
    
    return CUSTOMERS[customer_id]["accounts"][account_type]

# Authentication middleware
def authenticate():
    """Authenticate API request using the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    
    # Basic check for API key
    if auth_header.startswith("Bearer "):
        api_key = auth_header[7:]  # Remove "Bearer " prefix
        if api_key == API_KEY:
            return True
    
    return False

@app.route('/')
def index():
    """API root endpoint that shows available endpoints."""
    return jsonify({
        "name": "Banking API Simulation Service",
        "version": "1.1.0",
        "description": "A realistic mock banking API for testing and integration with the Alchemist banking agent",
        "endpoints": [
            "/accounts",  # Get all accounts for a customer
            "/accounts/{account_id}",  # Get specific account details
            "/accounts/{account_id}/balance",  # Get account balance
            "/accounts/{account_id}/transactions",  # Get account transactions
            "/accounts/types",  # Get available account types
            "/transfers",  # Transfer between accounts
            "/customer/info",  # Get customer info
            "/customers",  # List all customers
            "/health"  # Health check
        ]
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/accounts/types')
def get_account_types():
    """
    Get all available account types.
    """
    # Check authentication
    if not authenticate():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Define available account types with descriptions
    account_types = {
        "checking": "Everyday checking account for regular transactions",
        "savings": "Interest-bearing savings account",
        "money_market": "High-yield money market account",
        "cd": "Certificate of deposit with fixed term",
        "ira": "Individual retirement account",
        "credit_card": "Credit card account",
        "mortgage": "Home mortgage loan",
        "auto_loan": "Vehicle loan",
        "personal_loan": "Unsecured personal loan",
        "student_loan": "Education loan",
        "line_of_credit": "Personal line of credit"
    }
    
    # Log request
    logger.info("Account types request")
    
    # Return account types
    return jsonify({
        "account_types": [{
            "type": account_type,
            "description": description
        } for account_type, description in account_types.items()]
    })

@app.route('/accounts')
def get_accounts():
    """
    Get all accounts for a customer.
    
    Query parameters:
    - customer_id: Customer ID
    - account_type: (Optional) Filter by account type
    """
    # Check authentication
    if not authenticate():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get customer ID from query parameters
    customer_id = request.args.get("customer_id")
    if not customer_id:
        return jsonify({"error": "Missing customer_id parameter"}), 400
    
    # Check if customer exists
    if customer_id not in CUSTOMERS:
        return jsonify({"error": f"Customer {customer_id} not found"}), 404
    
    # Get optional account type filter
    account_type = request.args.get("account_type")
    
    # Get accounts based on filter
    if account_type:
        accounts = get_accounts_by_type(customer_id, account_type)
        if not accounts:
            return jsonify({"error": f"No {account_type} accounts found for customer {customer_id}"}), 404
    else:
        accounts = get_all_accounts(customer_id)
    
    # Format account summaries
    account_summaries = []
    for account in accounts:
        summary = {
            "account_id": account["account_id"],
            "account_number": account["account_number"],
            "account_type": account["account_type"],
            "balance": account["balance"],
            "currency": account["currency"],
            "status": account["status"]
        }
        
        # Add type-specific summary fields
        if account["account_type"] == "credit_card":
            summary["available_credit"] = account.get("available_credit")
            summary["credit_limit"] = account.get("credit_limit")
            # Include masked card number
            if "card" in account and "masked" in account["card"]:
                summary["card_number_masked"] = account["card"]["masked"]
        elif account["account_type"] in ["mortgage", "auto_loan", "personal_loan", "student_loan"]:
            summary["remaining_balance"] = account["balance"]
            summary["monthly_payment"] = account.get("monthly_payment")
        
        account_summaries.append(summary)
    
    # Log request
    logger.info(f"Accounts request for customer {customer_id}")
    
    # Return accounts
    return jsonify({
        "customer_id": customer_id,
        "count": len(account_summaries),
        "accounts": account_summaries
    })

@app.route('/accounts/<account_id>')
def get_account_details(account_id):
    """
    Get detailed information for a specific account.
    
    Path parameters:
    - account_id: Account ID
    """
    # Check authentication
    if not authenticate():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Find the account
    customer_id, account_type, account = find_account_by_id(account_id)
    if not account:
        return jsonify({"error": f"Account {account_id} not found"}), 404
    
    # Log request
    logger.info(f"Account details request for account {account_id}")
    
    # Return account details
    return jsonify(account)

@app.route('/accounts/<account_id>/balance')
def get_balance(account_id):
    """
    Get balance for a specific account.
    
    Path parameters:
    - account_id: Account ID
    """
    # Check authentication
    if not authenticate():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Find the account
    customer_id, account_type, account = find_account_by_id(account_id)
    if not account:
        return jsonify({"error": f"Account {account_id} not found"}), 404
    
    # Log request
    logger.info(f"Balance inquiry for account {account_id}")
    
    # Prepare response based on account type
    response = {
        "account_id": account["account_id"],
        "account_number": account["account_number"],
        "account_type": account["account_type"],
        "balance": account["balance"],
        "currency": account["currency"],
        "last_updated": account["last_updated"]
    }
    
    # Add account-type specific details
    if account_type == "credit_card":
        response["available_credit"] = account.get("available_credit")
        response["credit_limit"] = account.get("credit_limit")
    elif account_type in ["mortgage", "auto_loan", "personal_loan", "student_loan"]:
        response["original_loan_amount"] = account.get("original_loan_amount")
        response["monthly_payment"] = account.get("monthly_payment")
    elif account_type in ["savings", "money_market", "cd", "ira"]:
        response["interest_rate"] = account.get("interest_rate")
    
    # Return balance
    return jsonify(response)

@app.route('/accounts/<account_id>/transactions')
def get_transactions(account_id):
    """
    Get transactions for a specific account.
    
    Path parameters:
    - account_id: Account ID
    
    Query parameters:
    - period: Time period (last_week, last_month, last_3_months, last_year, all)
    - category: Filter by transaction category
    - limit: Maximum number of transactions to return
    """
    # Check authentication
    if not authenticate():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Find the account
    customer_id, account_type, account = find_account_by_id(account_id)
    if not account:
        return jsonify({"error": f"Account {account_id} not found"}), 404
    
    # Get query parameters
    period = request.args.get("period", "last_month")
    category = request.args.get("category")
    limit_str = request.args.get("limit", "50")
    
    try:
        limit = int(limit_str)
        if limit < 1 or limit > 500:
            limit = 50  # Default to 50 if invalid
    except ValueError:
        limit = 50
    
    # Check if transactions exist for this account
    if "transactions" not in CUSTOMERS[customer_id]:
        # Initialize transactions if not present
        CUSTOMERS[customer_id]["transactions"] = {}
        
    if account_type not in CUSTOMERS[customer_id]["transactions"]:
        # Generate transactions for this account type
        for acc in CUSTOMERS[customer_id]["accounts"].get(account_type, []):
            if acc["account_id"] == account_id:
                transactions = generate_transactions(account_type, acc["balance"])
                CUSTOMERS[customer_id]["transactions"][account_type] = transactions
                break
    
    # Get transactions for this account type
    all_transactions = CUSTOMERS[customer_id]["transactions"].get(account_type, [])
    
    # If still no transactions, return empty
    if not all_transactions:
        return jsonify({
            "account_id": account_id,
            "account_number": account["account_number"],
            "account_type": account_type,
            "period": period,
            "transactions": [],
            "count": 0
        })
    
    # Filter transactions based on period
    today = datetime.now()
    if period == "last_week":
        cutoff_date = today - timedelta(days=7)
    elif period == "last_month":
        cutoff_date = today - timedelta(days=30)
    elif period == "last_3_months":
        cutoff_date = today - timedelta(days=90)
    elif period == "last_year":
        cutoff_date = today - timedelta(days=365)
    elif period == "all":
        cutoff_date = today - timedelta(days=3650)  # 10 years should cover all
    else:
        return jsonify({"error": f"Invalid period {period}"}), 400
    
    # Filter transactions by date
    filtered_transactions = [
        t for t in all_transactions 
        if datetime.strptime(t["date"], "%Y-%m-%d") >= cutoff_date
    ]
    
    # Filter by category if specified
    if category:
        filtered_transactions = [
            t for t in filtered_transactions 
            if t.get("category", "").lower() == category.lower()
        ]
    
    # Format transactions for response and limit
    transactions_formatted = []
    for t in filtered_transactions[:limit]:
        amount_str = f"${abs(t['amount']):.2f}"
        if t['amount'] < 0:
            amount_str = f"-{amount_str}"
        else:
            amount_str = f"+{amount_str}"
            
        transactions_formatted.append({
            "transaction_id": t.get("transaction_id", str(uuid.uuid4())),
            "date": t["date"],
            "description": t["description"],
            "category": t.get("category", "Uncategorized"),
            "amount": t["amount"],
            "amount_formatted": amount_str,
            "balance_after": t["balance_after"],
            "status": t.get("status", "completed")
        })
    
    # Log request
    logger.info(f"Transaction inquiry for account {account_id}, period {period}")
    
    # Return transactions
    return jsonify({
        "account_id": account_id,
        "account_number": account["account_number"],
        "account_type": account_type,
        "period": period,
        "transactions": transactions_formatted,
        "count": len(transactions_formatted),
        "total_available": len(filtered_transactions)
    })

@app.route('/transfers', methods=['POST'])
def transfer_funds():
    """
    Transfer funds between accounts.
    
    Request body:
    {
        "from_account_id": "account-uuid",
        "to_account_id": "account-uuid",
        "amount": 123.45,
        "description": "Optional transfer description"
    }
    """
    # Check authentication
    if not authenticate():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get request body
    data = request.json
    if not data:
        return jsonify({"error": "Missing request body"}), 400
    
    # Validate request parameters
    required_params = ["from_account_id", "to_account_id", "amount"]
    for param in required_params:
        if param not in data:
            return jsonify({"error": f"Missing required parameter: {param}"}), 400
    
    # Extract parameters
    from_account_id = data["from_account_id"]
    to_account_id = data["to_account_id"]
    amount = float(data["amount"])
    description = data.get("description", "Transfer")
    
    # Find source account
    from_customer_id, from_account_type, from_account = find_account_by_id(from_account_id)
    if not from_account:
        return jsonify({"error": f"Source account {from_account_id} not found"}), 404
    
    # Find destination account
    to_customer_id, to_account_type, to_account = find_account_by_id(to_account_id)
    if not to_account:
        return jsonify({"error": f"Destination account {to_account_id} not found"}), 404
    
    # Check if amount is valid
    if amount <= 0:
        return jsonify({"error": "Amount must be greater than zero"}), 400
    
    # Check if source account has sufficient funds
    # Credit cards and lines of credit are sources of funds (negative balance means available credit)
    if from_account_type not in ["credit_card", "line_of_credit"] and from_account["balance"] < amount:
        return jsonify({"error": f"Insufficient funds in {from_account_type} account"}), 400
    
    # For credit accounts, check if there's enough available credit
    if from_account_type in ["credit_card", "line_of_credit"]:
        available_credit = from_account.get("available_credit", 0)
        if available_credit < amount:
            return jsonify({"error": f"Insufficient available credit"}), 400
    
    # Generate reference ID
    reference_id = f"TRF-{str(uuid.uuid4())[:8].upper()}"
    
    # In a real implementation, we would actually update the account balances
    # For this mock API, let's simulate the transfer by updating the balances
    
    # Update source account (subtract amount)
    if from_account_type in ["credit_card", "line_of_credit"]:
        # For credit accounts, balance increases (more debt)
        from_account["balance"] += amount
        from_account["available_credit"] -= amount
    else:
        # For deposit accounts, balance decreases
        from_account["balance"] -= amount
    
    # Update destination account (add amount)
    if to_account_type in ["credit_card", "line_of_credit"]:
        # For credit accounts, balance decreases (less debt)
        to_account["balance"] -= amount
        to_account["available_credit"] += amount
    else:
        # For deposit accounts, balance increases
        to_account["balance"] += amount
    
    # Update last_updated timestamp
    current_date = datetime.now().strftime("%Y-%m-%d")
    from_account["last_updated"] = current_date
    to_account["last_updated"] = current_date
    
    # Record the transactions in both accounts
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y-%m-%d")
    
    # Create source transaction
    source_transaction = {
        "transaction_id": generate_transaction_id(),
        "date": date_str,
        "description": f"TRANSFER TO {to_account['account_number'][-6:]} - {description}",
        "category": "Transfer",
        "amount": -amount,  # Negative for outgoing
        "balance_after": from_account["balance"],
        "status": "completed",
        "timestamp": timestamp.isoformat(),
        "reference_id": reference_id,
        "transfer_details": {
            "to_account_id": to_account_id,
            "to_account_number": to_account["account_number"],
            "to_account_type": to_account_type
        }
    }
    
    # Create destination transaction
    dest_transaction = {
        "transaction_id": generate_transaction_id(),
        "date": date_str,
        "description": f"TRANSFER FROM {from_account['account_number'][-6:]} - {description}",
        "category": "Transfer",
        "amount": amount,  # Positive for incoming
        "balance_after": to_account["balance"],
        "status": "completed",
        "timestamp": timestamp.isoformat(),
        "reference_id": reference_id,
        "transfer_details": {
            "from_account_id": from_account_id,
            "from_account_number": from_account["account_number"],
            "from_account_type": from_account_type
        }
    }
    
    # Add transactions to accounts
    if "transactions" not in CUSTOMERS[from_customer_id]:
        CUSTOMERS[from_customer_id]["transactions"] = {}
    if from_account_type not in CUSTOMERS[from_customer_id]["transactions"]:
        CUSTOMERS[from_customer_id]["transactions"][from_account_type] = []
    
    if "transactions" not in CUSTOMERS[to_customer_id]:
        CUSTOMERS[to_customer_id]["transactions"] = {}
    if to_account_type not in CUSTOMERS[to_customer_id]["transactions"]:
        CUSTOMERS[to_customer_id]["transactions"][to_account_type] = []
    
    # Insert at the beginning (most recent first)
    CUSTOMERS[from_customer_id]["transactions"][from_account_type].insert(0, source_transaction)
    CUSTOMERS[to_customer_id]["transactions"][to_account_type].insert(0, dest_transaction)
    
    # Log request
    logger.info(f"Fund transfer: {amount} from account {from_account_id} to account {to_account_id}")
    
    # Return transfer confirmation
    return jsonify({
        "from_account_id": from_account_id,
        "from_account_number": from_account["account_number"],
        "from_account_type": from_account_type,
        "to_account_id": to_account_id,
        "to_account_number": to_account["account_number"],
        "to_account_type": to_account_type,
        "amount": amount,
        "currency": "USD",
        "description": description,
        "reference_id": reference_id,
        "timestamp": timestamp.isoformat(),
        "status": "completed"
    })

@app.route('/customer/info')
def get_customer_info():
    """
    Get customer information.
    
    Query parameters:
    - customer_id: Customer ID
    - include_address: Whether to include address information (true/false)
    """
    # Check authentication
    if not authenticate():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get customer ID from query parameters
    customer_id = request.args.get("customer_id")
    if not customer_id:
        return jsonify({"error": "Missing customer_id parameter"}), 400
    
    # Get include_address parameter
    include_address = request.args.get("include_address", "false").lower() == "true"
    
    # Check if customer exists
    if customer_id not in CUSTOMERS:
        return jsonify({"error": f"Customer {customer_id} not found"}), 404
    
    # Get customer details (excluding sensitive information)
    customer = CUSTOMERS[customer_id]
    
    # Build account summary
    accounts = []
    for account_type, account_list in customer["accounts"].items():
        # Each account_type maps to a list of accounts
        for account in account_list:
            accounts.append({
                "type": account_type,
                "account_number": account["account_number"],
                "balance": account["balance"],
                "currency": account["currency"]
            })
    
    # Prepare response
    response = {
        "customer_id": customer_id,
        "name": customer["name"],
        "email": customer["email"],
        "phone": customer["phone"],
        "customer_since": customer.get("customer_since"),
        "accounts": accounts
    }
    
    # Include address if requested
    if include_address and "address" in customer:
        response["address"] = customer["address"]
    
    # Log request
    logger.info(f"Customer info request for customer {customer_id}")
    
    # Return customer info
    return jsonify(response)

# Initialize transaction data for all customers
def initialize_transactions():
    """Initialize transaction data for all customers."""
    for customer_id, customer in CUSTOMERS.items():
        customer["transactions"] = {}
        for account_type, accounts in customer["accounts"].items():
            # For each account of this type
            for account in accounts:
                # Generate transactions for this specific account
                if account_type not in customer["transactions"]:
                    customer["transactions"][account_type] = []
                
                # Generate transactions for this account
                transactions = generate_transactions(
                    account_type, 
                    account["balance"],
                    num_transactions=random.randint(5, 15),
                    max_days=random.randint(15, 45)
                )
                
                # Add to the transactions list for this account type
                customer["transactions"][account_type].extend(transactions)

@app.route('/customers')
def get_all_customers():
    """Get a list of all customers."""
    # Check authentication
    if not authenticate():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Prepare customer summaries (without sensitive data)
    customer_summaries = []
    for customer_id, customer in CUSTOMERS.items():
        customer_summaries.append({
            "customer_id": customer_id,
            "name": customer["name"],
            "email": customer["email"],
            "phone": customer["phone"],
            "account_types": list(customer["accounts"].keys())
        })
    
    # Log request
    logger.info("Customer list request")
    
    # Return customer summaries
    return jsonify({
        "count": len(customer_summaries),
        "customers": customer_summaries
    })

if __name__ == '__main__':
    # Initialize transaction data
    initialize_transactions()
    
    # Use a fixed port to avoid conflicts
    port = 8082
    
    print(f"Starting Banking API Simulation Service on port {port}...")
    
    # Run the Flask app with explicit port
    app.run(host='0.0.0.0', port=port, debug=False)
