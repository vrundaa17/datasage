import streamlit as st
import uuid

def get_or_create_session_token() -> str:
    if "session_token" not in st.session_state:
        st.session_state["session_token"] = str(uuid.uuid4())
    return st.session_state["session_token"]