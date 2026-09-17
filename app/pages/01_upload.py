import streamlit as st 
import sys 
from pathlib import Path 
import uuid


PROJECT_ROOT = Path(__file__).resolve().parents[2] 
if str(PROJECT_ROOT) not in sys.path: 
    sys.path.insert(0, str(PROJECT_ROOT))
    
from services.file_parser import handle_upload
from core.logger import get_logger
logger = get_logger(__name__)

# Generate session token once per browser session
if "session_token" not in st.session_state:
    st.session_state["session_token"] = str(uuid.uuid4())

st.title("Upload Your Data")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file:
    with st.spinner("Processing your file..."):
        try:
            result = handle_upload(
                file=uploaded_file,
                session_token=st.session_state["session_token"]
            )
            
            df = result["df"]
            user = result["user"]
            upload = result["upload"]
            
            st.session_state["dataframe"] = df
            st.session_state["user_id"] = str(user.user_id)
            st.session_state["upload_id"] = str(upload.upload_id)
            st.session_state["filename"] = uploaded_file.name
            
            st.success("File uploaded successfully")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Rows", len(df))
            col2.metric("Columns", len(df.columns))
            col3.metric("File", uploaded_file.name)
            
            st.subheader("Preview")
            st.dataframe(df.head(10))
            
            if st.button("Start Analysis →"):
                st.switch_page("pages/02_analysis.py")
        
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            st.error(f"Upload failed: {e}")