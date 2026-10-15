"""
FINTRACK - Database Query Optimization & Index Verification Script
Phase 7: MongoDB Query Optimization Proof via Execution Plan & Statistics

This script verifies that MongoDB B-Tree indexes are actively used
by the query planner, replacing unindexed full collection scans (COLLSCAN)
with high-performance index scans (IXSCAN / FETCH).
"""

import sys
import os
import json
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import database objects -- no monkey-patching required
from database.connection import transactions, db, check_connection
from pymongo import ASCENDING, DESCENDING


def find_stage_recursive(plan_stage, target_stage="IXSCAN"):
    """Recursively search for a specific stage (e.g., IXSCAN) in the execution plan tree."""
    if not isinstance(plan_stage, dict):
        return None
    if plan_stage.get("stage") == target_stage:
        return plan_stage
    # Search inputStage
    if "inputStage" in plan_stage:
        res = find_stage_recursive(plan_stage["inputStage"], target_stage)
        if res:
            return res
    # Search inputStages (array)
    if "inputStages" in plan_stage:
        for s in plan_stage["inputStages"]:
            res = find_stage_recursive(s, target_stage)
            if res:
                return res
    return None


def get_plan_hierarchy(stage_dict):
    """Return a string breadcrumb of stages: e.g. SORT -> FETCH -> IXSCAN"""
    if not isinstance(stage_dict, dict):
        return ""
    stage_name = stage_dict.get("stage", "UNKNOWN")
    if "inputStage" in stage_dict:
        sub = get_plan_hierarchy(stage_dict["inputStage"])
        return f"{stage_name} -> {sub}" if sub else stage_name
    elif "inputStages" in stage_dict and stage_dict["inputStages"]:
        subs = [get_plan_hierarchy(s) for s in stage_dict["inputStages"]]
        return "{} -> ({})".format(stage_name, ", ".join(subs))
    return stage_name


def run_optimization_verification():
    print("=" * 80)
    print("  FINTRACK | MONGODB QUERY OPTIMIZATION VERIFICATION REPORT (PHASE 7)")
    print("=" * 80)
    print("Timestamp: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    print("Database:  {}".format(db.name))
    print("Collection: {}".format(transactions.name))

    connected = check_connection()
    if not connected:
        print("\n[ERROR] Unable to connect to MongoDB Atlas. Please check network/credentials.")
        return

    # STEP 1: Ensure the required indexes exist
    print("\n" + "-" * 80)
    print("STEP 1: VERIFYING & ENSURING REQUIRED MONGODB INDEXES")
    print("-" * 80)

    idx_date = transactions.create_index([("date", DESCENDING)])
    print("  [+] Single-field index on [('date', -1)]:        {}".format(idx_date))

    idx_compound = transactions.create_index([("type", ASCENDING), ("category", ASCENDING)])
    print("  [+] Compound index on [('type', 1), ('category', 1)]: {}".format(idx_compound))

    existing_indexes = transactions.index_information()
    print("\n  Active Indexes on '{}' collection ({} total):".format(
        transactions.name, len(existing_indexes)))
    for name, info in existing_indexes.items():
        keys_repr = ", ".join("{}: {}".format(k, direction) for k, direction in info.get("key", []))
        print("    - {:<25} -> [{}]".format(name, keys_repr))

    # STEP 2: Run explain via db.command with verbosity="executionStats"
    #   PyMongo 4.x: Cursor.explain() accepts no verbosity argument.
    #   The native way to obtain executionStats is db.command("explain", ..., verbosity=...).
    #   No monkey-patching is needed or used here.
    print("\n" + "-" * 80)
    print("STEP 2: EXECUTING QUERY WITH db.command('explain', verbosity='executionStats')")
    print("-" * 80)
    target_query = {"type": "expense", "category": "Food"}
    print("  Target Query: {}, sort: date DESC".format(json.dumps(target_query)))

    explain_data = db.command(
        "explain",
        {
            "find":   transactions.name,
            "filter": target_query,
            "sort":   {"date": -1},
        },
        verbosity="executionStats",
    )

    # STEP 3: Parse execution stats
    print("\n" + "-" * 80)
    print("STEP 3: PARSING EXECUTION STATS & QUERY PLANNER METRICS")
    print("-" * 80)

    qp              = explain_data.get("queryPlanner", {})
    winning_plan    = qp.get("winningPlan", {})
    execution_stats = explain_data.get("executionStats", {})

    plan_hierarchy = get_plan_hierarchy(winning_plan)
    ixscan_stage   = find_stage_recursive(winning_plan, "IXSCAN")

    has_ixscan  = ixscan_stage is not None
    index_name  = ixscan_stage.get("indexName", "N/A") if ixscan_stage else "None (COLLSCAN)"
    key_pattern = ixscan_stage.get("keyPattern", {}) if ixscan_stage else {}

    # All values come directly from MongoDB executionStats output
    n_returned          = execution_stats.get("nReturned", 0)
    total_docs_examined = execution_stats.get("totalDocsExamined", 0)
    total_keys_examined = execution_stats.get("totalKeysExamined", 0)
    exec_time_ms        = execution_stats.get("executionTimeMillis", 0)
    total_docs_in_coll  = transactions.count_documents({})

    print("  * Winning Plan Stage Hierarchy:    {}".format(plan_hierarchy))
    print("  * Index Scan (IXSCAN) Detected:    {}".format("YES" if has_ixscan else "NO (COLLSCAN used)"))
    print("  * Index Used:                      {}".format(index_name))
    print("  * Index Key Pattern Applied:       {}".format(json.dumps(key_pattern)))
    print("  * Total Documents in Collection:   {}".format(total_docs_in_coll))
    print("  * totalDocsExamined:               {}".format(total_docs_examined))
    print("  * totalKeysExamined:               {}".format(total_keys_examined))
    print("  * nReturned:                       {}".format(n_returned))
    print("  * executionTimeMillis:             {} ms  (actual measured value)".format(exec_time_ms))

    efficiency_pct = (n_returned / total_docs_examined * 100) if total_docs_examined > 0 else 100.0

    print("\n  [ANALYSIS]")
    if has_ixscan and total_docs_examined < total_docs_in_coll:
        unscanned = total_docs_in_coll - total_docs_examined
        print("  -> SUCCESS: Only {} docs examined out of {} total.".format(
            total_docs_examined, total_docs_in_coll))
        print("  -> Bypassed {} irrelevant documents (no full collection scan).".format(unscanned))
        print("  -> Query selectivity: {:.1f}% ({} returned / {} examined).".format(
            efficiency_pct, n_returned, total_docs_examined))
    elif has_ixscan:
        print("  -> Index scan confirmed. {} docs examined, {} returned.".format(
            total_docs_examined, n_returned))
        print("  -> Query selectivity: {:.1f}%.".format(efficiency_pct))
    else:
        print("  -> WARNING: No index scan detected. {} docs examined (full scan).".format(
            total_docs_examined))
        print("     Verify the compound index exists and has not been dropped.")

    # STEP 4: Comparison table with actual measured values
    print("\n" + "=" * 80)
    print("STEP 4: PERFORMANCE COMPARISON -- MEASURED IXSCAN vs. COLLSCAN BASELINE")
    print("=" * 80)

    table_data = [
        ("Execution Strategy",       "Collection Scan (COLLSCAN)",
         "Index Scan (IXSCAN) -- measured"),
        ("Data Structure",           "Raw unordered document pages",
         "B-Tree balanced search tree"),
        ("Total Docs in Collection", str(total_docs_in_coll),
         str(total_docs_in_coll)),
        ("Docs Examined",            "{} (every doc)".format(total_docs_in_coll),
         "{} (index-filtered)".format(total_docs_examined)),
        ("Index Keys Examined",      "N/A",
         str(total_keys_examined)),
        ("Documents Returned",       str(n_returned),
         str(n_returned)),
        ("Execution Time (actual)",  "Not measured (baseline estimate)",
         "{} ms".format(exec_time_ms)),
    ]

    col1_w, col2_w, col3_w = 28, 38, 40

    print("\n+{}+{}+{}+".format("-" * col1_w, "-" * col2_w, "-" * col3_w))
    print("| {:<{}} | {:<{}} | {:<{}} |".format(
        "Metric", col1_w - 2,
        "Unindexed Scan (COLLSCAN)", col2_w - 2,
        "Indexed Scan (IXSCAN / FETCH)", col3_w - 2))
    print("+{}+{}+{}+".format("-" * col1_w, "-" * col2_w, "-" * col3_w))
    for metric, collscan_val, ixscan_val in table_data:
        print("| {:<{}} | {:<{}} | {:<{}} |".format(
            metric, col1_w - 2, collscan_val, col2_w - 2, ixscan_val, col3_w - 2))
    print("+{}+{}+{}+".format("-" * col1_w, "-" * col2_w, "-" * col3_w))

    print("\n" + "=" * 80)
    print("ARCHITECTURAL SUMMARY:")
    print("-" * 80)
    print("""
1. Index Verification:
   Compound index [('type', 1), ('category', 1)] checked.
   IXSCAN detected: {}  |  Index name: {}

2. Measured Execution Stats (executionStats verbosity via db.command):
   - nReturned:           {}
   - totalDocsExamined:   {}
   - totalKeysExamined:   {}
   - executionTimeMillis: {} ms

3. Stage Pipeline:
   Winning plan: {}
   - IXSCAN: Narrows candidates using the compound index key bounds.
   - FETCH:  Retrieves only the matching document bodies from storage.

4. Selectivity:
   {:.1f}% ({} returned / {} examined).
""".format(
        "YES" if has_ixscan else "NO", index_name,
        n_returned, total_docs_examined, total_keys_examined, exec_time_ms,
        plan_hierarchy,
        efficiency_pct, n_returned, total_docs_examined,
    ))
    print("=" * 80)
    print(">> Phase 7 Optimization Verification completed successfully.\n")


if __name__ == "__main__":
    run_optimization_verification()
