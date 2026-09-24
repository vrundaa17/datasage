import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from agents.graph import create_graph
from services.file_parser import get_create_user, save_upload
from tools.report_writer import write_full_report
from app.components.session import get_or_create_session_token
from app.components.charts import render_all_charts
import app.components.report_card as report_card
from core.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Analysis", layout="wide")
st.title("Analysis")


if "dataframe" not in st.session_state:
    st.warning("No file uploaded yet.")
    if st.button("Go to Upload"):
        st.switch_page("pages/01_upload.py")
    st.stop()

df = st.session_state["dataframe"]
filename = st.session_state.get("filename", "unknown.csv")


session_token = get_or_create_session_token()

if "user_id" not in st.session_state or "upload_id" not in st.session_state:
    user   = get_create_user(session_token)
    upload = save_upload(
        user_id  = user.user_id,
        filename = filename,
        filesize = 0,
        df = df,
    )
    st.session_state["user_id"]= str(user.user_id)
    st.session_state["upload_id"] = str(upload.upload_id)

user_id = st.session_state["user_id"]
upload_id = st.session_state["upload_id"]

 
if "analysis_result" not in st.session_state:

    initial_state = {
        "raw_df": df, "cleaned_df": None,
        "column_names": [], "data_types": {}, "null_counts":{}, "row_count": 0, "column_count": 0,"sample_values": {},
        "quality_score": 0.0, "issues_found":[], "data_domain": "",
        "cleaning_report": {}, "analysis_results":{}, "key_findings": [], "visualisations":[],
        "report": "",
        "conversation_history": [], 
        "current_question": "", "question_type": "", "followup_answer": "", "next_agent": "", "instructions": "",
        "iteration_count": 0,
        "user_id": user_id, "upload_id": upload_id, "error": None, "status": "running",
    }

    with st.status("Running DataSage pipeline...", expanded=True) as status:
        st.write("Inspecting your data...")
        try:
            graph= create_graph()
            result = graph.invoke(initial_state)

            if result.get("error"):
                status.update(label="Pipeline failed", state="error")
                st.error(f"Error: {result['error']}")
                st.stop()

            st.write("Saving results to database...")
            saved = write_full_report(result)

            st.session_state["analysis_result"] = result
            st.session_state["charts"] = saved.get("charts", [])
            st.session_state["run_id"]= saved.get("run_id")

            status.update(label="Analysis complete!", state="complete")
        except Exception as e:
            status.update(label="Something went wrong", state="error")
            logger.error(f"Pipeline error: {e}")
            st.error(str(e))
            st.stop()


result = st.session_state["analysis_result"]
charts = st.session_state.get("charts", [])

tab_report, tab_charts, tab_qa = st.tabs(["Report", "Charts", "Ask Questions"])

with tab_report:
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", result.get("row_count", 0))
    col2.metric("Columns",result.get("column_count", 0))
    col3.metric("Domain",result.get("data_domain", "-"))

    report_card.render_quality_badge(result.get("quality_score", 0.0))
    st.divider()
    report_card.render_key_findings(result.get("key_findings", []))
    st.divider()
    report_card.render_report(result.get("report", ""))


with tab_charts:
    render_all_charts(charts)


with tab_qa:
    st.subheader("Ask questions about your data")
    report_card.render_chat_history(result.get("conversation_history", []))
    question = report_card.chat_input_box()

    if question:
        with st.chat_message("user"):
            st.markdown(question)
        with st.spinner("Thinking..."):
            try:
                graph = create_graph()
                qa_state = { **result,
                    "current_question": question, "question_type": "followup",
                    "followup_answer":"", "iteration_count": 0,}
                
                qa_result = graph.invoke(qa_state)
                answer = qa_result.get("followup_answer", "Sorry, I couldn't answer that.")
                with st.chat_message("assistant"):
                    st.markdown(answer)

                st.session_state["analysis_result"] = qa_result

            except Exception as e:
                st.error(f"Q&A failed: {e}")
                logger.error(f"Q&A error: {e}")