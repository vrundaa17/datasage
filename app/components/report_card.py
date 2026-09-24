import streamlit as st

def render_report(report_text: str):
    if not report_text:
        st.warning("No report available.")
        return
    
    st.markdown(report_text)


def render_quality_badge(score: float):
    if score >= 85:
        color = "🟢"
    elif score >= 65:
        color = "🟡"
    else:
        color = "🔴"
    st.metric(label=f"{color} Data Quality Score", value=f"{score:.1f}%")


def render_key_findings(findings: list):
    if not findings:
        return
    st.subheader("Key Findings")
    for i, finding in enumerate(findings, 1):
        st.markdown(f"**{i}.** {finding}")
        
        
#chat things

def _inject_chat_css():
    st.markdown("""
    <style>
    .chat-wrapper {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding-bottom: 100px;  
    }
    .chat-row {
        display: flex;
        align-items: flex-end;
        gap: 8px;
    }
    .chat-row.user  { flex-direction: row-reverse; }
    .chat-row.assistant { flex-direction: row; }

    .bubble {
        max-width: 70%;
        padding: 10px 15px;
        border-radius: 18px;
        font-size: 0.95rem;
        line-height: 1.5;
        word-wrap: break-word;
    }
    .bubble.user {
        background: #2563eb;
        color: #ffffff;
        border-bottom-right-radius: 4px;
    }
    .bubble.assistant {
        background: #f1f5f9;
        color: #1e293b;
        border-bottom-left-radius: 4px;
    }
    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
    }
    .avatar.user      { background: #2563eb; }
    .avatar.assistant { background: #e2e8f0; }
    </style>
    """, unsafe_allow_html=True)


def render_chat_history(conversation_history: list):
    _inject_chat_css()

    if not conversation_history:
        st.caption("No conversation yet. Ask a question below!")
        return

    html = '<div class="chat-wrapper">'
    for msg in conversation_history:
        role = msg.get("role","user")
        content= msg.get("content", "").replace("\n", "<br>")
        avatar= "🐼" if role == "user" else "🧚"

        html += f"""
        <div class="chat-row {role}">
            <div class="avatar {role}">{avatar}</div>
            <div class="bubble {role}">{content}</div>
        </div>"""

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def chat_input_box() -> str | None:
    
    st.markdown("""
    <style>
    
    section[data-testid="stChatInput"] {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 999;
        background: var(--background-color, #ffffff);
        padding: 12px 2rem;
        border-top: 1px solid #e2e8f0;
        box-shadow: 0 -2px 8px rgba(0,0,0,0.06);
    }
    </style>
    """, unsafe_allow_html=True)

    return st.chat_input("Ask a question about your data...")