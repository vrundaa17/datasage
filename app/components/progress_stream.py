import streamlit as st
import time

def show_agent_progress(status_placeholder, agent_name, message, done: bool = False):
    if "agent_progress" not in st.session_state:
        st.session_state.agent_progress = {}

    st.session_state.agent_progress[agent_name] = {
        "message": message,
        "done": done
    }

    with status_placeholder.container():
        agents = [
            ("inspector", "🔍 Inspector"),
            ("cleaner", "🧹 Cleaner"),
            ("feature_engineer", "⚙️ Feature Engineer"),
            ("eda", "📊 EDA"),
            ("reporter", "📝 Reporter"),
        ]
        for key, label in agents:
            info = st.session_state.agent_progress.get(key)
            if not info:
                st.markdown(f"🟨 **{label}**      :      waiting...")
            elif info["done"]:
                st.markdown(f"🎯 **{label}**      :      {info['message']}")
            else:
                st.markdown(f"🐢 **{label}**      :      {info['message']}")