import pandas as pd
import numpy as np
import re
import sys
from pathlib import Path
import time
DELAY_BETWEEN_TESTS = 8 

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.cleaner import clean_node
from agents.graph import create_graph

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_base_state(df: pd.DataFrame, overrides: dict = {}) -> dict:
    """Build a minimal valid state with a given dataframe."""
    state = {
        "raw_df": df,
        "cleaned_df": None,
        "column_names": list(df.columns),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": {col: int(df[col].isnull().sum()) for col in df.columns},
        "row_count": len(df),
        "column_count": len(df.columns),
        "sample_values": df.head(3).to_dict(),
        "data_domain": "finance",
        "quality_score": 74.16,
        "issues_found": [],
        "cleaning_report": {},
        "analysis_results": {},
        "key_findings": [],
        "visualizations": [],
        "report": "",
        "next_agent": "",
        "instructions": "",
        "iteration_count": 1,
        "conversation_history": [],
        "current_question": "",
        "question_type": "",
        "followup_answer": "",
        "user_id": "test-user",
        "upload_id": "test-upload",
        "error": None,
        "status": "running"
    }
    state.update(overrides)
    return state


def print_section(title: str):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")


def print_result(result: dict):
    report = result.get("cleaning_report", {})
    print(f"  Status         : {result['status']}")
    print(f"  Error          : {result.get('error')}")
    print(f"  Shape change   : {report.get('initial_shape')} → {report.get('final_shape')}")
    print(f"  New quality    : {report.get('new_quality_score')}%")
    print(f"  Cleaned cols   : {list(result['cleaned_df'].columns) if result.get('cleaned_df') is not None else 'None'}")
    print(f"  Next agent     : {result['next_agent']}")
    print(f"\n  LLM reasoning  : {report.get('llm_reasoning', '')}")
    print(f"\n  Actions taken  :")
    for action in report.get("actions_taken", []):
        print(f"    - {action}")


def assert_ok(condition: bool, message: str):
    status = "✅ PASS" if condition else "❌ FAIL"
    print(f"  {status} — {message}")


# ─────────────────────────────────────────────
# Test 1 — Real CSV (your actual dataset)
# ─────────────────────────────────────────────
print_section("TEST 1: Real CSV (example.csv)")

df_real = pd.read_csv("tests/example.csv", encoding="utf-8-sig")
state = make_base_state(df_real, {
    "data_domain": "finance",
    "quality_score": 74.16,
    "issues_found": [
        "Current ₹ has 31.6% nulls",
        "Predicted ₹ has 31.6% nulls",
        "Actual ₹ has 94.7% missing values",
        "Human has 63.2% missing values"
    ]
})

result = clean_node(state)
print_result(result)

assert_ok(result["status"] == "running", "status is running")
assert_ok(result.get("cleaned_df") is not None, "cleaned_df is set")
assert_ok(bool(result.get("cleaning_report")), "cleaning_report is not empty")
assert_ok(result["next_agent"] == "supervisor", "routes back to supervisor")
assert_ok(result["cleaning_report"].get("new_quality_score", 0) > 74.16, "quality improved after cleaning")

time.sleep(DELAY_BETWEEN_TESTS)

print_section("TEST 2: Already clean data — no action needed")

df_clean = pd.DataFrame({
    "product": ["A", "B", "C", "D"],
    "revenue": [1000.0, 2000.0, 1500.0, 3000.0],
    "units_sold": [10, 20, 15, 30],
    "region": ["North", "South", "East", "West"]
})

state = make_base_state(df_clean, {
    "data_domain": "sales",
    "quality_score": 100.0,
    "issues_found": []
})

result = clean_node(state)
print_result(result)

assert_ok(result["status"] == "running", "status is running")
assert_ok(result["cleaning_report"].get("new_quality_score") == 100.0, "quality stays at 100%")
assert_ok(len(result["cleaned_df"]) == 4, "no rows lost")

time.sleep(DELAY_BETWEEN_TESTS)

print_section("TEST 3: Special characters in column names")

df_special = pd.DataFrame({
    "Sale Price ($)": [100.0, 200.0, 300.0],
    "Tax %": [10.0, 15.0, 12.0],
    "Customer Name ": ["Alice", "Bob", "Charlie"],   # trailing space
    "₹ Revenue": [8000.0, 16000.0, 24000.0]
})

state = make_base_state(df_special, {
    "data_domain": "sales",
    "quality_score": 100.0,
    "issues_found": []
})

result = clean_node(state)
print_result(result)

cleaned_cols = list(result["cleaned_df"].columns) if result.get("cleaned_df") is not None else []
assert_ok(result["status"] == "running", "status is running")
assert_ok(
    all(re.match(r'^[a-z0-9_]+$', col) for col in cleaned_cols) if cleaned_cols else False,
    f"all column names are clean alphanumeric/underscore: {cleaned_cols}"
)
time.sleep(DELAY_BETWEEN_TESTS)

print_section("TEST 4: Duplicate rows")

df_dupes = pd.DataFrame({
    "name": ["Alice", "Bob", "Alice", "Charlie", "Bob"],
    "score": [90, 85, 90, 78, 85]
})

state = make_base_state(df_dupes, {
    "data_domain": "customer",
    "quality_score": 100.0,
    "issues_found": ["2 duplicate rows found"]
})

result = clean_node(state)
print_result(result)

assert_ok(result["status"] == "running", "status is running")
assert_ok(
    result["cleaning_report"]["final_shape"][0] < 5,
    f"duplicate rows removed (rows: {result['cleaning_report']['final_shape'][0]})"
)

time.sleep(DELAY_BETWEEN_TESTS)

print_section("TEST 5: Column with >80% nulls — expect drop")

df_high_null = pd.DataFrame({
    "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "value": [10.0, 20.0, None, 40.0, None, 60.0, None, 80.0, None, 100.0],
    "nearly_empty": [None, None, None, None, None, None, None, None, None, 1.0],   # 90% null
    "category": ["A", "B", "A", None, "B", "A", None, "B", "A", "B"]
})

state = make_base_state(df_high_null, {
    "data_domain": "unknown",
    "quality_score": 60.0,
    "issues_found": ["nearly_empty has 90.0% missing values"]
})

result = clean_node(state)
print_result(result)

assert_ok(result["status"] == "running", "status is running")
assert_ok(
    "nearly_empty" not in list(result["cleaned_df"].columns),
    "nearly_empty column dropped (90% nulls)"
)


time.sleep(DELAY_BETWEEN_TESTS)
print_section("TEST 6: Numeric values stored as strings — expect cast")

df_strings = pd.DataFrame({
    "product": ["A", "B", "C"],
    "price": ["100.5", "200.0", "150.75"],    # numeric stored as string
    "quantity": ["10", "20", "15"],             # numeric stored as string
    "label": ["cheap", "expensive", "mid"]
})

state = make_base_state(df_strings, {
    "data_domain": "inventory",
    "quality_score": 100.0,
    "issues_found": []
})

result = clean_node(state)
print_result(result)

assert_ok(result["status"] == "running", "status is running")
if result.get("cleaned_df") is not None:
    price_dtype = str(result["cleaned_df"]["price"].dtype) if "price" in result["cleaned_df"].columns else "missing"
    assert_ok(
        "float" in price_dtype or "int" in price_dtype,
        f"price column cast to numeric (dtype: {price_dtype})"
    )

time.sleep(DELAY_BETWEEN_TESTS)

print_section("TEST 7: Health domain data")

df_health = pd.DataFrame({
    "patient_id": [1, 2, 3, 4, 5],
    "age": [25, None, 45, 30, None],
    "blood_pressure": [120, 130, None, 115, 125],
    "diagnosis": ["flu", "cold", None, "flu", "cold"],
    "visit_date": ["2024-01-01", "2024-01-02", "2024-01-03", None, "2024-01-05"]
})

state = make_base_state(df_health, {
    "data_domain": "health",
    "quality_score": 76.0,
    "issues_found": [
        "age has 40.0% nulls",
        "blood_pressure has 20.0% nulls",
        "diagnosis has 20.0% nulls",
        "visit_date has 20.0% nulls"
    ]
})

result = clean_node(state)
print_result(result)

assert_ok(result["status"] == "running", "status is running")
assert_ok(result["cleaning_report"].get("new_quality_score", 0) >= 76.0, "quality same or improved")


time.sleep(DELAY_BETWEEN_TESTS)
print_section("TEST 8: Empty dataframe — edge case")

df_empty = pd.DataFrame(columns=["col_a", "col_b", "col_c"])

state = make_base_state(df_empty, {
    "data_domain": "unknown",
    "quality_score": 100.0,
    "issues_found": []
})

result = clean_node(state)
print_result(result)

assert_ok(result["status"] in ["running", "failed"], "handles empty df without crash")


time.sleep(DELAY_BETWEEN_TESTS)
time.sleep(DELAY_BETWEEN_TESTS)
print_section("TEST 9: Full pipeline — Inspector + Cleaner via graph")


df_real = pd.read_csv("tests/example.csv", encoding="utf-8-sig")

initial_state = make_base_state(df_real, {
    "column_names": [],
    "data_types": {},
    "null_counts": {},
    "row_count": 0,
    "column_count": 0,
    "sample_values": {},
    "data_domain": "",
    "quality_score": 0.0,
    "issues_found": [],
    "cleaning_report": {},
    "iteration_count": 0,
})

graph = create_graph()
result = graph.invoke(initial_state)

print(f"  Domain         : {result['data_domain']}")
print(f"  Quality before : 74.16%")
print(f"  Quality after  : {result['quality_score']}%")
print(f"  Cleaned cols   : {list(result['cleaned_df'].columns) if result.get('cleaned_df') is not None else 'None'}")
print(f"  Cleaning done  : {bool(result.get('cleaning_report'))}")
print(f"  Next agent     : {result['next_agent']}")

assert_ok(bool(result.get("data_domain")), "Inspector set domain")
assert_ok(bool(result.get("cleaning_report")), "Cleaner ran and set cleaning_report")
assert_ok(result.get("cleaned_df") is not None, "cleaned_df exists in final state")
assert_ok(result["status"] != "failed", "pipeline did not fail")


# ─────────────────────────────────────────────
print("\n" + "="*55)
print("  ALL TESTS DONE")
print("="*55 + "\n")