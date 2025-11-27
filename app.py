import streamlit as st
import requests
import time

st.set_page_config(page_title="Incident Management", layout="wide")

API_BASE = "http://127.0.0.1:8000"

# Initialize session state
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

# ------------- helpers -------------
def require_login():
    """Redirect to login if not authenticated."""
    if not st.session_state["user_email"] or not st.session_state["username"]:
        st.warning("You must be logged in to access the dashboard.")
        st.session_state["page"] = "login"
        st.rerun()

def top_auth_nav():
    """Auth navigation only for home/login/signup pages."""
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Login"):
            st.session_state["page"] = "login"
            st.rerun()
    with col2:
        if st.button("Sign Up"):
            st.session_state["page"] = "signup"
            st.rerun()

# ------------- HOME PAGE -------------
if st.session_state["page"] == "home":
    st.title("🏠 Welcome to Incident Management System")
    st.write("Manage your incidents, track open items, and create new ones.")
    top_auth_nav()

# ------------- SIGN UP PAGE -------------
elif st.session_state["page"] == "signup":
    st.title("🔐 Sign Up")
    top_auth_nav()  # show auth nav only here

    username = st.text_input("Username", key="signup_username")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")

    if st.button("Submit Sign Up", key="signup_submit"):
        data = {"username": username, "email": email, "password": password}
        try:
            response = requests.post(f"{API_BASE}/signup", json=data)
            result = response.json()
            if response.status_code == 200:
                st.success(result.get("message", "Signup processed."))
                # Show message clearly for 5 sec, then go to login
                st.info("👉 Redirecting you to login page in 5 seconds...")
                time.sleep(5)
                st.session_state["page"] = "login"
                st.rerun()
            else:
                st.error(result.get("detail", "Signup failed"))
        except Exception as e:
            st.error(f"Failed to connect to API: {e}")

    if st.button("⬅ Back to Home", key="signup_back"):
        st.session_state["page"] = "home"
        st.rerun()

# ------------- LOGIN PAGE -------------
elif st.session_state["page"] == "login":
    st.title("🔑 Login")
    top_auth_nav()  # show auth nav only here

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Submit Login", key="login_submit"):
        data = {"email": email, "password": password}
        try:
            response = requests.post(f"{API_BASE}/login", json=data)
            result = response.json()
            if response.status_code == 200:
                st.success(f"{result.get('message', 'Login successful')} (User: {result.get('user')})")
                st.session_state["user_email"] = email
                st.session_state["username"] = result.get("user")
                st.session_state["page"] = "dashboard"
                st.rerun()
            else:
                st.error(result.get("detail", "Invalid credentials"))
        except Exception as e:
            st.error(f"Failed to connect to API: {e}")

    if st.button("⬅ Back to Home", key="login_back"):
        st.session_state["page"] = "home"
        st.rerun()

# ------------- DASHBOARD PAGE -------------
elif st.session_state["page"] == "dashboard":
    require_login()  # ensure only logged-in users proceed

    st.title("📊 Dashboard")

    # Sidebar: user details + logout
    with st.sidebar:
        st.success(f"Logged in as: {st.session_state['username']} ({st.session_state['user_email']})")
        if st.button("Logout", key="logout"):
            st.session_state.clear()
            st.session_state["page"] = "home"
            st.rerun()

    # Top-left create incident
    if st.button("+ Create Incident", key="go_create_incident"):
        st.session_state["page"] = "create_incident"
        st.rerun()

    # Center: open incidents
    try:
        response = requests.get(
            f"{API_BASE}/incidents",
            params={"email": st.session_state["user_email"]}
        )
        if response.status_code == 200:
            data = response.json()
            incidents = data.get("open_incidents", [])
            st.subheader(f"Open Incidents ({len(incidents)})")

            # Flash-card style layout
            cols = st.columns(3)
            for idx, incident in enumerate(incidents):
                c = cols[idx % 3]
                with c:
                    st.markdown(f"### {incident.get('title','Untitled')}")
                    st.write(incident.get("description", ""))
                    st.caption(f"Status: {incident.get('status', 'open')}")
        else:
            st.warning("No incidents found or failed to fetch.")
    except Exception as e:
        st.error(f"Failed to fetch incidents: {e}")

# ------------- CREATE INCIDENT PAGE -------------
elif st.session_state["page"] == "create_incident":
    require_login()  # ensure only logged-in users proceed

    st.title("📝 Create Incident")

    with st.sidebar:
        if st.button("⬅ Back to Dashboard", key="back_to_dashboard"):
            st.session_state["page"] = "dashboard"
            st.rerun()

    title = st.text_input("Incident Title", key="incident_title")
    description = st.text_area("Description", key="incident_description")

    if st.button("Submit Incident", key="incident_submit"):
        data = {
            "title": title,
            "description": description,
            "assigned_to": st.session_state["user_email"]
        }
        try:
            response = requests.post(f"{API_BASE}/incidents", json=data)
            if response.status_code == 200:
                st.success("Incident created successfully!")
                st.session_state["page"] = "dashboard"
                st.rerun()
            else:
                result = response.json()
                st.error(result.get("detail", "Failed to create incident"))
        except Exception as e:
            st.error(f"Failed to connect to API: {e}")
