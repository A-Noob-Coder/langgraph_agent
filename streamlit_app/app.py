import streamlit as st
from streamlit_option_menu import option_menu
from utils.api_client import client

st.set_page_config(
    page_title="LangGraph Agent",
    page_icon="🤖",
    layout="wide"
)


def main():
    if not client.is_logged_in():
        st.switch_page("pages/login.py")

    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("🤖 LangGraph Agent")
    with col2:
        if st.button("Logout"):
            client.logout()
            st.rerun()

    selected = option_menu(
        menu_title=None,
        options=["Chat", "Sessions", "History"],
        icons=["chat", "list", "clock-history"],
        default_index=0,
        orientation="horizontal"
    )

    if selected == "Chat":
        st.switch_page("pages/chat.py")
    elif selected == "Sessions":
        st.switch_page("pages/sessions.py")
    elif selected == "History":
        st.switch_page("pages/history.py")


if __name__ == "__main__":
    main()
