"""
FinTrack – MongoDB Connection Module
Establishes the database connection and exposes collection variables.
"""

import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def _get_secret(key, default=None):
    """Retrieve secret from os.getenv (dotenv) or Streamlit st.secrets."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default

MONGO_URI = _get_secret("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI is missing. Check your .env file or Streamlit secrets.")

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

# Select database
db = client["fintrack_db"]

# Define collections
transactions  = db["transactions"]
budgets       = db["budgets"]
savings_goals = db["savings_goals"]
settings      = db["settings"]

db_connected = False
db_error = None
_indexes_created = False

def check_connection(force=False):
    """Check if MongoDB Atlas is reachable, and initialize indexes once connected."""
    global db_connected, db_error, _indexes_created
    if db_connected and not force:
        return True
    try:
        client.admin.command("ping")
        db_connected = True
        db_error = None
        if not _indexes_created:
            try:
                transactions.create_index([("date", DESCENDING)])
                transactions.create_index([("type", ASCENDING), ("category", ASCENDING)])
                _indexes_created = True
            except Exception:
                pass
        return True
    except Exception as e:
        db_connected = False
        db_error = str(e)
        return False

# Initial check
check_connection()


