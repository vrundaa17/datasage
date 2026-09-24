import sys
import time
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.eda import eda_node

DELAY = 10  # seconds between tests — respect free tier rate limit

def make_state(df, domain="finance", overrides={}):
    state = {
        "raw_df": df,
        "cleaned_df": df,
        "column_names": list(df.columns),
        "data_types": {},
        "null_counts": {},
        "row_count": len(df),
        "column_count": len(df.columns),
        "sample_values": {},
        "data_domain": domain,
        "quality_score": 95.0,
        "issues_found": [],
        "cleaning_report": {"done": True},
        "analysis_results": {},
        "key_findings": [],
        "visualisations": [],
        "report": "",
        "next_agent": "",
        "instructions": "",
        "iteration_count": 2,
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

def assert_ok(condition, message):
    print(f"  {'✅ PASS' if condition else '❌ FAIL'} — {message}")

def section(title):
    print(f"\n{'-'*55}\n  {title}\n{'-'*55}")


# ─────────────────────────────────────────────
# Test 1 — Real CSV after cleaning
# ─────────────────────────────────────────────
section("TEST 1: Real CSV — finance domain")

df = pd.read_csv("tests/example.csv", encoding="utf-8-sig")
result = eda_node(make_state(df, domain="finance"))

print(f"  Status       : {result['status']}")
print(f"  Findings     : {len(result['key_findings'])}")
print(f"  Charts       : {len(result['visualisations'])}")
print(f"  Next agent   : {result['next_agent']}")
print(f"\n  Key findings:")
for f in result["key_findings"]:
    print(f"    - {f}")
print(f"\n  Chart specs:")
for c in result["visualisations"]:
    print(f"    - [{c.get('chart_type')}] {c.get('title')}")

assert_ok(result["status"] == "running", "status is running")
assert_ok(len(result["key_findings"]) > 0, "key findings generated")
assert_ok(len(result["visualisations"]) > 0, "chart specs generated")
assert_ok(bool(result["analysis_results"]), "analysis_results set in state")
assert_ok(result["next_agent"] == "supervisor", "routes back to supervisor")

time.sleep(DELAY)

# ─────────────────────────────────────────────
# Test 2 — Health domain
# ─────────────────────────────────────────────
section("TEST 2: Health domain data")

df_health = pd.DataFrame({
    "patient_id": range(1, 21),
    "age": [25,34,45,52,61,28,39,47,55,63,29,38,44,51,60,27,36,48,56,64],
    "blood_pressure": [120,130,140,135,150,118,128,138,142,155,122,132,136,140,152,116,126,134,144,158],
    "cholesterol": [180,220,240,210,260,175,215,235,205,255,185,225,230,200,250,170,210,228,208,248],
    "diagnosis": ["healthy","hypertension","diabetes","healthy","hypertension",
                  "healthy","healthy","diabetes","hypertension","diabetes",
                  "healthy","hypertension","healthy","healthy","diabetes",
                  "healthy","healthy","hypertension","diabetes","hypertension"],
    "readmitted": [0,1,0,0,1,0,0,1,1,1,0,0,0,0,1,0,0,1,1,0]
})

result = eda_node(make_state(df_health, domain="health"))

print(f"  Status       : {result['status']}")
print(f"  Findings     : {len(result['key_findings'])}")
print(f"  Charts       : {len(result['visualisations'])}")
print(f"\n  Key findings:")
for f in result["key_findings"]:
    print(f"    - {f}")

assert_ok(result["status"] == "running", "status is running")
assert_ok(len(result["key_findings"]) >= 3, "at least 3 findings")
assert_ok(result["analysis_results"].get("shape", {}).get("rows") == 20, "correct row count")

time.sleep(DELAY)

# ─────────────────────────────────────────────
# Test 3 — Only categorical columns
# ─────────────────────────────────────────────
section("TEST 3: Categorical-only dataset")

df_cat = pd.DataFrame({
    "region":   ["North","South","East","West","North","South"],
    "product":  ["A","B","A","C","B","C"],
    "outcome":  ["win","loss","win","win","loss","win"],
})

result = eda_node(make_state(df_cat, domain="sales"))

print(f"  Status       : {result['status']}")
print(f"  Findings     : {len(result['key_findings'])}")

assert_ok(result["status"] == "running", "handles categorical-only without crash")
assert_ok(result["analysis_results"]["numeric_columns"] == [], "no numeric columns detected")

time.sleep(DELAY)

# ─────────────────────────────────────────────
# Test 4 — cleaned_df missing, falls back to raw_df
# ─────────────────────────────────────────────
section("TEST 4: No cleaned_df — fallback to raw_df")

df_raw = pd.DataFrame({
    "sales": [100, 200, 300, 400, 500],
    "cost":  [50, 80, 120, 160, 200],
    "profit":[50, 120, 180, 240, 300]
})

result = eda_node(make_state(df_raw, overrides={"cleaned_df": None}))

print(f"  Status       : {result['status']}")
assert_ok(result["status"] == "running", "falls back to raw_df without crash")


print("  ALL EDA TESTS DONE")
print(f"{'-'*55}\n")