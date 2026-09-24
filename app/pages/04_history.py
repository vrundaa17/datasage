import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from db.connection import SessionLocal
from db.models import AnalysisRun, Report, Upload
from app.components.session import get_or_create_session_token
from services.file_parser import get_create_user

st.set_page_config(page_title="DataSage — History", layout="wide")
st.title("Analysis History")

session_token = get_or_create_session_token()
user = get_create_user(session_token)
user_id = user.user_id

db = SessionLocal()
try:
    runs = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.user_id == user_id)
        .order_by(AnalysisRun.started_at.desc())
        .limit(20)
        .all()
    )
finally:
    db.close()

if not runs:
    st.info("No past analyses found. Upload a file to get started.")
    if st.button("Go to Upload"):
        st.switch_page("pages/01_upload.py")
    st.stop()

for run in runs:
    with st.expander(
        f"Run — {run.started_at.strftime('%d %b %Y %H:%M') if run.started_at else 'Unknown date'} "
        f"| Domain: {run.data_domain or '—'} "
        f"| Quality: {run.quality_score or 0:.1f}%"
    ):
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows",         run.row_count or 0)
        col2.metric("Quality",      f"{run.quality_score or 0:.1f}%")
        col3.metric("Domain",       run.data_domain or "—")
        
        # Fetch linked report text
        db2 = SessionLocal()
        try:
            report_row = db2.query(Report).filter(Report.run_id == run.run_id).first()
        finally:
            db2.close()
        
        if report_row and report_row.report_text:
            with st.container():
                st.markdown(report_row.report_text[:800] + "...")
        else:
            st.caption("No report text saved for this run.")
        
        # Key findings
        findings = run.key_finding or []
        if findings:
            st.markdown("**Key Findings:**")
            for i, f in enumerate(findings[:3], 1):
                st.markdown(f"**{i}.** {f}")