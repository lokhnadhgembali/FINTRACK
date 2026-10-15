"""
FinTrack - Budgets Module
CRUD operations for monthly category budget limits stored in MongoDB.
"""

from database.connection import budgets as _budgets_col
from pymongo.errors import PyMongoError


def set_or_update_budget(category: str, monthly_limit: float) -> None:
    """
    Create or update a monthly budget limit for a category.

    Args:
        category      (str)   : Category name (non-empty).
        monthly_limit (float) : Positive limit value in INR.

    Raises:
        ValueError    : If inputs are invalid.
        PyMongoError  : On database failure.
    """
    if not isinstance(category, str) or not category.strip():
        raise ValueError("category must be a non-empty string.")
    if not isinstance(monthly_limit, (int, float)) or monthly_limit <= 0:
        raise ValueError("monthly_limit must be a positive number.")

    try:
        _budgets_col.update_one(
            {"category": category.strip()},
            {"$set": {"category": category.strip(), "monthly_limit": float(monthly_limit)}},
            upsert=True,
        )
    except PyMongoError as e:
        raise PyMongoError(f"Failed to save budget: {e}") from e


def get_all_budgets() -> list:
    """
    Return all budget documents.

    Returns:
        list[dict]: Budget documents with at least 'category' and 'monthly_limit'.
    """
    try:
        return list(_budgets_col.find())
    except PyMongoError as e:
        raise PyMongoError(f"Failed to fetch budgets: {e}") from e


def delete_budget(category: str) -> int:
    """
    Delete a budget by category name.

    Args:
        category (str): Category name.

    Returns:
        int: Number of documents deleted (0 or 1).
    """
    if not isinstance(category, str) or not category.strip():
        raise ValueError("category must be a non-empty string.")
    try:
        result = _budgets_col.delete_one({"category": category.strip()})
        return result.deleted_count
    except PyMongoError as e:
        raise PyMongoError(f"Failed to delete budget: {e}") from e
