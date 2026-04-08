import streamlit as st
import httpx
import uuid

API_BASE_URL = "http://localhost:8000/api/v1"


def get_headers():
    if "token" not in st.session_state:
        return {}
    return {"Authorization": f"Bearer {st.session_state.token}"}


def get_sessions():
    try:
        response = httpx.get(f"{API_BASE_URL}/sessions", headers=get_headers())
        response.raise_for_status()
        return response.json().get("sessions", [])
    except Exception as e:
        st.error(f"Failed to fetch sessions: {e}")
        return []


st.set_page_config(page_title="Sessions - LangGraph Agent", page_icon="📋")

st.title("📋 Sessions")

if "username" not in st.session_state:
    st.error("Please login first")
    st.switch_page("pages/login.py")

col1, col2 = st.columns([6, 1])
with col1:
    st.write(f"Welcome, **{st.session_state.username}**!")
with col2:
    if st.button("New Chat"):
        new_id = str(uuid.uuid4())[:8]
        st.session_state.session_id = new_id
        st.session_state.chat_history = []
        st.session_state.last_session_id = None
        st.switch_page("pages/chat.py")

st.divider()

sessions = get_sessions()

if not sessions:
    st.info("No sessions yet. Start a new conversation!")
    if st.button("Start Chatting"):
        new_id = str(uuid.uuid4())[:8]
        st.session_state.session_id = new_id
        st.session_state.chat_history = []
        st.session_state.last_session_id = None
        st.switch_page("pages/chat.py")
else:
    for s in sessions:
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.subheader(f"Session: {s['session_id']}")
                st.caption(f"Messages: {s.get('message_count', 0)}")
                preview = s.get("last_message_preview", "")
                if preview:
                    st.text(f"Last: {preview[:100]}...")
            with col2:
                if st.button("Open", key=f"open_{s['session_id']}"):
                    st.session_state.session_id = s["session_id"]
                    st.session_state.chat_history = []
                    st.session_state.last_session_id = None
                    st.switch_page("pages/chat.py")
            st.divider()
