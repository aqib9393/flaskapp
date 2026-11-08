import pandas as pd
import requests
import streamlit as st
import utils as u

st.set_page_config(page_title="Admin Portal", page_icon="🔐", layout="wide")

# Base URL for the backend connected to MongoDB
API_BASE_URL = "http://127.0.0.1:8000"


# ----------------- HTTP Requests (MongoDB API) -----------------
def login_request(username, password):
    """POST request to verify plaintext credentials against MongoDB."""
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
    """GET request to retrieve all users from MongoDB."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/admin/get_all_users", timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except requests.RequestException:
        return []


def create_user_request(user_data):
    """POST request to insert a new document in MongoDB."""
    try:
        print(f"Creating user with data: {user_data}")
        print(type(user_data))
        response = requests.post(f"{API_BASE_URL}/api/admin/create_user", json=user_data, timeout=5)
        return response.status_code in [200, 201], response.json().get(
            "message", ""
        )
    except requests.RequestException as e:
        return False, str(e)


def update_user_request(user_id, update_data):
    """PUT request to update an existing user by MongoDB _id."""
    try:
        response = requests.put(
            f"{API_BASE_URL}/api/admin/update_user/{user_id}", json=update_data, timeout=5
        )
        return response.status_code == 200, response.json().get("message", "")
    except requests.RequestException as e:
        return False, str(e)

# ----------------- Session State -----------------
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None


def logout():
    st.session_state.authenticated_user = None
    st.rerun()


# ----------------- Login View -----------------
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
                    st.success("Authentication successful.")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
    st.stop()

# ----------------- Portal Dashboard -----------------
current_user = st.session_state.authenticated_user
has_write_access = current_user.get("permissions") == "read_write"

with st.sidebar:
    st.subheader(f"Welcome, {current_user.get('name', '')}")
    st.caption(f"Role: **{current_user.get('role', '').upper()}**")
    st.caption(
        f"Access Level: **{'Read & Write' if has_write_access else 'Read Only'}**"
    )
    st.divider()
    if st.button("Log Out", use_container_width=True):
        logout()

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
            target = next(u for u in users_data if u["_id"] == selected_id)
            print(users_data)
            with st.form("edit_form"):
                
                edit_first_name = st.text_input("Full Name", value = target.get("first_name")+ " "+target.get("last_name"))
                edit_email = st.text_input("Email", value=target.get("email", ""))
                edit_weekly_job_limit = st.number_input("Weekly Job Limit", value=target.get("weekly_job_apply_limit", 0))
                
                try:
                    edit_expiration = st.date_input(
                        "Account Expiration Date",
                        value=pd.to_datetime(target.get("expiry_date", pd.Timestamp.now())),
                    )
                except:
                    edit_expiration = st.date_input(
                        "Account Expiration Date", value=pd.Timestamp.now()
                    )
                
                col_save, col_delete = st.columns([1, 1])
                save_clicked = col_save.form_submit_button(
                    "Save Changes", type="primary"
                )

                if save_clicked:
                    print(f"Updating user {selected_id} with first name: {edit_first_name}, email: {edit_email}, expiry_date: {edit_expiration}")
                    success, msg = update_user_request(
                        selected_id,
                        {
                            # u.first_name: edit_first_name,
                            # u.last_name: edit_last_name,
                            u.email: edit_email,
                            u.expiry_date: edit_expiration,
                        },
                    )
                    if success:
                        st.success("User updated successfully.")
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
                            "email": new_email
                        }
                    )
                    if success:
                        st.success("User created successfully.")
                    else:
                        st.error(f"Failed to create user: {msg}")

else:
    st.info("You have read-only access. Mutation controls are hidden.")
    st.dataframe(df, use_container_width=True, hide_index=True)