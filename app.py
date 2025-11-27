import streamlit as st
import requests

st.set_page_config(page_title="Auth System", layout="wide")

# Top navigation buttons
col1, col2, col3 = st.columns([6, 1, 1])
with col2:
    if st.button("Login"):
        st.session_state["page"] = "login"
with col3:
    if st.button("Sign Up"):
        st.session_state["page"] = "signup"

# Default page
if "page" not in st.session_state:
    st.session_state["page"] = "signup"

# ---------------- SIGN UP PAGE ----------------
if st.session_state["page"] == "signup":
    st.title("🔐 Sign Up Page")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Submit Sign Up"):
        data = {"username": username, "email": email, "password": password}
        try:
            response = requests.post("http://127.0.0.1:8000/signup", json=data)
            if response.status_code == 200:
                result = response.json()
                st.success(f"{result['message']} (User: {result['user']})")
            else:
                st.error(response.json()["detail"])
                st.info("👉 Please login instead.")
                st.session_state["page"] = "login"
        except Exception as e:
            st.error(f"Failed to connect to API: {e}")

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
            else:
                st.error(response.json()["detail"])
        except Exception as e:
            st.error(f"Failed to connect to API: {e}")
