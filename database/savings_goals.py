"""
FinTrack - Savings Goals Module
CRUD operations for the savings_goals collection in MongoDB.
"""

from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import PyMongoError

from database.connection import savings_goals as _goals_col


def add_savings_goal(
    name: str,
    target_amount: float,
    current_amount: float = 0.0,
    target_date=None,
) -> str:
    """
    Insert a new savings goal document.

    Args:
        name           (str)            : Non-empty goal name.
        target_amount  (float)          : Positive target in INR.
        current_amount (float)          : Initial deposit (default 0).
        target_date    (date|None)      : Optional target completion date.

    Returns:
        str: Inserted document _id as string.

    Raises:
        ValueError   : On invalid input.
        PyMongoError : On database failure.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string.")
    if not isinstance(target_amount, (int, float)) or target_amount <= 0:
        raise ValueError("target_amount must be a positive number.")

    cur = max(0.0, float(current_amount))
    doc = {
        "name":           name.strip(),
        "target_amount":  round(float(target_amount), 2),
        "current_amount": round(cur, 2),
        "completed":      cur >= float(target_amount),
        "created_at":     datetime.now(timezone.utc),
    }
    if target_date is not None:
        if isinstance(target_date, datetime):
            doc["target_date"] = target_date
        else:
            try:
                doc["target_date"] = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
            except Exception:
                pass

    try:
        result = _goals_col.insert_one(doc)
        return str(result.inserted_id)
    except PyMongoError as e:
        raise PyMongoError(f"Failed to add savings goal: {e}") from e


def get_all_savings_goals() -> list:
    """
    Return all savings goal documents sorted by created_at descending.

    Returns:
        list[dict]: All savings goal documents.
    """
    try:
        return list(_goals_col.find().sort("created_at", -1))
    except PyMongoError as e:
        raise PyMongoError(f"Failed to fetch savings goals: {e}") from e


def update_goal_progress(goal_id: str, additional_amount: float) -> int:
    """
    Add funds to a savings goal by incrementing current_amount.

    Args:
        goal_id           (str)   : MongoDB ObjectId string.
        additional_amount (float) : Positive amount to add.

    Returns:
        int: Number of documents modified (0 or 1).

    Raises:
        ValueError   : On invalid inputs.
        PyMongoError : On database failure.
    """
    if not isinstance(additional_amount, (int, float)) or additional_amount <= 0:
        raise ValueError("additional_amount must be a positive number.")
    try:
        oid = ObjectId(goal_id)
    except (InvalidId, TypeError):
        raise ValueError("Invalid goal_id.")

    try:
        # Increment and then set completed flag based on updated values
        result = _goals_col.update_one(
            {"_id": oid},
            {"$inc": {"current_amount": float(additional_amount)}},
        )
        # Refresh completed flag
        doc = _goals_col.find_one({"_id": oid})
        if doc:
            completed = doc.get("current_amount", 0) >= doc.get("target_amount", 1)
            _goals_col.update_one({"_id": oid}, {"$set": {"completed": completed}})
        return result.modified_count
    except PyMongoError as e:
        raise PyMongoError(f"Failed to update goal progress: {e}") from e


def delete_savings_goal(goal_id: str) -> int:
    """
    Delete a savings goal by its ObjectId string.

    Args:
        goal_id (str): MongoDB ObjectId string.

    Returns:
        int: Number of documents deleted (0 or 1).

    Raises:
        ValueError   : On invalid goal_id.
        PyMongoError : On database failure.
    """
    try:
        oid = ObjectId(goal_id)
    except (InvalidId, TypeError):
        raise ValueError("Invalid goal_id.")
    try:
        result = _goals_col.delete_one({"_id": oid})
        return result.deleted_count
    except PyMongoError as e:
        raise PyMongoError(f"Failed to delete savings goal: {e}") from e
