"""
STREAMLIT INTEGRATION
======================
Ye code aapki Streamlit application mein add hoga.
Login ke baad, is helper ka use karke user ki local EXE ko commands bhej sakte hain.
"""

import requests
import streamlit as st

RELAY_BASE_URL = "https://test.muhammad-aqib.com"
RELAY_API_KEY = "replace_this_with_another_strong_random_key"  # relay_server.py ke RELAY_API_KEY se match hona chahiye


def send_command_to_local_app(client_id: str, command: str, data: dict = None, timeout: int = 30) -> dict:
    """
    Local EXE ko command bhejta hai relay server ke through.
    Returns: local EXE ka response (dict), ya error info agar fail ho.
    """
    url = f"{RELAY_BASE_URL}/api/send/{client_id}"
    headers = {"x-api-key": RELAY_API_KEY}
    payload = {"command": command, "data": data or {}, "timeout": timeout}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout + 5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            return {"status": "error", "result": "Local application is offline"}
        elif response.status_code == 504:
            return {"status": "error", "result": "Local application did not respond in time"}
        return {"status": "error", "result": str(e)}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "result": f"Connection error: {e}"}


def check_local_app_status(client_id: str) -> bool:
    """Check karta hai ke user ki local EXE relay se connected hai ya nahi."""
    url = f"{RELAY_BASE_URL}/api/status/{client_id}"
    headers = {"x-api-key": RELAY_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json().get("online", False)
    except requests.exceptions.RequestException:
        return False


# ---------------------------------------------------------------------------
# Example: Streamlit page ke andar use kaise karein (login ke baad)
# ---------------------------------------------------------------------------

def example_page():
    st.title("Local App Control Panel")

    # client_id aap login session se lenge (e.g. user ki unique ID/username)
    client_id = st.session_state.get("user_id", "user_123")

    is_online = check_local_app_status(client_id)
    if is_online:
        st.success("Local application connected hai ✅")
    else:
        st.error("Local application offline hai ❌ — pehle EXE run karein")

    if st.button("Run Task", disabled=not is_online):
        with st.spinner("Local application se response ka wait ho raha hai..."):
            result = send_command_to_local_app(
                client_id=client_id,
                command="run_task",
                data={"task_name": "example_task"},
            )
        if result.get("status") == "success":
            st.success(f"Result: {result.get('result')}")
        else:
            st.error(f"Error: {result.get('result')}")


if __name__ == "__main__":
    example_page()