"""
FinTrack - Analytics Module
MongoDB aggregation pipelines for spending insights and reporting.
"""

from datetime import datetime, timezone
from database.connection import transactions


def get_category_expense_breakdown():
    """
    Aggregate total expenses grouped by category, sorted by highest spend.

    Returns:
        list[dict]: [{"category": str, "total": float, "count": int}, ...]
    """
    pipeline = [
        {"$match": {"type": "expense"}},
        {
            "$group": {
                "_id":   "$category",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"total": -1}},
    ]
    try:
        results = list(transactions.aggregate(pipeline))
        return [
            {"category": doc["_id"], "total": doc["total"], "count": doc["count"]}
            for doc in results
        ]
    except Exception as e:
        raise RuntimeError(f"Analytics error (category breakdown): {e}") from e


def get_monthly_income_expense_summary(year=None):
    """
    Aggregate monthly income, expenses, and savings.
    """
    match_stage = {}
    if year is not None:
        start = datetime(year, 1, 1, tzinfo=timezone.utc)
        end   = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        match_stage = {"date": {"$gte": start, "$lt": end}}

    pipeline = [
        *(([{"$match": match_stage}]) if match_stage else []),
        {
            "$group": {
                "_id": {
                    "year":  {"$year":  "$date"},
                    "month": {"$month": "$date"},
                    "type":  "$type",
                },
                "total": {"$sum": "$amount"},
            }
        },
    ]

    try:
        raw = list(transactions.aggregate(pipeline))
    except Exception as e:
        raise RuntimeError(f"Analytics error (monthly summary): {e}") from e

    buckets: dict = {}
    for doc in raw:
        y = doc["_id"]["year"]
        m = doc["_id"]["month"]
        t = doc["_id"]["type"]
        key = (y, m)
        if key not in buckets:
            buckets[key] = {"year": y, "month": m, "income": 0.0, "expenses": 0.0}
        if t == "income":
            buckets[key]["income"] = doc["total"]
        elif t == "expense":
            buckets[key]["expenses"] = doc["total"]

    _MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    result = []
    for (y, m), data in sorted(buckets.items()):
        data["month_label"] = _MONTH_LABELS[m - 1]
        data["savings"]     = data["income"] - data["expenses"]
        result.append(data)

    return result


def get_total_spent_by_category_for_month(category: str, year: int, month: int) -> float:
    """
    Sum expense amounts for a specific category within a calendar month.
    """
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    start    = datetime(year, month, 1,        tzinfo=timezone.utc)
    end      = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    pipeline = [
        {
            "$match": {
                "type":     "expense",
                "category": category,
                "date":     {"$gte": start, "$lte": end},
            }
        },
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    try:
        result = list(transactions.aggregate(pipeline))
        return result[0]["total"] if result else 0.0
    except Exception as e:
        raise RuntimeError(f"Analytics error (category/month spend): {e}") from e
