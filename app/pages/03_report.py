import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from app.components.charts import render_all_charts
import app.components.report_card as report_card
from core.logger import get_logger
logger = get_logger(__name__)
st.set_page_config(page_title="DataSage - Report", layout="wide")
st.title("Report")

if "analysis_result" not in st.session_state:
    st.warning("No analysis found. Run an analysis first.")
    if st.button("Go to Upload"):
        st.switch_page("pages/01_upload.py")
    st.stop()

result = st.session_state["analysis_result"]
charts = st.session_state.get("charts", [])

st.caption(f"""Domain: **{result.get('data_domain','-')}** | \n
           Rows: **{result.get('row_count',0)}** | \n
           Quality: **{result.get('quality_score',0.0):.1f}%**""")

report_card.render_quality_badge(result.get('quality_score',0.0))
st.divider()

report_card.render_key_findings(result.get('key_findings',[]))
st.divider()

report_card.render_report(result.get("report", ""))
st.divider()

st.subheader("Charts")
render_all_charts(charts)