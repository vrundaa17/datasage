import pandas as pd
import sys 
from pathlib import Path 

PROJECT_ROOT = Path(__file__).resolve().parents[1] 
if str(PROJECT_ROOT) not in sys.path: 
    sys.path.insert(0, str(PROJECT_ROOT))
    
from agents.graph import create_graph

# Load a real CSV
df = pd.read_csv("tests/example.csv", encoding="utf-8-sig")

# Initial state
initial_state = {
    "raw_df": df,
    "cleaned_df": None,
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
    "analysis_results": {},
    "key_findings": [],
    "visualizations": [],
    "report": "",
    "next_agent": "",
    "instructions": "",
    "iteration_count": 0,
    "conversation_history": [],
    "current_question": "",
    "question_type": "",
    "followup_answer": "",
    "user_id": "test-user",
    "upload_id": "test-upload",
    "error": None,
    "status": "running"
}

graph = create_graph()
result = graph.invoke(initial_state)

print("Domain:", result["data_domain"])
print("Quality:", result["quality_score"])
print("Issues:", result["issues_found"])
print("Next agent:", result["next_agent"])