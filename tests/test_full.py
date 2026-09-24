import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.graph import create_graph

# ─────────────────────────────────────────
def section(title):
    print(f"\n{'-'*65}")
    print(f"  {title}")
    print(f"{'-'*65}")

def check(condition, message):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {message}")
    return condition

# ─────────────────────────────────────────
# 1. LOAD CSV
# ─────────────────────────────────────────
section("LOAD CSV")

csv_path = Path(__file__).parent / "example.csv"
df = pd.read_csv(csv_path, encoding="utf-8-sig")

print(f"  File    : {csv_path.name}")
print(f"  Rows    : {len(df)}")
print(f"  Columns : {list(df.columns)}")

check(len(df) > 0, "CSV loaded with rows")
check(len(df.columns) > 0, "CSV has columns")

# ─────────────────────────────────────────
# 2. BUILD INITIAL STATE
# ─────────────────────────────────────────
section("INITIAL STATE")

initial_state = {
    "raw_df":               df,
    "cleaned_df":           None,
    "column_names":         [],
    "data_types":           {},
    "null_counts":          {},
    "row_count":            0,
    "column_count":         0,
    "sample_values":        {},
    "quality_score":        0.0,
    "issues_found":         [],
    "data_domain":          "",
    "cleaning_report":      {},
    "analysis_results":     {},
    "key_findings":         [],
    "visualisations":       [],
    "report":               "",
    "conversation_history": [],
    "current_question":     "",
    "question_type":        "",
    "followup_answer":      "",
    "next_agent":           "",
    "instructions":         "",
    "iteration_count":      0,
    "user_id":              "test-user",
    "upload_id":            "test-upload",
    "error":                None,
    "status":               "running",
}

check(initial_state["raw_df"] is not None, "raw_df set")
check(initial_state["report"] == "",       "report starts empty")
print("  Initial state ready")

# ─────────────────────────────────────────
# 3. CREATE GRAPH
# ─────────────────────────────────────────
section("CREATE GRAPH")

graph = create_graph()
check(graph is not None, "Graph compiled")

# ─────────────────────────────────────────
# 4. RUN FULL PIPELINE
# ─────────────────────────────────────────


try:
    result = graph.invoke(initial_state)
    pipeline_error = None
except Exception as e:
    result = None
    pipeline_error = e

check(pipeline_error is None, "Pipeline ran without Python exception")

if pipeline_error:
    print(f"\n  ERROR: {pipeline_error}")
    raise pipeline_error

# ─────────────────────────────────────────
# 5. INSPECTOR CHECKS
# ─────────────────────────────────────────
section("INSPECTOR CHECKS")

check(bool(result.get("data_domain")),          "Domain detected")
check(result.get("row_count", 0) > 0,           "row_count populated")
check(result.get("column_count", 0) > 0,        "column_count populated")
check(bool(result.get("column_names")),          "column_names populated")
check(bool(result.get("data_types")),            "data_types populated")
check(result.get("quality_score") is not None,  "quality_score calculated")

print(f"\n  Domain   : {result.get('data_domain')}")
print(f"  Quality  : {result.get('quality_score')}%")
print(f"  Issues   : {result.get('issues_found')}")

# ─────────────────────────────────────────
# 6. CLEANER CHECKS
# ─────────────────────────────────────────
section("CLEANER CHECKS")

cleaned_df     = result.get("cleaned_df")
cleaning_report = result.get("cleaning_report", {})

check(cleaned_df is not None,           "cleaned_df created")
check(len(cleaned_df) > 0,              "cleaned_df has rows")
check(bool(cleaning_report),            "cleaning_report created")
check("actions_taken" in cleaning_report, "cleaning_report has actions")
check("new_quality_score" in cleaning_report, "cleaning_report has quality score")

print(f"\n  Initial shape : {cleaning_report.get('initial_shape')}")
print(f"  Final shape   : {cleaning_report.get('final_shape')}")
print(f"  New quality   : {cleaning_report.get('new_quality_score')}%")
print(f"  Actions taken : {len(cleaning_report.get('actions_taken', []))}")
for action in cleaning_report.get("actions_taken", []):
    print(f"    - {action}")

# ─────────────────────────────────────────
# 7. EDA CHECKS
# ─────────────────────────────────────────
section("EDA CHECKS")

analysis = result.get("analysis_results", {})

check(bool(analysis),                               "analysis_results created")
check("shape" in analysis,                          "analysis has shape")
check("numeric_columns" in analysis,                "analysis has numeric_columns")
check("categorical_columns" in analysis,            "analysis has categorical_columns")
check(len(result.get("key_findings", [])) >= 3,    "at least 3 key findings")
check(len(result.get("visualisations", [])) > 0,   "at least 1 chart spec")

print(f"\n  Shape      : {analysis.get('shape')}")
print(f"  Numeric    : {analysis.get('numeric_columns')}")
print(f"  Categoric  : {analysis.get('categorical_columns')}")
print(f"\n  Key Findings:")
for i, f in enumerate(result.get("key_findings", []), 1):
    print(f"    {i}. {f}")

print(f"\n  Chart Specs:")
for i, c in enumerate(result.get("visualisations", []), 1):
    print(f"    {i}. [{c.get('chart_type','?').upper()}] {c.get('title','?')}")

# ─────────────────────────────────────────
# 8. REPORTER CHECKS — FULL REPORT
# ─────────────────────────────────────────
section("REPORTER CHECKS ")

report = result.get("report", "")

check(bool(report),                   "report is not empty")
check(len(report) > 200,              "report has substantial content")
check("##" in report,                 "report has markdown sections")
check(result.get("status") == "completed", "status is completed")
check(result.get("error") is None,    "no error in state")

print(f"\n  Report length : {len(report)} chars")
print(f"\n--- REPORT PREVIEW (first 600 chars) ---")
print(report[:600])
print("...")

# ─────────────────────────────────────────
# 9. Q&A ROUND 1
# ─────────────────────────────────────────
section("Q&A")

qa_state_1 = {
    **result,
    "current_question": "What is the average price of houses in this dataset?",
    "question_type":    "followup",
    "followup_answer":  "",
    "iteration_count":  0,
}

try:
    qa_result_1 = graph.invoke(qa_state_1)
    qa_error_1 = None
except Exception as e:
    qa_result_1 = None
    qa_error_1 = e

check(qa_error_1 is None,                          "Q&A round 1 ran without exception")
check(bool(qa_result_1.get("followup_answer")),    "Q&A round 1 produced an answer")
check(qa_result_1.get("current_question") == "",   "current_question cleared after answer")
check(len(qa_result_1.get("conversation_history", [])) == 2, "conversation history has 2 entries")

print(f"\n  Answer 1: {qa_result_1.get('followup_answer', 'NO ANSWER')}")

# ─────────────────────────────────────────
# 10. Q&A ROUND 2
# ─────────────────────────────────────────
section("Q&A")

qa_state_2 = {
    **qa_result_1,
    "current_question": "Which feature has the strongest impact on house price?",
    "question_type":    "followup",
    "followup_answer":  "",
    "iteration_count":  0,
}

try:
    qa_result_2 = graph.invoke(qa_state_2)
    qa_error_2 = None
except Exception as e:
    qa_result_2 = None
    qa_error_2 = e

check(qa_error_2 is None,                          "Q&A round 2 ran without exception")
check(bool(qa_result_2.get("followup_answer")),    "Q&A round 2 produced an answer")
check(qa_result_2.get("current_question") == "",   "current_question cleared after answer")
check(len(qa_result_2.get("conversation_history", [])) == 4, "conversation history now has 4 entries")

print(f"\n  Answer 2: {qa_result_2.get('followup_answer', 'NO ANSWER')}")

# ─────────────────────────────────────────
# 11. FINAL SUMMARY
# ─────────────────────────────────────────
section("FINAL SUMMARY")

print(f"  CSV rows              : {len(df)}")
print(f"  CSV columns           : {len(df.columns)}")
print(f"  Domain detected       : {result.get('data_domain')}")
print(f"  Quality score         : {result.get('quality_score')}%")
print(f"  Issues found          : {len(result.get('issues_found', []))}")
print(f"  Cleaned df            : {'YES' if cleaned_df is not None else 'NO'}")
print(f"  Key findings          : {len(result.get('key_findings', []))}")
print(f"  Chart specs           : {len(result.get('visualisations', []))}")
print(f"  Report generated      : {'YES' if report else 'NO'} ({len(report)} chars)")
print(f"  Q&A rounds tested     : 2")
print(f"  Conversation entries  : {len(qa_result_2.get('conversation_history', []))}")
print(f"  Final status          : {result.get('status')}")

print(f"\n{'-'*65}")
print("COMPLETE ")
print(f"{'-'*65}\n")