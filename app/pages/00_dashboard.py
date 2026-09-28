import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from app.components.session import get_or_create_session_token
from services.file_parser import get_create_user
from services.connection_service import get_user_connections, list_tables

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")
st.title("🏠 DataSage Dashboard")

# ── Session / user ────────────────────────────────────────────────────────────
session_token = get_or_create_session_token()
user          = get_create_user(session_token)
user_id       = str(user.user_id)
st.session_state["user_id"] = user_id


# ══════════════════════════════════════════════════════════════════════════════
# Data Sources section
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("📊 Your Data Sources")

db_conns = get_user_connections(user_id)

# Current session upload (from session_state)
current_df       = st.session_state.get("dataframe")
current_filename = st.session_state.get("filename")
current_source   = st.session_state.get("source_type", "CSV Upload")

# Count total items for column layout
total_items = len(db_conns) + (1 if current_df is not None else 0) + 1  # +1 for Add button
num_cols    = min(total_items, 4)

if num_cols == 0:
    num_cols = 2  # at minimum show 2 columns even if empty

cols    = st.columns(num_cols)
col_idx = 0

# ── DB connection cards ───────────────────────────────────────────────────────
for conn in db_conns:
    tables = list_tables(conn.id, user_id)
    with cols[col_idx % num_cols]:
        st.markdown(f"""
<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:8px;">
  <div style="font-size:22px;">🔌</div>
  <div style="font-weight:600;font-size:15px;margin:6px 0;">{conn.name}</div>
  <div style="color:#6b7280;font-size:12px;">{conn.db_type.upper()}</div>
  <div style="color:#10b981;font-size:12px;margin-top:6px;">🟢 Connected</div>
  <div style="color:#6b7280;font-size:12px;">{len(tables)} table(s)</div>
</div>
""", unsafe_allow_html=True)
    col_idx += 1

# ── Current session upload card ───────────────────────────────────────────────
if current_df is not None and current_filename:
    with cols[col_idx % num_cols]:
        st.markdown(f"""
<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:8px;">
  <div style="font-size:22px;">📁</div>
  <div style="font-weight:600;font-size:15px;margin:6px 0;">{current_filename}</div>
  <div style="color:#6b7280;font-size:12px;">{current_source}</div>
  <div style="color:#10b981;font-size:12px;margin-top:6px;">✅ Loaded</div>
  <div style="color:#6b7280;font-size:12px;">{len(current_df)} rows × {len(current_df.columns)} cols</div>
</div>
""", unsafe_allow_html=True)
    col_idx += 1

# ── Add Source button card ────────────────────────────────────────────────────
with cols[col_idx % num_cols]:
    st.markdown("""
<div style="border:2px dashed #e5e7eb;border-radius:12px;padding:16px;margin-bottom:8px;text-align:center;">
  <div style="font-size:28px;color:#9ca3af;">＋</div>
  <div style="color:#9ca3af;font-size:13px;">Add Source</div>
</div>
""", unsafe_allow_html=True)
    if st.button("Upload File", use_container_width=True):
        st.switch_page("pages/01_upload.py")
    if st.button("Connect Database", use_container_width=True):
        st.switch_page("pages/05_connect_db.py")


# ══════════════════════════════════════════════════════════════════════════════
# Latest Insight
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
st.subheader("📈 Latest Insight")

result = st.session_state.get("analysis_result")
if result:
    findings = result.get("key_findings", [])
    if findings:
        st.info(f"💡 {findings[0]}")
        if len(findings) > 1:
            with st.expander("See all findings"):
                for i, f in enumerate(findings, 1):
                    st.markdown(f"**{i}.** {f}")
    domain  = result.get("data_domain", "")
    quality = result.get("quality_score", 0)
    col_a, col_b = st.columns(2)
    col_a.metric("Domain", domain or "—")
    col_b.metric("Quality Score", f"{quality:.1f}%")

    if st.button("▶ View Full Report →", type="primary"):
        st.switch_page("pages/02_analysis.py")
else:
    st.info("No analysis run yet this session. Upload a file or connect your database to get started.")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📁 Upload a File", use_container_width=True):
            st.switch_page("pages/01_upload.py")
    with col_b:
        if st.button("🔌 Connect Database", use_container_width=True):
            st.switch_page("pages/05_connect_db.py")


# ══════════════════════════════════════════════════════════════════════════════
# History quick link
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
st.subheader("📂 Past Analyses")
st.caption("View all your previous analysis runs and reports")
if st.button("View History →"):
    st.switch_page("pages/04_history.py")