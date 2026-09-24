import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.graph import create_graph


def print_section(title):
    
    print(f"  {title}")
    print("-" * 65)


def assert_ok(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'} — {message}")


# ============================================================
# 1. LOAD CSV
# ============================================================

print_section("LOAD CSV")

csv_path = "tests/example.csv"

df = pd.read_csv(
    csv_path,
    encoding="utf-8-sig"
)

print(f"  File           : {csv_path}")
print(f"  Rows           : {len(df)}")
print(f"  Columns        : {len(df.columns)}")
print(f"  Column names   : {list(df.columns)}")

assert_ok(len(df) > 0, "CSV loaded successfully")
assert_ok(len(df.columns) > 0, "CSV has columns")


# ============================================================
# 2. INITIAL STATE
# ============================================================

print_section("INITIAL STATE")

initial_state = {
    # data
    "raw_df": df,
    "cleaned_df": None,

    # inspector
    "column_names": [],
    "data_types": {},
    "null_counts": {},
    "row_count": 0,
    "column_count": 0,
    "sample_values": {},
    "quality_score": 0.0,
    "issues_found": [],
    "data_domain": "",

    # cleaner
    "cleaning_report": {},

    # EDA
    "analysis_results": {},
    "key_findings": [],
    "visualisations": [],

    # final
    "report": "",

    # supervisor
    "next_agent": "",
    "instructions": "",
    "iteration_count": 0,

    # conversation / QA
    "conversation_history": [],
    "current_question": "",
    "question_type": "",
    "followup_answer": "",

    # meta
    "user_id": "integration-test-user",
    "upload_id": "integration-test-upload",

    # error / status
    "error": None,
    "status": "running",
}

print("  Initial state created")

assert_ok(
    initial_state["raw_df"] is not None,
    "raw_df exists"
)

assert_ok(
    initial_state["cleaned_df"] is None,
    "cleaned_df starts as None"
)


# ============================================================
# 3. CREATE GRAPH
# ============================================================

print_section("CREATE GRAPH")

graph = create_graph()

print("  Graph created successfully")

assert_ok(
    graph is not None,
    "graph object exists"
)


# ============================================================
# 4. RUN COMPLETE PIPELINE
# ============================================================

print_section("PIPELINE")



try:
    result = graph.invoke(initial_state)
    pipeline_error = None

except Exception as e:
    result = None
    pipeline_error = e

assert_ok(
    pipeline_error is None,
    "pipeline completed without Python exception"
)

if pipeline_error:
    print("\n❌ PIPELINE FAILED")
    print(pipeline_error)
    raise pipeline_error


# ============================================================
# 5. INSPECT FINAL STATE
# ============================================================

print_section("FINAL PIPELINE STATE")

print(f"  Status         : {result.get('status')}")
print(f"  Domain         : {result.get('data_domain')}")
print(f"  Quality        : {result.get('quality_score')}")
print(f"  Rows           : {result.get('row_count')}")
print(f"  Columns        : {result.get('column_count')}")
print(f"  Issues         : {len(result.get('issues_found', []))}")
print(f"  Findings       : {len(result.get('key_findings', []))}")
print(f"  visualisations : {len(result.get('visualisations', []))}")
print(f"  Next agent     : {result.get('next_agent')}")


# ============================================================
# 6. INSPECTOR CHECKS
# ============================================================

print_section("INSPECTOR CHECKS")

assert_ok(
    bool(result.get("data_domain")),
    "Inspector detected data domain"
)

assert_ok(
    result.get("row_count", 0) > 0,
    "Inspector populated row_count"
)

assert_ok(
    result.get("column_count", 0) > 0,
    "Inspector populated column_count"
)

assert_ok(
    bool(result.get("column_names")),
    "Inspector populated column_names"
)

assert_ok(
    bool(result.get("data_types")),
    "Inspector populated data_types"
)

assert_ok(
    result.get("quality_score") is not None,
    "Inspector calculated quality_score"
)


# ============================================================
# 7. CLEANER CHECKS
# ============================================================

print_section("CLEANER CHECKS")

cleaned_df = result.get("cleaned_df")

assert_ok(
    cleaned_df is not None,
    "Cleaner created cleaned_df"
)

if cleaned_df is not None:

    print(f"  Cleaned rows   : {len(cleaned_df)}")
    print(f"  Cleaned cols   : {len(cleaned_df.columns)}")
    print(f"  Cleaned names  : {list(cleaned_df.columns)}")

    assert_ok(
        len(cleaned_df) > 0,
        "cleaned_df contains rows"
    )

    assert_ok(
        len(cleaned_df.columns) > 0,
        "cleaned_df contains columns"
    )

assert_ok(
    bool(result.get("cleaning_report")),
    "Cleaner created cleaning_report"
)

report = result.get("cleaning_report", {})

if report:

    print(f"  Initial shape  : {report.get('initial_shape')}")
    print(f"  Final shape    : {report.get('final_shape')}")
    print(f"  New quality    : {report.get('new_quality_score')}")

    assert_ok(
        report.get("initial_shape") is not None,
        "cleaning report contains initial shape"
    )

    assert_ok(
        report.get("final_shape") is not None,
        "cleaning report contains final shape"
    )


# ============================================================
# 8. EDA CHECKS
# ============================================================

print_section("EDA CHECKS")

analysis = result.get("analysis_results", {})

assert_ok(
    bool(analysis),
    "EDA created analysis_results"
)

assert_ok(
    bool(result.get("key_findings")),
    "EDA generated key findings"
)

assert_ok(
    len(result.get("key_findings", [])) >= 3,
    "EDA generated at least 3 findings"
)

assert_ok(
    "shape" in analysis,
    "EDA stored dataset shape"
)

assert_ok(
    "numeric_columns" in analysis,
    "EDA stored numeric columns"
)

assert_ok(
    "categorical_columns" in analysis,
    "EDA stored categorical columns"
)

assert_ok(
    len(result.get("visualisations", [])) > 0,
    "EDA generated visualization specs"
)


# ============================================================
# 9. PRINT FINDINGS
# ============================================================

print_section("KEY FINDINGS")

for i, finding in enumerate(
    result.get("key_findings", []),
    start=1
):
    print(f"  {i}. {finding}")


# ============================================================
# 10. PRINT CHART SPECS
# ============================================================

print_section("VISUALISATION SPECS")

visualisations = result.get("visualisations", [])

for i, chart in enumerate(visualisations, start=1):

    print(f"\n  Chart {i}")
    print(f"    Type   : {chart.get('chart_type')}")
    print(f"    X      : {chart.get('x_column')}")
    print(f"    Y      : {chart.get('y_column')}")
    print(f"    Title  : {chart.get('title')}")
    print(f"    Reason : {chart.get('reason')}")


# ============================================================
# 11. ROUTING CHECK
# ============================================================

print_section("STEP 11 — GRAPH ROUTING")

assert_ok(
    result.get("next_agent") == "supervisor",
    "pipeline routes back to supervisor"
)

assert_ok(
    result.get("status") != "failed",
    "final status is not failed"
)

assert_ok(
    result.get("error") in [None, ""],
    "no pipeline error in state"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print_section("FINAL SUMMARY")

print(f"  CSV rows             : {len(df)}")
print(f"  CSV columns          : {len(df.columns)}")
print(f"  Detected domain      : {result.get('data_domain')}")
print(f"  Final quality        : {result.get('quality_score')}")
print(f"  Issues found         : {len(result.get('issues_found', []))}")
print(f"  Cleaned dataframe    : {'YES' if cleaned_df is not None else 'NO'}")
print(f"  Cleaning report      : {'YES' if result.get('cleaning_report') else 'NO'}")
print(f"  Analysis results     : {'YES' if analysis else 'NO'}")
print(f"  Key findings         : {len(result.get('key_findings', []))}")
print(f"  Chart specifications  : {len(visualisations)}")
print(f"  Final status         : {result.get('status')}")
print(f"  Next agent           : {result.get('next_agent')}")

print("\n" + "-" * 65)
print("FULL PIPELINE TEST COMPLETE")
print("-" * 65)
