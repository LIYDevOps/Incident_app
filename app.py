import streamlit as st
import requests
import time
st.set_page_config(page_title="Auth System", layout="wide")

# ---------------- DEFAULT PAGE ----------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

# ---------------- HOME PAGE ----------------
if st.session_state["page"] == "home":
    st.title("🏠 Welcome to Incident Management System")

    st.write("Please choose an option below to continue:")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Login"):
            st.session_state["page"] = "login"
            st.rerun()
    with col2:
        if st.button("Sign Up"):
            st.session_state["page"] = "signup"
            st.rerun()

# ---------------- SIGN UP PAGE ----------------
elif st.session_state["page"] == "signup":
    st.title("🔐 Sign Up Page")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

if st.button("Submit Sign Up"):
    data = {"username": username, "email": email, "password": password}
    try:
        response = requests.post("http://127.0.0.1:8000/signup", json=data)
        result = response.json()
        if response.status_code == 200:
            st.success(result["message"])
            if result.get("redirect") == "login":
                st.info("👉 Redirecting you to login page...")
                time.sleep(5)
                st.session_state["page"] = "login"
                st.rerun()
        else:
            st.error(result["detail"])
    except Exception as e:
        st.error(f"Failed to connect to API: {e}")


    if st.button("⬅ Back to Home"):
        st.session_state["page"] = "home"
        st.rerun()

# ---------------- LOGIN PAGE ----------------
elif st.session_state["page"] == "login":
    st.title("🔑 Login Page")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Submit Login"):
        data = {"email": email, "password": password}
        try:
            response = requests.post("http://127.0.0.1:8000/login", json=data)
            if response.status_code == 200:
                result = response.json()
                st.success(f"{result['message']} (User: {result['user']})")
                st.session_state["user_email"] = email
                st.session_state["username"] = result["user"]
                st.session_state["page"] = "dashboard"
                st.rerun()
            else:
                st.error(response.json()["detail"])
        except Exception as e:
            st.error(f"Failed to connect to API: {e}")

    if st.button("⬅ Back to Home"):
        st.session_state["page"] = "home"
        st.rerun()

# ---------------- DASHBOARD PAGE ----------------
elif st.session_state["page"] == "dashboard":
    st.title("📊 Dashboard")

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.session_state["page"] = "home"
        st.rerun()

    # Top-left: Create Incident button
    if st.button("+ Create Incident"):
        st.session_state["page"] = "create_incident"
        st.rerun()

    # Top-right: User details
    st.sidebar.success(f"Logged in as: {st.session_state['username']} ({st.session_state['user_email']})")

    # Center: Open incidents
    try:
        response = requests.get("http://127.0.0.1:8000/incidents", params={"email": st.session_state["user_email"]})
        if response.status_code == 200:
            incidents = response.json()["open_incidents"]
            st.subheader(f"Open Incidents ({len(incidents)})")
            cols = st.columns(3)
            for idx, incident in enumerate(incidents):
                with cols[idx % 3]:
                    st.markdown(f"### {incident['title']}")
                    st.write(incident["description"])
                    st.write(f"Status: {incident['status']}")
        else:
            st.warning("No incidents found.")
    except Exception as e:
        st.error(f"Failed to fetch incidents: {e}")

# ---------------- CREATE INCIDENT PAGE ----------------
elif st.session_state["page"] == "create_incident":
    st.title("📝 Create Incident")

    if st.sidebar.button("⬅ Back to Dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()

    title = st.text_input("Incident Title")
    description = st.text_area("Description")

    if st.button("Submit Incident"):
        data = {
            "title": title,
            "description": description,
            "assigned_to": st.session_state["user_email"]
        }
        try:
            response = requests.post("http://127.0.0.1:8000/incidents", json=data)
            if response.status_code == 200:
                st.success("Incident created successfully!")
                st.session_state["page"] = "dashboard"
                st.rerun()
            else:
                st.error(response.json()["detail"])
        except Exception as e:
            st.error(f"Failed to connect to API: {e}")
