import streamlit as st
import httpx

API_BASE_URL = "http://localhost:8000/api/v1"


def logout():
    st.session_state.token = None
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.session_id = None
    st.session_state.chat_history = []
    st.session_state.last_session_id = None


st.set_page_config(page_title="Login - LangGraph Agent", page_icon="🔐")

if "token" in st.session_state and st.session_state.token:
    st.title("🔐 Logged In")
    st.write(f"Welcome back, **{st.session_state.username}**!")
    
    if st.button("Logout", use_container_width=True):
        logout()
        st.rerun()
    
    if st.button("Go to Chat", use_container_width=True):
        st.switch_page("pages/chat.py")
    
    st.stop()

st.title("🔐 Login / Register")

tab1, tab2 = st.tabs(["Login", "Register"])

with tab1:
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("Please enter username and password")
            else:
                try:
                    data = {"username": username, "password": password}
                    response = httpx.post(f"{API_BASE_URL}/login", data=data)
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.token = result["access_token"]
                        st.session_state.username = username
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(response.json().get("detail", "Login failed"))
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")

with tab2:
    with st.form("register_form"):
        new_username = st.text_input("Username", key="reg_username")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register", use_container_width=True)
        
        if submit:
            if not new_username or not new_password:
                st.error("Please fill in all fields")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                try:
                    data = {"username": new_username, "password": new_password}
                    response = httpx.post(f"{API_BASE_URL}/register", json=data)
                    if response.status_code == 200:
                        st.success("Registration successful! Please login.")
                    else:
                        st.error(response.json().get("detail", "Registration failed"))
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")
