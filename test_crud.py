"""
FinTrack – CRUD Test
Verifies all four CRUD operations against the live MongoDB Atlas database.

Usage:
    .\.venv\Scripts\python.exe test_crud.py
"""

from database.connection import client
from database.transactions import (
    add_transaction,
    get_transactions,
    update_transaction,
    delete_transaction,
)

transaction_id = None

try:
    # ── CREATE ────────────────────────────────────────────────────────────────
    transaction_id = add_transaction(
        title="FINTRACK Test Expense",
        amount=250.00,
        transaction_type="expense",
        category="Food",
        notes="CRUD verification",
    )
    print("CREATE passed:", transaction_id)

    # ── READ ──────────────────────────────────────────────────────────────────
    records = get_transactions()
    print("READ passed:", len(records), "record(s) found")

    # ── UPDATE ────────────────────────────────────────────────────────────────
    modified_count = update_transaction(transaction_id, 300.00)
    print("UPDATE operation completed:", modified_count)

    # Verify the update
    records = get_transactions()
    updated_record = next((r for r in records if str(r["_id"]) == transaction_id), None)
    assert updated_record is not None, "Updated record not found."
    assert updated_record["amount"] == 300.00, (
        f"Expected 300.00 but got {updated_record['amount']}"
    )
    print("UPDATE verification passed")

finally:
    # ── DELETE (cleanup) ──────────────────────────────────────────────────────
    if transaction_id:
        deleted_count = delete_transaction(transaction_id)
        print("Test cleanup completed:", deleted_count, "record(s) deleted")
    client.close()

print("CRUD test finished.")
