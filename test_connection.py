"""
FinTrack – MongoDB Connection Test
Run this script to verify your MongoDB connection before launching the app.

Usage:
    python test_connection.py
"""

from database.connection import client, db


try:
    result = client.admin.command("ping")
    print("FINTRACK MongoDB connection successful!")
    print("Database name:", db.name)
    print("Ping result:", result)
    print("Collections:", db.list_collection_names())
finally:
    client.close()
