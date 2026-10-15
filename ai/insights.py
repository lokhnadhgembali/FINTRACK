"""
FinTrack - AI Finance Insights Module
Uses Groq LLM to generate personalized financial insights and a chat interface
backed by live MongoDB spending data.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def _get_api_key():
    """Retrieve GROQ_API_KEY from os.getenv (dotenv) or Streamlit st.secrets."""
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    return None

GROQ_API_KEY = _get_api_key()

_groq_client = None

def _get_client():
    """Lazy-init Groq client; returns None if API key is missing."""
    global _groq_client, GROQ_API_KEY
    if _groq_client is not None:
        return _groq_client
    api_key = GROQ_API_KEY or _get_api_key()
    if not api_key:
        return None
    try:
        from groq import Groq
        _groq_client = Groq(api_key=api_key)
        return _groq_client
    except Exception:
        return None


_SYSTEM_PROMPT = (
    "You are FINTRACK's expert personal finance AI advisor. "
    "Analyze the user's live financial data and provide 3-4 crisp, highly actionable bullet points: "
    "highlight their biggest spending leaks, assess their savings rate, evaluate progress toward "
    "active goals, and give one concrete tip to save more money. "
    "Keep tone encouraging, realistic, and succinct without unnecessary pleasantries. "
    "Use the \u20b9 (Indian Rupee) currency symbol. "
    "Format each insight as a bullet starting with a relevant emoji."
)

_CHAT_SYSTEM_TEMPLATE = (
    "You are FINTRACK's expert personal finance AI advisor. "
    "You have access to the user's live financial summary below. "
    "Answer their questions with specific numbers from the data, be concise and actionable. "
    "Use the \u20b9 (Indian Rupee) currency symbol.\n\n"
    "--- FINANCIAL SUMMARY ---\n{context}\n--- END OF SUMMARY ---"
)


def _build_financial_context() -> str:
    """
    Fetches live MongoDB data and builds a concise text summary for the LLM.
    """
    lines = []

    # Transactions summary
    try:
        from database.transactions import get_transactions
        txns = get_transactions()
        total_income   = sum(t["amount"] for t in txns if t.get("type") == "income")
        total_expenses = sum(t["amount"] for t in txns if t.get("type") == "expense")
        net_savings    = total_income - total_expenses
        sav_rate       = (net_savings / total_income * 100) if total_income else 0
        lines.append(f"Total Income: \u20b9{total_income:,.0f}")
        lines.append(f"Total Expenses: \u20b9{total_expenses:,.0f}")
        lines.append(f"Net Savings: \u20b9{net_savings:,.0f} ({sav_rate:.1f}% savings rate)")
        lines.append(f"Total Transactions: {len(txns)}")
    except Exception as e:
        lines.append(f"[Transaction data unavailable: {e}]")

    # Category breakdown
    try:
        from database.analytics import get_category_expense_breakdown
        breakdown = get_category_expense_breakdown()
        if breakdown:
            lines.append("\nCategory-wise Spending (all time):")
            for item in breakdown[:8]:
                lines.append(f"  - {item['category']}: \u20b9{item['total']:,.0f} ({item['count']} transactions)")
    except Exception as e:
        lines.append(f"[Category breakdown unavailable: {e}]")

    # Budgets vs actuals
    try:
        from database.budgets import get_all_budgets
        from database.analytics import get_total_spent_by_category_for_month
        from datetime import datetime
        budgets = get_all_budgets()
        if budgets:
            now = datetime.now()
            lines.append(f"\nMonthly Budget Status ({now.strftime('%B %Y')}):")
            for b in budgets:
                cat = b["category"]
                lim = b["monthly_limit"]
                try:
                    spent = get_total_spent_by_category_for_month(cat, now.year, now.month)
                except Exception:
                    spent = 0.0
                pct = (spent / lim * 100) if lim else 0
                status = "OVER" if spent > lim else f"{pct:.0f}% used"
                lines.append(f"  - {cat}: \u20b9{spent:,.0f} / \u20b9{lim:,.0f} ({status})")
    except Exception as e:
        lines.append(f"[Budget data unavailable: {e}]")

    # Savings goals
    try:
        from database.savings_goals import get_all_savings_goals
        goals = get_all_savings_goals()
        if goals:
            lines.append("\nSavings Goals:")
            for g in goals:
                name    = g.get("name", "Goal")
                target  = g.get("target_amount", 0)
                current = g.get("current_amount") or g.get("saved_amount") or 0
                pct     = (current / target * 100) if target else 0
                status  = "COMPLETED" if g.get("completed") else f"{pct:.1f}% done"
                lines.append(f"  - {name}: \u20b9{current:,.0f} of \u20b9{target:,.0f} ({status})")
    except Exception as e:
        lines.append(f"[Goals data unavailable: {e}]")

    return "\n".join(lines)


def generate_ai_financial_insights(force_refresh: bool = False) -> str:
    """
    Generate 3-4 bullet-point financial insights using live MongoDB data.
    Caches result in st.session_state under 'ai_insights_cache'.

    Args:
        force_refresh (bool): If True, ignore cached result and regenerate.

    Returns:
        str: Markdown-formatted insight text, or an error/fallback message.
    """
    import streamlit as st

    cache_key = "ai_insights_cache"
    if not force_refresh and cache_key in st.session_state:
        return st.session_state[cache_key]

    client = _get_client()
    if client is None:
        msg = (
            "⚠️ **GROQ_API_KEY not configured.**\n\n"
            "Add your Groq API key to your `.env` file or Streamlit secrets as `GROQ_API_KEY=...` "
            "to enable AI insights."
        )
        return msg

    context = _build_financial_context()
    user_prompt = (
        "Here is my current financial snapshot:\n\n"
        f"{context}\n\n"
        "Please provide 3-4 crisp, actionable bullet-point insights about my finances."
    )

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=600,
            temperature=0.65,
        )
        result = response.choices[0].message.content.strip()
        st.session_state[cache_key] = result
        return result
    except Exception as e:
        # Try fallback model
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ],
                max_tokens=600,
                temperature=0.65,
            )
            result = response.choices[0].message.content.strip()
            st.session_state[cache_key] = result
            return result
        except Exception as e2:
            return f"\u274c AI insights unavailable: {e2}"


def chat_with_finance_ai(user_question: str, chat_history: list) -> str:
    """
    Answer a user's financial question using live MongoDB context.

    Args:
        user_question (str)   : The user's chat message.
        chat_history  (list)  : List of {"role": ..., "content": ...} dicts.

    Returns:
        str: The AI assistant's response text.
    """
    client = _get_client()
    if client is None:
        return (
            "⚠️ AI Assistant is not available. "
            "Please add your `GROQ_API_KEY` to your `.env` file or Streamlit secrets."
        )

    context   = _build_financial_context()
    sys_msg   = _CHAT_SYSTEM_TEMPLATE.format(context=context)

    messages  = [{"role": "system", "content": sys_msg}]
    # Include up to last 10 turns of history for context
    for msg in chat_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_question})

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=messages,
            max_tokens=700,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                max_tokens=700,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e2:
            return f"\u274c Chat unavailable: {e2}"
