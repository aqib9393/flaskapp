from datetime import datetime, time, timezone
from time import sleep
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
import pandas as pd
import requests
import streamlit as st
import utils as u

st.set_page_config(page_title="Admin Portal", page_icon="🔐", layout="wide")

# Base URL for the backend connected to MongoDB
API_BASE_URL = "https://databaseapi.muhammad-aqib.com"

# Secret key kept on the server (store in .streamlit/secrets.toml)
SECRET_KEY = st.secrets.get("SESSION_SECRET", "change-this-to-a-secure-random-key")
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7 # 24 hours

serializer = URLSafeTimedSerializer(SECRET_KEY)


# ----------------- Session Persistence Helpers -----------------
def encode_session_token(user_data: dict) -> str:
    return serializer.dumps(user_data)


def decode_session_token(
    token: str, max_age: int = SESSION_MAX_AGE_SECONDS
) -> dict | None:
    try:
        return serializer.loads(token, max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None


# ----------------- HTTP Requests (MongoDB API) -----------------
def login_request(username, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/admin_login",
            json={"username": username, "password": password},
            timeout=5,
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


def fetch_all_users():
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/admin/get_all_users", timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return []
    except requests.RequestException:
        return []


def create_user_request(user_data):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/admin/create_user", json=user_data, timeout=5
        )
        return response.status_code in [200, 201], response.json().get(
            "message", ""
        )
    except requests.RequestException as e:
        return False, str(e)


def update_user_request(user_id, update_data):
    try:
        response = requests.put(
            f"{API_BASE_URL}/api/admin/update_user/{user_id}",
            json=update_data,
            timeout=5,
        )
        return response.status_code == 200, response.json().get("message", "")
    except requests.RequestException as e:
        return False, str(e)

def fetch_contact_messages():
    """GET request to retrieve contact submissions."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/admin/get_user_contact_messages", timeout=5
        )
        if response.status_code == 200:
            return response.json()['result']
        return []
    except requests.RequestException:
        return []


def mark_message_as_viewed(message_id):
    """PUT request to flag the message as viewed in MongoDB."""
    try:
        response = requests.put(
            f"{API_BASE_URL}/api/admin/update_contact/{message_id}",
            json={"isViewd": True},
            timeout=5,
        )
        
        return response.status_code == 200, response.json().get("success", "")
    except requests.RequestException as e:
        return False, str(e)


# ----------------- Session State & Query Param Sync -----------------
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

if not st.session_state.authenticated_user:
    session_token = st.query_params.get("session")
    if session_token:
        restored_user = decode_session_token(session_token)
        if restored_user:
            st.session_state.authenticated_user = restored_user
        else:
            del st.query_params["session"]
            st.warning("Your session has expired. Please log in again.")


def logout():
    st.session_state.authenticated_user = None
    if "session" in st.query_params:
        del st.query_params["session"]
    st.rerun()


# =====================================================================
# UN-AUTHENTICATED VIEW: User Contact Form OR Admin Login
# =====================================================================
if not st.session_state.authenticated_user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Admin Portal Login")
        with st.form("login_form"):
            username = st.text_input("Username").strip()
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In")

            if submit:
                user = login_request(username, password)
                if user:
                    st.session_state.authenticated_user = user
                    st.query_params["session"] = encode_session_token(user)
                    st.success("Authentication successful.")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
    st.stop()


# =====================================================================
# AUTHENTICATED VIEW: Admin Dashboard
# =====================================================================
current_user = st.session_state.authenticated_user
has_write_access = current_user.get("permissions") == "read_write"

with st.sidebar:
    st.subheader(
        f"Welcome, {current_user.get('name', current_user.get('username', ''))}"
    )
    st.caption(f"Role: **{current_user.get('role', '').upper()}**")
    st.caption(
        f"Access Level: **{'Read & Write' if has_write_access else 'Read Only'}**"
    )
    st.divider()

    admin_view_choice = st.radio(
        "Navigation", ["Users Directory", "Unread Messages Inbox"]
    )

    st.divider()
    if st.button("Log Out", use_container_width=True):
        logout()


# ----------------- SECTION 1: Users Directory -----------------
if admin_view_choice == "Users Directory":
    st.title("Workyai User Management")

    users_data = fetch_all_users()
    df = (
        pd.DataFrame(users_data).drop(columns=["password"], errors="ignore")
        if users_data
        else pd.DataFrame()
    )

    if has_write_access:
        tab_view, tab_edit, tab_create = st.tabs(
            ["View Users", "Modify User", "Add New User"]
        )

        with tab_view:
            st.dataframe(df, use_container_width=True, hide_index=True)

        with tab_edit:
            st.subheader("Edit User Record")
            if not df.empty and "_id" in df.columns:
                user_ids = df["_id"].tolist()
                selected_id = st.selectbox("Select User ID to edit:", user_ids)
                target = next(
                    (u for u in users_data if u["_id"] == selected_id), {}
                )

                with st.form("edit_form"):
                    full_name_val = f"{target.get('first_name') or ''} {target.get('last_name') or ''}".strip()
                    edit_first_name = st.text_input(
                        "Full Name", value=full_name_val
                    )
                    edit_email = st.text_input(
                        "Email", value=target.get("email", "")
                    )
                    edit_weekly_job_limit = st.number_input(
                        "Weekly Job Limit",
                        value=int(target.get("weekly_job_apply_limit", 0)),
                    )

                    try:
                        edit_expiration = st.date_input(
                            "Account Expiration Date",
                            value=pd.to_datetime(
                                target.get("expiry_date", pd.Timestamp.now())
                            ),
                        )
                    except Exception:
                        edit_expiration = st.date_input(
                            "Account Expiration Date", value=pd.Timestamp.now()
                        )

                    col_save, _ = st.columns([1, 1])
                    save_clicked = col_save.form_submit_button(
                        "Save Changes", type="primary"
                    )

                    if save_clicked:
                        formatted_expiry = None
                        if edit_expiration:
                            if isinstance(edit_expiration, datetime):
                                formatted_expiry = edit_expiration.astimezone(
                                    timezone.utc
                                ).isoformat()
                            else:
                                combined_dt = datetime.combine(
                                    edit_expiration, time.max
                                ).replace(tzinfo=timezone.utc)
                                formatted_expiry = combined_dt.isoformat()

                        payload = {
                            u.email: edit_email,
                            u.expiry_date: formatted_expiry,
                            u.weekly_job_apply_limit: edit_weekly_job_limit,
                        }
                        success, msg = update_user_request(selected_id, payload)
                        if success:
                            st.success("User updated successfully.")
                            sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Failed to update: {msg}")
            else:
                st.info("No records found to edit.")

        with tab_create:
            st.subheader("Register New User")
            with st.form("create_form"):
                new_username = st.text_input("Username").strip()
                new_first_name = st.text_input("First Name").strip()
                new_last_name = st.text_input("Last Name").strip()
                new_pass = st.text_input("Password", type="password")
                new_email = st.text_input("Email")
                add_submit = st.form_submit_button("Create User")

                if add_submit:
                    if not new_username or not new_pass:
                        st.error("Username and password are required.")
                    else:
                        success, msg = create_user_request(
                            {
                                "username": new_username,
                                "password": new_pass,
                                "first_name": new_first_name,
                                "last_name": new_last_name,
                                "email": new_email,
                            }
                        )
                        if success:
                            st.success("User created successfully.")
                            st.rerun()
                        else:
                            st.error(f"Failed to create user: {msg}")
    else:
        st.info("You have read-only access. Mutation controls are hidden.")
        st.dataframe(df, use_container_width=True, hide_index=True)


# ----------------- SECTION 2: Unread Contact Messages -----------------
elif admin_view_choice == "Unread Messages Inbox":
    st.title("Unread Contact Submissions")

    all_messages = fetch_contact_messages()

    # Filter strictly for isViewd == False
    unread_messages = [
        msg for msg in all_messages if msg.get("isViewed") is False
    ]

    if not unread_messages:
        st.info("No unread contact messages found.")
    else:
        st.caption(
            f"Showing {len(unread_messages)} unviewed submission(s)."
        )

        for msg in unread_messages:
            msg_id = msg.get("_id")
            first_name = msg.get("first_name", "")
            last_name = msg.get("last_name", "")
            sender_name = f"{first_name} {last_name}".strip() or "Anonymous"
            sender_email = msg.get("email", "N/A")
            sender_phone = msg.get("phone", "N/A")
            message_content = msg.get("message", "")

            # Container card for each unread submission
            with st.container(border=True):
                c_head, c_btn = st.columns([4, 1])
                with c_head:
                    st.subheader(f"From: {sender_name}")
                    st.write(
                        f"**Email:** `{sender_email}` | **Phone:** `{sender_phone}`"
                    )

                with c_btn:
                    # Clicking this marks the entry as viewed in MongoDB and refreshes
                    if st.button("Mark as Viewed", key=f"view_{msg_id}"):
                        success, update_msg = mark_message_as_viewed(msg_id)
                        if success:
                            st.success("Marked as viewed.")
                            sleep(0.5)
                            st.rerun()
                        else:
                            st.error(f"Error updating message: {update_msg}")

                st.markdown("**Message:**")
                st.info(message_content)