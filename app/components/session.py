import uuid
import streamlit as st
from core.logger import get_logger

logger = get_logger(__name__)

def get_or_create_session_token() -> str:
    if "session_token" not in st.session_state:
        st.session_state["session_token"] = str(uuid.uuid4())
        logger.info(f"New session token: {st.session_state['session_token'][:8]}")
    return st.session_state["session_token"]