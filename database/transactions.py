"""
FinTrack – Transactions & Goals CRUD Operations
Provides add / read / update / delete for transactions and savings goals.
"""

from datetime import datetime, timezone, date as date_type
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import PyMongoError

from database.connection import transactions, savings_goals


# ──────────────────────────────────────────────────────────────────────────────
# TRANSACTIONS
# ──────────────────────────────────────────────────────────────────────────────

def add_transaction(title, amount, transaction_type, category, notes="", date=None):
    """
    Insert a new transaction document.

    Args:
        title (str)             : Non-empty transaction title.
        amount (int|float)      : Positive monetary amount.
        transaction_type (str)  : 'income' or 'expense'.
        category (str)          : Non-empty category name.
        notes (str)             : Optional notes (default '').
        date (date|datetime|None): Transaction date. Accepts a datetime.date
                                  (from Streamlit date_input), a datetime, or
                                  None (defaults to UTC now).

    Returns:
        str: Inserted document _id as string.

    Raises:
        ValueError: On validation failure.
    """
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be a non-empty string.")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("amount must be a positive number (int or float).")
    if transaction_type not in ("income", "expense"):
        raise ValueError("transaction_type must be either 'income' or 'expense'.")
    if not isinstance(category, str) or not category.strip():
        raise ValueError("category must be a non-empty string.")

    # ── Date normalisation ────────────────────────────────────────────────────
    if date is None:
        txn_date = datetime.now(timezone.utc)
    elif isinstance(date, datetime):
        txn_date = date if date.tzinfo else date.replace(tzinfo=timezone.utc)
    elif isinstance(date, date_type):
        txn_date = datetime.combine(date, datetime.min.time(), tzinfo=timezone.utc)
    else:
        txn_date = datetime.now(timezone.utc)

    document = {
        "title":    title.strip(),
        "amount":   round(float(amount), 2),
        "type":     transaction_type,
        "category": category.strip(),
        "notes":    notes.strip() if isinstance(notes, str) else "",
        "date":     txn_date,
    }
    result = transactions.insert_one(document)
    return str(result.inserted_id)


def get_transactions():
    """Return all transactions sorted by date descending."""
    try:
        return list(transactions.find().sort("date", -1))
    except PyMongoError as e:
        raise PyMongoError(f"Failed to fetch transactions: {e}") from e


def update_transaction(transaction_id, new_amount):
    """
    Update the amount of an existing transaction.

    Returns:
        int: Number of documents modified (0 or 1).
    """
    if isinstance(new_amount, bool) or not isinstance(new_amount, (int, float)) or new_amount <= 0:
        raise ValueError("new_amount must be a positive number.")
    try:
        object_id = ObjectId(transaction_id)
    except (InvalidId, TypeError):
        raise ValueError("Invalid transaction ID.")

    result = transactions.update_one(
        {"_id": object_id},
        {"$set": {"amount": round(float(new_amount), 2)}},
    )
    return result.modified_count


def delete_transaction(transaction_id):
    """
    Delete a transaction by its ID.

    Returns:
        int: Number of documents deleted (0 or 1).
    """
    try:
        object_id = ObjectId(transaction_id)
    except (InvalidId, TypeError):
        raise ValueError("Invalid transaction ID.")

    result = transactions.delete_one({"_id": object_id})
    return result.deleted_count


# ──────────────────────────────────────────────────────────────────────────────
# SAVINGS GOALS
# ──────────────────────────────────────────────────────────────────────────────

def add_goal(name, target_amount, saved_amount=0.0):
    """
    Insert a new savings goal.

    Args:
        name (str)            : Non-empty goal name.
        target_amount (float) : Positive target amount.
        saved_amount (float)  : Amount already saved (default 0).

    Returns:
        str: Inserted document _id as string.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string.")
    if isinstance(target_amount, bool) or not isinstance(target_amount, (int, float)) or target_amount <= 0:
        raise ValueError("target_amount must be a positive number.")

    saved = float(saved_amount) if not isinstance(saved_amount, bool) else 0.0
    saved = max(0.0, saved)

    document = {
        "name":          name.strip(),
        "target_amount": round(float(target_amount), 2),
        "saved_amount":  round(saved, 2),
        "completed":     saved >= float(target_amount),
        "created_at":    datetime.now(timezone.utc),
    }
    result = savings_goals.insert_one(document)
    return str(result.inserted_id)


def get_goals():
    """Return all savings goals."""
    try:
        return list(savings_goals.find())
    except PyMongoError as e:
        raise PyMongoError(f"Failed to fetch goals: {e}") from e


# ──────────────────────────────────────────────────────────────────────────────
# SEED DATA
# ──────────────────────────────────────────────────────────────────────────────

def seed_sample_data_if_empty():
    """
    Insert 6 months of realistic sample data (Jan–Jun 2025) and 4 savings
    goals when the transactions collection is empty.

    Returns:
        bool: True if data was seeded, False if collection already had data.
    """
    if transactions.count_documents({}) > 0:
        return False

    YEAR = 2025
    MONTH_NAMES = {
        1: "January", 2: "February", 3: "March",
        4: "April",   5: "May",      6: "June",
    }

    # ── Monthly salary income ────────────────────────────────────────────────
    for month in range(1, 7):
        add_transaction(
            title=f"{MONTH_NAMES[month]} Salary",
            amount=45000,
            transaction_type="income",
            category="Salary",
            notes="Monthly salary credit",
            date=datetime(YEAR, month, 1, tzinfo=timezone.utc),
        )

    # ── Expense transactions (month, category, title, amount, day) ───────────
    _EXPENSES = [
        # ── January (total ≈ ₹19,000) ──────────────────────────────────────
        (1, "Food",             "Grocery Shopping",      3200,  3),
        (1, "Food",             "Restaurant Dinner",     1800, 12),
        (1, "Food",             "Office Lunch",           900, 20),
        (1, "Food",             "Snacks & Beverages",     400, 27),
        (1, "Shopping",         "Winter Clothes",        2500,  5),
        (1, "Shopping",         "Amazon Purchase",       1400, 18),
        (1, "Transport",        "Monthly Metro Pass",    1500,  2),
        (1, "Transport",        "Cab Rides",             1300, 25),
        (1, "Bills & Utilities","Electricity Bill",      1200,  8),
        (1, "Bills & Utilities","Internet Plan",          800,  8),
        (1, "Entertainment",    "Movie Tickets",          600, 14),
        (1, "Entertainment",    "Streaming Services",     500,  1),
        (1, "Entertainment",    "Weekend Outing",         900, 21),
        (1, "Others",           "Miscellaneous",         2000, 28),
        # ── February (total ≈ ₹21,200) ─────────────────────────────────────
        (2, "Food",             "Grocery Shopping",      3800,  4),
        (2, "Food",             "Valentine's Dinner",    2200, 14),
        (2, "Food",             "Office Lunch",          1200, 20),
        (2, "Shopping",         "Valentine's Gift",      3000, 12),
        (2, "Shopping",         "Online Shopping",       1400, 22),
        (2, "Transport",        "Monthly Metro Pass",    1500,  1),
        (2, "Transport",        "Fuel",                  1700, 18),
        (2, "Bills & Utilities","Electricity Bill",      1200,  7),
        (2, "Bills & Utilities","Mobile Recharge",        500,  7),
        (2, "Bills & Utilities","Water Bill",             500, 15),
        (2, "Entertainment",    "Movie Night",            700, 10),
        (2, "Entertainment",    "Netflix",                500,  1),
        (2, "Entertainment",    "Weekend Fun",           1000, 24),
        (2, "Others",           "Pharmacy",              2000, 19),
        # ── March (total ≈ ₹23,000) ────────────────────────────────────────
        (3, "Food",             "Grocery Shopping",      4200,  3),
        (3, "Food",             "Restaurant Lunch",      1800, 10),
        (3, "Food",             "Holi Sweets",           1800, 25),
        (3, "Shopping",         "Spring Clothes",        2800,  8),
        (3, "Shopping",         "Electronics Accessories",1900, 20),
        (3, "Transport",        "Monthly Metro Pass",    1500,  1),
        (3, "Transport",        "Road Trip Fuel",        1900, 22),
        (3, "Bills & Utilities","Electricity Bill",      1300,  6),
        (3, "Bills & Utilities","Internet",               800,  6),
        (3, "Bills & Utilities","Gym Membership",         200, 15),
        (3, "Entertainment",    "Holi Party",             900, 25),
        (3, "Entertainment",    "Prime & Netflix",        700,  1),
        (3, "Entertainment",    "Concert Tickets",        700, 18),
        (3, "Others",           "Home Maintenance",      2500, 28),
        # ── April (total ≈ ₹24,000) ────────────────────────────────────────
        (4, "Food",             "Grocery Shopping",      4500,  2),
        (4, "Food",             "Office Dinner",         2000, 15),
        (4, "Food",             "Weekend Brunch",        1900, 27),
        (4, "Shopping",         "Summer Clothes",        3200,  6),
        (4, "Shopping",         "Books & Stationery",    1800, 19),
        (4, "Transport",        "Monthly Metro Pass",    1500,  1),
        (4, "Transport",        "Ola / Uber Rides",      2100, 20),
        (4, "Bills & Utilities","Electricity Bill",      1400,  5),
        (4, "Bills & Utilities","Internet",               800,  5),
        (4, "Bills & Utilities","Water Tax",              250, 12),
        (4, "Entertainment",    "IPL Match Tickets",     1200,  8),
        (4, "Entertainment",    "Streaming",              500,  1),
        (4, "Entertainment",    "Weekend Outing",         650, 21),
        (4, "Others",           "Gifts & Donations",     2200, 29),
        # ── May (total ≈ ₹25,400) ──────────────────────────────────────────
        (5, "Food",             "Grocery Shopping",      5000,  3),
        (5, "Food",             "Team Lunch",            2200, 12),
        (5, "Food",             "Restaurant Visits",     1800, 25),
        (5, "Shopping",         "Online Sale",           3500, 10),
        (5, "Shopping",         "Home Decor",            1500, 22),
        (5, "Transport",        "Monthly Metro Pass",    1500,  1),
        (5, "Transport",        "Fuel & Cabs",           2400, 18),
        (5, "Bills & Utilities","Electricity Bill",      1600,  6),
        (5, "Bills & Utilities","Internet & Phone",       900,  6),
        (5, "Entertainment",    "Movies",                 800, 11),
        (5, "Entertainment",    "Subscriptions",          700,  1),
        (5, "Entertainment",    "Gaming",                1000, 28),
        (5, "Others",           "Medical & Health",      2500, 20),
        # ── June (total ≈ ₹26,550) — Food = ₹9,975 to match template ───────
        (6, "Food",             "Grocery Shopping",      5500,  2),
        (6, "Food",             "Lunch at Cafe",          450, 10),
        (6, "Food",             "Restaurant Dinner",     1800, 18),
        (6, "Food",             "Snacks & Beverages",     800, 25),
        (6, "Food",             "Weekly Groceries",      1425, 28),
        (6, "Shopping",         "Amazon Purchase",       1200,  9),
        (6, "Shopping",         "Monsoon Essentials",    3500, 20),
        (6, "Transport",        "Metro Recharge",         300, 28),
        (6, "Transport",        "Cab Rides",             1500, 15),
        (6, "Transport",        "Fuel",                  2075, 22),
        (6, "Bills & Utilities","Electricity Bill",      1500,  5),
        (6, "Bills & Utilities","Internet & OTT",        1350, 25),
        (6, "Entertainment",    "Movie Tickets",          600,  8),
        (6, "Entertainment",    "Streaming Services",     700,  1),
        (6, "Entertainment",    "Weekend Outing",        1200, 21),
        (6, "Others",           "Miscellaneous",         2650, 29),
    ]

    for month, category, title, amount, day in _EXPENSES:
        add_transaction(
            title=title,
            amount=amount,
            transaction_type="expense",
            category=category,
            date=datetime(YEAR, month, day, tzinfo=timezone.utc),
        )

    # ── Savings goals ─────────────────────────────────────────────────────────
    if savings_goals.count_documents({}) == 0:
        add_goal("Emergency Fund",   50000,  50000)   # ✅ completed
        add_goal("Laptop Upgrade",   80000,  80000)   # ✅ completed
        add_goal("Family Vacation", 150000,  75000)   # 50 % active
        add_goal("New Car Fund",    500000, 100000)   # 20 % active

    return True
