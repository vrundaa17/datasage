import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from services.file_parser import handle_upload
from app.components.session import get_or_create_session_token
from core.logger import get_logger
from core.exce import FileParsingError, UnsupportedFileTypeError

logger = get_logger(__name__)

st.set_page_config(page_title="DataSage - Upload", layout="wide")
st.title("Upload Your Data")
st.write("Supports CSV and Excel files up to 50MB")

session_token = get_or_create_session_token()

uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])

if uploaded_file:
    with st.spinner("Parsing your file..."):
        try:
            result = handle_upload(uploaded_file, session_token)
            df = result["df"]
            user = result["user"]
            upload = result["upload"]
            
            st.session_state["dataframe"] = df
            st.session_state["filename"] = uploaded_file.name
            st.session_state["user_id"]= str(user.user_id)
            st.session_state["upload_id"]= str(upload.upload_id)
            st.session_state.pop("analysis_result", None)
            st.session_state.pop("charts", None)

            st.success("File uploaded successfully")

            col1, col2 = st.columns(2)
            col2.metric("Columns", len(df.columns))

            st.subheader("Preview")
            st.dataframe(df.head(10))

            if st.button("Start Analysis →"):
                st.switch_page("pages/02_analysis.py")

        except UnsupportedFileTypeError as e:
            st.error(str(e))
        except FileParsingError as e:
            st.error(str(e))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            st.error("Something went wrong. Try again.")