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
from db.connection import SessionLocal
from tools.db_writer import create_conversation, save_conversation_message
from tools.question_classifier import classify_question, is_data_question
import app.components.report_card as report_card
from app.components.progress_stream import show_agent_progress
from services.export_service import generate_report_pdf, generate_clean_csv

from core.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Analysis", layout="wide")
st.title("Analysis")


if "dataframe" not in st.session_state:

    st.info("Choose how you want to load your data")
    source = st.radio(
        "Data source",
        ["📁 Uploaded File", "🔌 My Database"],
        horizontal=True
    )

    if source == "📁 Uploaded File":
        st.warning("No file uploaded yet.")
        if st.button("Go to Upload"):
            st.switch_page("pages/01_upload.py")
        st.stop()

    else:
        # DB connection path
        from services.connection_service import get_user_connections, get_connection_string, list_tables
        from tools.db_loader import load_table_as_df

        session_token = get_or_create_session_token()

        try:
            db    = SessionLocal()
            # get user from session token same way your upload flow does
            user  = get_create_user(session_token)
            conns = get_user_connections(db, str(user.user_id))
            db.close()
        except Exception as e:
            st.error(f"Could not load connections: {e}")
            st.stop()

        if not conns:
            st.warning("No database connected yet.")
            if st.button("Connect a Database"):
                st.switch_page("pages/05_connect_db.py")
            st.stop()

        conn_map    = {c.name: c for c in conns}
        chosen_name = st.selectbox("Choose a connection", list(conn_map.keys()))
        chosen_conn = conn_map[chosen_name]

        try:
            db         = SessionLocal()
            conn_str   = get_connection_string(db, chosen_conn.id, str(user.user_id))
            tables     = list_tables(db, chosen_conn.id, str(user.user_id))
            db.close()
        except Exception as e:
            st.error(f"Could not reach database: {e}")
            st.stop()

        table = st.selectbox("Choose a table to analyze", tables)

        col_prev, col_load = st.columns([1, 1])
        with col_prev:
            if st.button("Preview Table"):
                from tools.db_loader import get_table_preview
                st.dataframe(get_table_preview(conn_str, table))
        with col_load:
            if st.button("Load & Analyse →", type="primary"):
                with st.spinner(f"Loading {table}..."):
                    df = load_table_as_df(conn_str, table)
                st.session_state["dataframe"] = df
                st.session_state["filename"]  = f"{chosen_name}__{table}"
                st.session_state["source_type"] = "Database"
                st.session_state["source_name"] = f"{chosen_name} → {table}"
                st.rerun()
        st.stop()


df = st.session_state["dataframe"]
filename = st.session_state.get("filename", "unknown.csv")

source_name = st.session_state.get("source_name", filename)
source_type = st.session_state.get("source_type", "CSV Upload")

session_token = get_or_create_session_token()

if "user_id" not in st.session_state or "upload_id" not in st.session_state:
    user   = get_create_user(session_token)
    upload = save_upload(
        user_id= user.user_id,
        filename = filename,
        filesize = 0,
        df = df,
    )
    st.session_state["user_id"]= str(user.user_id)
    st.session_state["upload_id"] = str(upload.upload_id)

user_id = st.session_state["user_id"]
upload_id = st.session_state["upload_id"]

 
# REPLACE the entire if "analysis_result" not in st.session_state: block:

if "analysis_result" not in st.session_state:

    initial_state = {
        "raw_df": df, "cleaned_df": None,
        "column_names": [], "data_types": {}, "null_counts": {}, "row_count": 0,
        "column_count": 0, "sample_values": {},
        "quality_score": 0.0, "issues_found": [], "data_domain": "",
        "engineered_df": None, "feature_report": {},
        "cleaning_report": {}, "analysis_results": {}, "key_findings": [], "visualisations": [],
        "report": "",
        "conversation_history": [], "current_question": "", "question_type": "",
        "followup_answer": "", "next_agent": "", "instructions": "",
        "iteration_count": 0,
        "user_id": user_id, "upload_id": upload_id, "error": None, "status": "running",
    }

    progress_placeholder = st.empty()

    try:
        graph = create_graph()
        result = None

        for snapshot in graph.stream(initial_state, stream_mode="values"):
            result = snapshot

            if snapshot.get("data_domain") and not snapshot.get("cleaning_report"):
                show_agent_progress(progress_placeholder, "inspector",
                                    f"Domain: {snapshot['data_domain']}", done=True)
                show_agent_progress(progress_placeholder, "cleaner", "Cleaning data...", done=False)

            elif snapshot.get("cleaning_report") and not snapshot.get("feature_report"):
                show_agent_progress(progress_placeholder, "cleaner", "Done", done=True)
                show_agent_progress(progress_placeholder, "feature_engineer",
                                    "Engineering features...", done=False)

            elif snapshot.get("feature_report") and not snapshot.get("analysis_results"):
                show_agent_progress(progress_placeholder, "feature_engineer", "Done", done=True)
                show_agent_progress(progress_placeholder, "eda", "Analysing...", done=False)

            elif snapshot.get("analysis_results") and not snapshot.get("report"):
                show_agent_progress(progress_placeholder, "eda", "Done", done=True)
                show_agent_progress(progress_placeholder, "reporter",
                                    "Writing report...", done=False)

            elif snapshot.get("report"):
                show_agent_progress(progress_placeholder, "reporter", "Done", done=True)

        if not result or result.get("error"):
            progress_placeholder.error(f"❌ {result.get('error', 'Unknown error') if result else 'Pipeline returned nothing'}")
            st.stop()

        with st.spinner("Saving results..."):
            saved = write_full_report(result)

        st.session_state["analysis_result"] = result
        st.session_state["charts"] = saved.get("charts", [])
        st.session_state["run_id"] = saved.get("run_id")

        progress_placeholder.empty()
        st.rerun()

    except Exception as e:
        progress_placeholder.error(f"❌ Something went wrong: {e}")
        logger.error(f"Pipeline error: {e}")
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
    
    # Feature engineering summary
    feature_report = result.get("feature_report", {})
    if feature_report.get("features_created"):
        st.divider()
        st.subheader("⚙️ Engineered Features")
        st.caption(feature_report.get("reasoning", ""))
        cols_created = feature_report.get("features_created", [])
        original = feature_report.get("original_shape", {})
        new_shape = feature_report.get("new_shape", {})
        st.markdown(
            f"Added **{len(cols_created)} new features** - "
            f"columns grew from **{original.get('cols', '?')}** | **{new_shape.get('cols', '?')}**"
        )
        for f in feature_report.get("features_planned", []):
            if f["name"] in cols_created:
                st.markdown(f"- **{f['name']}** - {f['description']}")
                
    report_card.render_key_findings(result.get("key_findings", []))
    st.divider()
    report_card.render_report(result.get("report", ""))

    st.divider()
    st.subheader("⬇️ Download Your Results")
    
    dl_col1, dl_col2 = st.columns(2)

    with dl_col1:
        try:
            if result.get("engineered_df") is not None:
                clean_df = result["engineered_df"]
            elif result.get("cleaned_df") is not None:
                clean_df = result["cleaned_df"]
            else:
                clean_df = df
            pdf = generate_report_pdf(
                source_name=source_name,
                source_type=source_type,
                summary=result.get("report", ""),
                quality_score=result.get("quality_score", 0),
                issues_fixed=len(result.get("issues_found", [])),
                charts=charts,
                findings=result.get("key_findings", []),
                qa_logs=st.session_state.get("qa_log", []),
                dataframe=clean_df,
            )
            st.download_button(
                label = "📄 Download PDF Report",
                data = pdf,
                file_name =f'datasage_report_{filename}.pdf',
                mime ="application/pdf"
            )
        except Exception as e:
            
            st.warning(f"PDF generation failed: {e}")
            
            
            
    with dl_col2:
        try:
            has_engineered = result.get("engineered_df") is not None
            has_cleaned = result.get("cleaned_df") is not None
            
            if has_engineered and has_cleaned:
                csv_choice = st.radio("Which version to choose?",["Cleaned", "Cleaned + Engineered "],horizontal=True)
                export_df = result["engineered_df"] if csv_choice == "Cleaned + Engineered " else result["cleaned_df"]
            elif has_engineered:
                export_df = result["engineered_df"]
            elif has_cleaned:
                export_df = result["cleaned_df"]
            else:
                export_df = df
                
                
            csv = generate_clean_csv(export_df)
            st.download_button(
                label="🧹 Download CSV",
                data=csv,
                file_name=f"datasage_clean_{filename}.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.warning(f"CSV failed: {e}")
            
            
            
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

                if not is_data_question(question):
                    with st.chat_message("assistant"):
                        st.markdown("I'm here to answer questions about your data. Try asking about trends, averages, or specific columns!")
                    st.stop()

                q_type = classify_question(question)
                qa_state = { **result,
                    "current_question": question, "question_type": q_type,
                    "followup_answer": "", "iteration_count": 0,}
                
                qa_result = graph.invoke(qa_state)
                answer = qa_result.get("followup_answer", "Sorry, I couldn't answer that.")
                with st.chat_message("assistant"):
                    st.markdown(answer)

                try:
                    db = SessionLocal()
                    run_id = st.session_state.get("run_id")
                    if run_id:
                        conv_id = create_conversation(db, user_id, run_id)
                        save_conversation_message(db, user_id, conv_id, "user", question, "followup")
                        save_conversation_message(db, user_id, conv_id, "assistant", answer, "followup")
                    db.close()
                except Exception as conv_err:
                    logger.warning(f"Could not save conversation to DB: {conv_err}")

                st.session_state["analysis_result"] = qa_result

            except Exception as e:
                st.error(f"Q&A failed: {e}")
                logger.error(f"Q&A error: {e}")