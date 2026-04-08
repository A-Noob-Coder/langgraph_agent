import streamlit as st
import httpx
import json
from datetime import datetime

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
        st.sidebar.error(f"Failed to load sessions: {e}")
        return []


def load_history(session_id: str):
    try:
        response = httpx.get(
            f"{API_BASE_URL}/history",
            headers=get_headers(),
            params={"session_id": session_id}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to load history: {e}")
        return {"messages": [], "summary": ""}


def convert_messages_to_chat_history(messages):
    chat_history = []
    for msg in messages:
        if hasattr(msg, "type"):
            msg_type = msg.type
            content = msg.content if hasattr(msg, "content") else str(msg)
        else:
            msg_type = msg.get("type", "unknown")
            content = msg.get("content", "")

        if msg_type == "human":
            chat_history.append({"role": "user", "content": content})
        elif msg_type in ("ai", "assistant", "AIMessage"):
            chat_history.append({"role": "assistant", "content": content})
    return chat_history


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "last_session_id" not in st.session_state:
    st.session_state.last_session_id = None

st.set_page_config(
    page_title="Chat - LangGraph Agent",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "username" not in st.session_state:
    st.error("Please login first")
    st.switch_page("pages/login.py")

st.title("💬 Chat")

with st.sidebar:
    st.header("💬 Conversations")
    
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.session_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.chat_history = []
        st.session_state.last_session_id = st.session_state.session_id
        st.rerun()
    
    st.divider()
    
    sessions = get_sessions()
    
    if sessions:
        for s in reversed(sessions[-10:]):
            session_name = s.get("session_id", "Untitled")
            is_active = st.session_state.session_id == session_name
            btn_label = f"💬 {session_name[:25]}"
            if is_active:
                btn_label = f"✅ {session_name[:22]}"
            
            if st.button(btn_label, key=f"session_{session_name}", use_container_width=True):
                st.session_state.session_id = session_name
                st.session_state.chat_history = []
                st.session_state.last_session_id = None
                st.rerun()
    else:
        st.info("No conversations yet")

if not st.session_state.session_id:
    st.info("👆 Select a conversation or create a new one from the sidebar")
    st.stop()

if st.session_state.session_id != st.session_state.last_session_id:
    history = load_history(st.session_state.session_id)
    st.session_state.chat_history = convert_messages_to_chat_history(history.get("messages", []))
    st.session_state.last_session_id = st.session_state.session_id

for msg in st.session_state.chat_history:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    with st.chat_message(role):
        st.markdown(content)

if prompt := st.chat_input("Type your message..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            with httpx.stream(
                "POST",
                f"{API_BASE_URL}/chat/stream",
                headers=get_headers(),
                params={"text": prompt, "session_id": st.session_state.session_id},
                timeout=180.0
            ) as response:
                if response.status_code != 200:
                    error_msg = response.text
                    message_placeholder.error(f"Error {response.status_code}: {error_msg}")
                else:
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                event_type = data.get("type")
                                
                                if event_type == "token":
                                    content = data.get("content", "")
                                    full_response += content
                                    message_placeholder.markdown(full_response + "▌")
                                    
                                elif event_type == "tool_call":
                                    tool_name = data.get("name", "unknown")
                                    with st.expander(f"🔧 Tool: {tool_name}"):
                                        st.json(data.get("args", {}))
                                        
                                elif event_type == "tool_result":
                                    with st.expander("🔧 Tool Result"):
                                        st.write(data.get("content", ""))
                                        
                                elif event_type == "done":
                                    full_response = data.get("content", full_response)
                                    message_placeholder.markdown(full_response)
                                    
                                elif event_type == "error":
                                    message_placeholder.error(data.get("message", "Error"))
                                    full_response = f"Error: {data.get('message', 'Unknown error')}"
                            except json.JSONDecodeError:
                                continue
                            
        except Exception as e:
            message_placeholder.error(f"Connection error: {str(e)}")
            full_response = f"Error: {str(e)}"
    
    st.session_state.chat_history.append({"role": "assistant", "content": full_response})

with st.sidebar:
    st.divider()
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
