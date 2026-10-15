# 🌱 FINTRACK — Personal Finance & Spending Analytics Platform

> **Track Today, Build Tomorrow.**

FINTRACK is a full-stack personal finance dashboard built with **Streamlit** and **MongoDB Atlas**. It solves the everyday problem of unorganized, fragmented personal expense tracking by consolidating income, expenses, savings goals, and budget limits into a single, real-time green-themed web interface — backed by a production-grade NoSQL database with verified B-Tree index optimization.

**Who should use it?**
Students, freelancers, and individuals who want a self-hosted, data-driven alternative to generic budgeting spreadsheets — with live MongoDB persistence, dynamic KPI analytics, and an AI spending advisor powered by Llama 3.3.

---

## 2. Features

| Feature | Description |
|---|---|
| **📊 Dashboard & KPIs** | Live Total Income, Expenses, Savings, and Active Goals cards with **dynamic month-over-month % deltas** computed from actual transaction history (shows `vs. last month: N/A` when prior-month data is absent) |
| **📋 Transaction Management** | Full CRUD — add, filter (by date range / category / type / keyword), paginate, update amount, delete, and **export to CSV** |
| **🕒 Budget Tracking** | Set per-category monthly limits; progress bars calculated as `(spent / limit) × 100` from live MongoDB aggregation; colour-coded status (green / amber / red) |
| **🎯 Savings Goals** | Create, fund, and track completion of named savings goals with target dates and progress bars |
| **📈 Spending Analytics** | Monthly income/expense/savings line charts, category donut charts, and top-spending bar charts — all driven by MongoDB aggregation pipelines |
| **🔍 Query Optimization** | Compound B-Tree index `[('type', 1), ('category', 1)]` + single-field index `[('date', -1)]` verified via `db.command("explain", ..., verbosity="executionStats")` — `IXSCAN` confirmed, 100 % selectivity |
| **🤖 AI Assistant** | Groq-powered Llama 3.3 financial insights and interactive chat, seeded with live MongoDB transaction data |

---

## 3. Demo & Screenshots

| Dashboard | MongoDB Atlas | Optimization Test |
|---|---|---|
| ![Dashboard](<img width="1917" height="930" alt="01_dashboard_overview" src="https://github.com/user-attachments/assets/f3409a26-d21c-4290-85fd-acca3e03e663" />
) | ![MongoDB Atlas](<img width="1917" height="928" alt="05_atlas_collections" src="https://github.com/user-attachments/assets/246b3d29-98b2-458e-8dae-dd2782b1da21" />
) | ![Optimization Test](<img width="1917" height="1047" alt="06_index_optimization" src="https://github.com/user-attachments/assets/8c5f6664-66a9-4504-b7ac-74a578d9e056" />
) |

> 📁 Place your screenshots in `docs/images/` to render them above.

---

## 4. Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| **Frontend** | [Streamlit](https://streamlit.io) | Single-page app with radio-button navigation, custom CSS, Plotly charts |
| **Application Logic** | Python 3.10+ | Validation, business logic, session state, caching (`@st.cache_data`) |
| **Database** | [MongoDB Atlas](https://www.mongodb.com/atlas) | Cloud-hosted NoSQL — database `fintrack_db`, collections: `transactions`, `budgets`, `savings_goals` |
| **Database Driver** | [PyMongo](https://pymongo.readthedocs.io) (`pymongo` ≥ 4.x) | Synchronous `MongoClient`; no async layer |
| **Data Processing** | Pandas | DataFrame aggregation for charts and CSV export |
| **Visualization** | Plotly (`plotly.graph_objects`) | Interactive bar, pie/donut, scatter/line charts |
| **AI Integration** | [Groq SDK](https://groq.com) | Llama 3.3 70B for financial insights and chat |
| **Configuration** | `python-dotenv` | Loads `MONGO_URI` from `.env`; Streamlit `st.secrets` fallback for cloud |

---

## 5. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Browser                                │
│                    http://localhost:8501                             │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  HTTP (Streamlit protocol)
┌───────────────────────────────▼─────────────────────────────────────┐
│              Streamlit Frontend  (app.py)                           │
│                                                                     │
│  ┌──────────┐ ┌────────────┐ ┌────────┐ ┌────────┐ ┌───────────┐  │
│  │Dashboard │ │Transactions│ │Budgets │ │ Goals  │ │ Analytics │  │
│  └──────────┘ └────────────┘ └────────┘ └────────┘ └───────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │          Python Application & Validation Layer               │  │
│  │  compute_month_delta()  ·  fmt_inr()  ·  Input Validation   │  │
│  └─────────────────────────────┬────────────────────────────────┘  │
└────────────────────────────────│────────────────────────────────────┘
                                 │  Synchronous PyMongo calls
┌────────────────────────────────▼────────────────────────────────────┐
│              database/  (Python modules)                            │
│                                                                     │
│  connection.py   transactions.py   budgets.py   savings_goals.py   │
│  analytics.py    ai/insights.py                                     │
│                                                                     │
│  MongoClient  ·  insert_one  ·  find().sort()  ·  update_one       │
│  delete_one   ·  aggregate()  ·  db.command("explain", ...)        │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │  MongoDB Wire Protocol (TLS)
┌─────────────────────────────────▼───────────────────────────────────┐
│              MongoDB Atlas  —  fintrack_db                          │
│                                                                     │
│   Collection: transactions   ·  Indexes: date_-1, type_1_cat_1     │
│   Collection: budgets                                               │
│   Collection: savings_goals                                         │
└─────────────────────────────────────────────────────────────────────┘
```

**Data flow:** Every user interaction (add transaction, update budget, etc.) triggers a synchronous PyMongo operation in the appropriate `database/` module. `@st.cache_data(ttl=30)` caches read results for 30 seconds; mutating operations call `load_txns.clear()` to invalidate the cache and force a fresh read before the next `st.rerun()`.

---

## 6. Requirements

| Requirement | Details |
|---|---|
| **Python** | 3.10 or higher |
| **MongoDB Atlas** | Free M0 cluster or higher; database named `fintrack_db` |
| **Atlas Network Access** | Your machine's public IP whitelisted (or `0.0.0.0/0` for development) |
| **Git** | For cloning and version control |

---

## 7. Setup

### Step 1 — Clone the repository

```bash
git clone https://github.com/lokhnadhgembali/FINTRACK.git
cd FINTRACK
```

### Step 2 — Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` installs: `streamlit`, `pymongo`, `dnspython`, `pandas`, `plotly`, `groq`, `python-dotenv`.

### Step 4 — Configure environment variables

Create a `.env` file in the project root:

```dotenv
MONGO_URI="mongodb+srv://<username>:<password>@<cluster-host>/fintrack_db?retryWrites=true&w=majority"
```

> ⚠️ **Never commit `.env` to version control.** It is already listed in `.gitignore`.

### Step 5 — Run the application

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser. On first launch, click **🌱 Load Sample Data** on the Dashboard to seed six months of realistic transactions.

---

## 8. Usage

| Step | Action |
|---|---|
| **1. View KPIs** | Open the **Dashboard** to see live Total Income, Expenses, Savings, and Active Goals. Dynamic `▲/▼ X.X% vs. last month` badges are calculated from actual transaction records; `vs. last month: N/A` is shown when prior-month history is insufficient |
| **2. Add a transaction** | Go to **📋 Transactions → ➕ Add New Transaction**. Fill in Title, Amount, Type (`income`/`expense`), Category, Date, and optional Notes. Data is validated before `insert_one` persists it to MongoDB |
| **3. Filter & export** | Use the filter bar (date range, category, type, keyword search) and click **📥 CSV** to download matching records |
| **4. Set budgets** | Go to **🕒 Budgets → ➕ Set / Update a Budget Limit**. Budget progress bars reflect `(current_month_spend / limit) × 100` from a live MongoDB aggregation pipeline |
| **5. Track goals** | Go to **🎯 Goals → ➕ Create New Savings Goal**. Add funds incrementally and track the progress bar toward your target amount |
| **6. View analytics** | Go to **📊 Analytics** for monthly income/expense/savings trends, category breakdowns, and comparative bar charts |
| **7. AI insights** | Go to **🤖 AI Assistant** or click **✨ Generate New Insights** on the Dashboard for Llama 3.3-powered spending analysis |

---

## 9. Project Structure

```
FINTRACK/
│
├── app.py                   # Main Streamlit application — all pages & navigation
│
├── database/                # PyMongo data layer
│   ├── __init__.py
│   ├── connection.py        # MongoClient setup, index creation, check_connection()
│   ├── transactions.py      # add_transaction, get_transactions, update_transaction,
│   │                        #   delete_transaction, add_goal, get_goals,
│   │                        #   seed_sample_data_if_empty
│   ├── budgets.py           # set_or_update_budget, get_all_budgets, delete_budget
│   ├── savings_goals.py     # add_savings_goal, get_all_savings_goals,
│   │                        #   update_goal_progress, delete_savings_goal
│   └── analytics.py         # get_category_expense_breakdown,
│                            #   get_monthly_income_expense_summary,
│                            #   get_total_spent_by_category_for_month
│
├── ai/                      # AI integration
│   ├── __init__.py
│   └── insights.py          # generate_ai_financial_insights, chat_with_finance_ai
│
├── .streamlit/
│   └── config.toml          # Streamlit theme & server configuration
│
├── test_connection.py       # Verifies MongoDB Atlas ping and collection listing
├── test_crud.py             # Automated create → read → update → delete test cycle
├── test_optimization.py     # Index verification via db.command("explain", ...,
│                            #   verbosity="executionStats") — Phase 7
│
├── .env                     # ⚠️ Secret — NOT committed (in .gitignore)
├── .gitignore               # Excludes .env, .venv/, __pycache__/, etc.
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## 10. Database Schema & PyMongo Operations

### Collections in `fintrack_db`

| Collection | Key Fields | Purpose |
|---|---|---|
| `transactions` | `_id` (ObjectId), `title` (str), `amount` (float), `type` ("income"\|"expense"), `category` (str), `date` (datetime, UTC), `notes` (str), `created_at` (datetime) | Core financial records; primary target of all CRUD and aggregation operations |
| `budgets` | `_id` (ObjectId), `category` (str, unique), `monthly_limit` (float), `updated_at` (datetime) | Per-category monthly spending ceilings set by the user |
| `savings_goals` | `_id` (ObjectId), `name` (str), `target_amount` (float), `current_amount` (float), `target_date` (datetime\|None), `completed` (bool), `created_at` (datetime) | Named savings targets tracked by the user |

### Core PyMongo Methods Implemented

| PyMongo Operation | Module / Function | Purpose |
|---|---|---|
| `client.admin.command("ping")` | `database/connection.py` → `check_connection()` | Verifies Atlas reachability on startup |
| `collection.create_index(...)` | `database/connection.py` → `check_connection()` | Creates `date_-1` and `type_1_category_1` indexes on first connect |
| `collection.insert_one(doc)` | `database/transactions.py` → `add_transaction()` | Persists a validated transaction document |
| `collection.find(filter).sort(key, dir)` | `database/transactions.py` → `get_transactions()` | Retrieves all transactions sorted by date descending |
| `collection.update_one(filter, update)` | `database/transactions.py` → `update_transaction()` | Updates the amount field of a single transaction by `_id` |
| `collection.delete_one(filter)` | `database/transactions.py` → `delete_transaction()` | Removes a single transaction by `_id` |
| `collection.aggregate(pipeline)` | `database/analytics.py` → `get_total_spent_by_category_for_month()` | `$match` + `$group` pipeline to sum category spend for a calendar month |
| `db.command("explain", cmd, verbosity="executionStats")` | `test_optimization.py` → `run_optimization_verification()` | Returns full execution plan with `nReturned`, `totalDocsExamined`, `totalKeysExamined`, `executionTimeMillis` |

---

## 11. Key Engineering Concepts

- **Direct Synchronous PyMongo Persistence** — The application uses a plain synchronous `MongoClient` (no async/Beanie/Motor). Every user action triggers an immediate, blocking database call; `@st.cache_data(ttl=30)` provides read-layer caching, invalidated explicitly after every mutation via `load_txns.clear()`.

- **B-Tree Indexing & Selectivity** — Two indexes are created on `transactions` at startup:
  - `date_-1` — single-field descending index; accelerates chronological queries and the spending trend chart.
  - `type_1_category_1` — compound index; used by budget aggregations and the Phase 7 optimization query.  
  Verified result: **IXSCAN** confirmed, **100 % selectivity** (22 documents returned / 22 examined out of 93 total in the collection), with `FETCH → SORT` upstream stages.

- **Strict Input & BSON Validation** — `add_transaction()` in `database/transactions.py` enforces non-empty title, positive amount, valid type/category enum, and converts `date` input to a timezone-aware `datetime` object before `insert_one`, ensuring all stored dates are BSON-compatible UTC timestamps.

- **Dynamic KPI Month-over-Month Computation** — `compute_month_delta(txns, txn_type)` in `app.py` iterates cached transaction records, computes totals for the current and previous calendar months, and returns `(delta_pct, direction)`. When `prev_val == 0` (no prior-month data), it returns `(None, "")` and `render_delta_badge()` displays `"vs. last month: N/A"` in grey — preventing fabricated percentage claims.

- **Secret Isolation via `.gitignore`** — `MONGO_URI` is stored exclusively in `.env` (loaded by `python-dotenv`) and `.streamlit/secrets.toml` (for cloud). Both paths are listed in `.gitignore`. The `_get_secret()` helper in `database/connection.py` tries `os.getenv` first, then `st.secrets`, with no hardcoded fallback.

---

## 12. Testing

Three standalone test scripts validate the full stack against the live Atlas cluster. Run them from the project root after activating `.venv`.

### `python test_connection.py`

Verifies that `MongoClient` can reach Atlas and lists the collections.

```
FINTRACK MongoDB connection successful!
Database name: fintrack_db
Ping result: {'ok': 1.0}
Collections: ['transactions', 'budgets', 'savings_goals']
```

### `python test_crud.py`

Inserts a test transaction, reads it back, updates the amount, asserts the value, then deletes it as cleanup.

```
CREATE passed: 6849f3a2c4e1b7d0e8f12345
READ passed: 94 record(s) found
UPDATE operation completed: 1
UPDATE verification passed
Test cleanup completed: 1 record(s) deleted
CRUD test finished.
```

### `python test_optimization.py`

Runs `db.command("explain", ..., verbosity="executionStats")` — **no monkey-patching** — on the query `{"type": "expense", "category": "Food"}` sorted by `date DESC`. Reports all raw metrics.

```
STEP 2: EXECUTING QUERY WITH db.command('explain', verbosity='executionStats')
  Target Query: {"type": "expense", "category": "Food"}, sort: date DESC

STEP 3: PARSING EXECUTION STATS & QUERY PLANNER METRICS
  * Winning Plan Stage Hierarchy:    SORT -> FETCH -> IXSCAN
  * Index Scan (IXSCAN) Detected:    YES
  * Index Used:                      type_1_category_1
  * Index Key Pattern Applied:       {"type": 1, "category": 1}
  * Total Documents in Collection:   93
  * totalDocsExamined:               22
  * totalKeysExamined:               22
  * nReturned:                       22
  * executionTimeMillis:             2 ms  (actual measured value)

  [ANALYSIS]
  -> SUCCESS: Only 22 docs examined out of 93 total.
  -> Bypassed 71 irrelevant documents (no full collection scan).
  -> Query selectivity: 100.0% (22 returned / 22 examined).
```

> All stats are **actual measured values** from MongoDB Atlas — no fabricated or theoretical figures.

---

## 13. Deployment

### Streamlit Community Cloud

1. Push your repository to GitHub (ensure `.env` and `.streamlit/secrets.toml` are in `.gitignore`).
2. Log in to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Point it to `app.py` in the `main` branch.
4. In **Advanced settings → Secrets**, add:

```toml
MONGO_URI = "mongodb+srv://<username>:<password>@<cluster-host>/fintrack_db?retryWrites=true&w=majority"
```

5. **Atlas Network Access:** Add `0.0.0.0/0` (allow from anywhere) under your Atlas cluster's **Network Access** tab, since Streamlit Cloud uses dynamic IPs.

6. Click **Deploy** — the `_get_secret()` helper in `database/connection.py` will automatically read `MONGO_URI` from `st.secrets` when running in the cloud environment.

---

## 14. Known Limitations

| Limitation | Detail |
|---|---|
| **Single-tenant scope** | FINTRACK is designed for a single user per deployment. There is no authentication layer; all visitors to the URL share the same database view. |
| **Month-over-month delta requires history** | The `compute_month_delta()` function needs at least **two consecutive calendar months** of transactions to compute a numeric percentage change. For the current month with no prior-month data, all KPI delta badges display `vs. last month: N/A` in grey. |

---

## 15. Future Improvements

| Improvement | Description |
|---|---|
| **Multi-user authentication** | Per-user accounts with `bcrypt`-hashed passwords, session tokens, and user-scoped MongoDB queries |
| **Google Gemini AI Financial Advisor** | Replace or supplement Groq/Llama 3.3 with Gemini 1.5 Pro for richer, multimodal spending analysis |
| **Automated recurring transactions** | Define recurring income/expense rules (e.g., "Rent on 1st of each month") that auto-insert via a scheduled background task |
| **Receipt OCR scanning** | Upload photos of receipts; use a vision model to extract merchant, amount, and date and pre-fill the Add Transaction form |

---

## 16. License & Contact

**License:** MIT — Free for academic, educational, and personal use. See [LICENSE](LICENSE) for full terms.

| | |
|---|---|
| **GitHub** | [github.com/lokhnadhgembali](https://github.com/lokhnadhgembali) |
| **Repository** | [github.com/lokhnadhgembali/FINTRACK](https://github.com/lokhnadhgembali/FINTRACK) |
| **Email** | *(add your contact email here)* |

---

<p align="center">
  Made with 💚 using Streamlit · MongoDB Atlas · PyMongo · Plotly · Groq / Llama 3.3
</p>
