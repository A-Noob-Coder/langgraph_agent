import streamlit as st
import httpx

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
    except Exception:
        return []


def get_history(session_id: str):
    try:
        response = httpx.get(
            f"{API_BASE_URL}/history",
            headers=get_headers(),
            params={"session_id": session_id}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch history: {e}")
        return {"messages": [], "summary": ""}


st.set_page_config(page_title="History - LangGraph Agent", page_icon="🕒")

st.title("🕒 Conversation History")

if "username" not in st.session_state:
    st.error("Please login first")
    st.switch_page("pages/login.py")

st.write(f"Welcome, **{st.session_state.username}**!")

sessions = get_sessions()

if not sessions:
    st.info("No conversations yet.")
    if st.button("Start Chatting"):
        st.switch_page("pages/chat.py")
    st.stop()

session_ids = [s["session_id"] for s in sessions]
selected_session = st.selectbox("Select Conversation", session_ids, key="history_session")

if selected_session:
    history = get_history(selected_session)
    
    if history.get("summary"):
        st.subheader("📝 Summary")
        st.info(history["summary"])
    
    st.subheader("💬 Messages")
    messages = history.get("messages", [])
    
    if not messages:
        st.info("No messages in this conversation.")
    else:
        st.caption(f"Total: {len(messages)} messages")
        
        for msg in messages:
            if hasattr(msg, "type"):
                msg_type = msg.type
                content = msg.content if hasattr(msg, "content") else str(msg)
            else:
                msg_type = msg.get("type", "unknown")
                content = msg.get("content", "")
            
            if msg_type == "human":
                with st.chat_message("user"):
                    st.markdown(content)
            elif msg_type in ("ai", "assistant", "AIMessage"):
                with st.chat_message("assistant"):
                    st.markdown(content)
            else:
                with st.chat_message("user"):
                    st.caption(f"Type: {msg_type}")
                    st.markdown(content)

    st.divider()
    if st.button("Continue this conversation"):
        st.session_state.session_id = selected_session
        st.session_state.chat_history = []
        st.session_state.last_session_id = None
        st.switch_page("pages/chat.py")
