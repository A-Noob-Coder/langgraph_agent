import streamlit as st
import httpx
from typing import Optional

API_BASE_URL = "http://localhost:8000/api/v1"


class APIClient:
    def __init__(self):
        if "token" not in st.session_state:
            st.session_state.token = None
        if "user_id" not in st.session_state:
            st.session_state.user_id = None
        if "username" not in st.session_state:
            st.session_state.username = None

    @property
    def token(self) -> Optional[str]:
        return st.session_state.token

    @property
    def headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def is_logged_in(self) -> bool:
        return self.token is not None

    def login(self, username: str, password: str) -> dict:
        data = {"username": username, "password": password}
        response = httpx.post(f"{API_BASE_URL}/login", data=data)
        response.raise_for_status()
        result = response.json()
        st.session_state.token = result["access_token"]
        st.session_state.username = username
        self._decode_token()
        return result

    def register(self, username: str, password: str) -> dict:
        data = {"username": username, "password": password}
        response = httpx.post(f"{API_BASE_URL}/register", json=data)
        response.raise_for_status()
        return response.json()

    def _decode_token(self):
        import jwt
        if self.token:
            try:
                payload = jwt.decode(self.token, options={"verify_signature": False})
                st.session_state.user_id = payload.get("sub")
            except Exception:
                pass

    def logout(self):
        st.session_state.token = None
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.session_id = None
        st.session_state.messages = []

    def set_session_id(self, session_id: str):
        st.session_state.session_id = session_id

    def get_sessions(self) -> list:
        response = httpx.get(f"{API_BASE_URL}/sessions", headers=self.headers)
        response.raise_for_status()
        return response.json().get("sessions", [])

    def get_history(self, session_id: str) -> dict:
        response = httpx.get(
            f"{API_BASE_URL}/history",
            headers=self.headers,
            params={"session_id": session_id}
        )
        response.raise_for_status()
        return response.json()

    def chat(self, text: str, session_id: str) -> dict:
        response = httpx.post(
            f"{API_BASE_URL}/chat",
            headers=self.headers,
            params={"text": text, "session_id": session_id}
        )
        response.raise_for_status()
        return response.json()

    def chat_stream(self, text: str, session_id: str):
        with httpx.stream(
            "POST",
            f"{API_BASE_URL}/chat/stream",
            headers=self.headers,
            params={"text": text, "session_id": session_id},
            timeout=120.0
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    yield line[6:]


client = APIClient()
