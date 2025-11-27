# incident_app.py
import streamlit as st
import requests
import time

st.set_page_config(page_title="Incident Management", layout="wide")
API = "http://127.0.0.1:8000"

# Session state
for key, default in [
    ("page", "home"),
    ("user_email", None),
    ("username", None),
    ("role", None),
    ("incident_id", None),
    ("analyst_group", "Support"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

def require_login():
    if not st.session_state["user_email"] or not st.session_state["username"]:
        st.warning("You must be logged in.")
        st.session_state["page"] = "login"
        st.rerun()

def top_auth_nav():
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Login"):
            st.session_state["page"] = "login"; st.rerun()
    with c2:
        if st.button("Sign Up"):
            st.session_state["page"] = "signup"; st.rerun()

# Home
if st.session_state["page"] == "home":
    st.title("🏠 Incident Management System")
    st.write("Create incidents, track progress, and see projected resolution time.")
    top_auth_nav()

# Signup
elif st.session_state["page"] == "signup":
    st.title("🔐 Sign Up")
    top_auth_nav()
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["user", "analyst"])

    if st.button("Submit Sign Up"):
        payload = {"username": username, "email": email, "password": password, "role": role}
        try:
            r = requests.post(f"{API}/signup", json=payload)
            res = r.json()
            if r.status_code == 200:
                st.success("Signup successful. Redirecting to login...")
                time.sleep(1.5); st.session_state["page"] = "login"; st.rerun()
            else:
                st.error(res.get("detail", "Signup failed"))
        except Exception as e:
            st.error(f"API error: {e}")

    if st.button("⬅ Back to Home"):
        st.session_state["page"] = "home"; st.rerun()

# Login
elif st.session_state["page"] == "login":
    st.title("🔑 Login")
    top_auth_nav()
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Submit Login"):
        try:
            r = requests.post(f"{API}/login", json={"email": email, "password": password})
            res = r.json()
            if r.status_code == 200:
                st.session_state["user_email"] = email
                st.session_state["username"] = res.get("user")
                st.session_state["role"] = res.get("role")
                st.success(f"Welcome {st.session_state['username']} ({st.session_state['role']})")
                st.session_state["page"] = "dashboard"; st.rerun()
            else:
                st.error(res.get("detail", "Invalid credentials"))
        except Exception as e:
            st.error(f"API error: {e}")

    if st.button("⬅ Back to Home"):
        st.session_state["page"] = "home"; st.rerun()

# Dashboard
elif st.session_state["page"] == "dashboard":
    require_login()
    st.title("📊 Dashboard")

    with st.sidebar:
        st.success(f"Logged in: {st.session_state['username']} ({st.session_state['user_email']})")
        st.info(f"Role: {st.session_state['role']}")
        if st.button("Logout"):
            st.session_state.clear(); st.session_state["page"] = "home"; st.rerun()

    if st.session_state["role"] == "user":
        # Create Incident
        st.subheader("📝 Create Incident")
        title = st.text_input("Title")
        description = st.text_area("Description")
        group_name = st.selectbox("Assign to Group", ["Support", "Infra", "Network"])

        if st.button("Ensure Group Exists"):
            try:
                rg = requests.post(f"{API}/groups/create", params={"name": group_name})
                st.info(rg.json().get("message", "Done"))
            except Exception as e:
                st.error(f"API error: {e}")

        if st.button("Submit Incident"):
            payload = {"title": title, "description": description, "group_name": group_name}
            try:
                r = requests.post(f"{API}/incidents", params={"requester_email": st.session_state["user_email"]}, json=payload)
                try:
                    res = r.json()
                except Exception:
                    st.error(f"Unexpected response: {r.text}"); st.stop()
                if r.status_code == 200:
                    st.success(f"Created Incident #{res['incident']['id']}")
                    st.session_state["incident_id"] = res["incident"]["id"]
                    st.session_state["page"] = "incident_detail"; st.rerun()
                else:
                    st.error(res.get("detail", "Failed to create incident"))
            except Exception as e:
                st.error(f"API error: {e}")

        # Stats card
        st.subheader("📈 My Stats")
        try:
            ds = requests.get(f"{API}/dashboard_stats", params={"email": st.session_state["user_email"]}).json()
            c1, c2 = st.columns(2)
            with c1:
                st.metric("📂 Open Incidents", ds.get("open_incidents", 0))
            with c2:
                v = ds.get("latest_projected_hours")
                st.metric("⏳ Projected Closure (hrs)", f"{v:.1f}" if v is not None else "—")
        except Exception as e:
            st.error(f"API error: {e}")

        # My Incidents
        st.subheader("📂 My Incidents")
        try:
            r = requests.get(f"{API}/incidents/my", params={"email": st.session_state["user_email"]})
            res = r.json()
            incidents = res.get("incidents", [])
            cols = st.columns(3)
            for idx, inc in enumerate(incidents):
                c = cols[idx % 3]
                with c:
                    st.markdown(f"### #{inc['id']} — {inc['title']}")
                    st.caption(f"Group: {inc.get('group')}")
                    st.write(inc.get("description", ""))
                    st.caption(f"Status: {inc['status']}")
                    if st.button(f"Open #{inc['id']}", key=f"open_{inc['id']}"):
                        st.session_state["incident_id"] = inc["id"]
                        st.session_state["page"] = "incident_detail"; st.rerun()
        except Exception as e:
            st.error(f"API error: {e}")

    else:
        # Analyst view
        st.subheader("🛠 Analyst Queue")
        st.session_state["analyst_group"] = st.selectbox("Analyst Group", ["Support", "Infra", "Network"], index=["Support", "Infra", "Network"].index(st.session_state["analyst_group"]))
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Ensure Group Exists"):
                try:
                    rg = requests.post(f"{API}/groups/create", params={"name": st.session_state['analyst_group']})
                    st.info(rg.json().get("message", "Done"))
                except Exception as e:
                    st.error(f"API error: {e}")
        with c2:
            if st.button("Join Group"):
                try:
                    ra = requests.post(f"{API}/groups/add_analyst", params={"analyst_email": st.session_state["user_email"], "group_name": st.session_state["analyst_group"]})
                    st.info(ra.json().get("message", "Done"))
                except Exception as e:
                    st.error(f"API error: {e}")

        try:
            rq = requests.get(f"{API}/incidents/group_queue", params={"group_name": st.session_state["analyst_group"]})
            resq = rq.json()
            open_incidents = resq.get("open_incidents", [])
            st.caption(f"Open in {st.session_state['analyst_group']}: {len(open_incidents)}")
            cols = st.columns(3)
            for idx, inc in enumerate(open_incidents):
                c = cols[idx % 3]
                with c:
                    st.markdown(f"### #{inc['id']} — {inc['title']}")
                    st.write(inc.get("description", ""))
                    if st.button(f"Assign to me #{inc['id']}", key=f"assign_{inc['id']}"):
                        try:
                            ra = requests.post(f"{API}/incidents/{inc['id']}/assign", json={"analyst_email": st.session_state["user_email"]})
                            resa = ra.json()
                            if ra.status_code == 200:
                                st.success(f"Assigned #{inc['id']} to you")
                                st.session_state["incident_id"] = inc["id"]
                                st.session_state["page"] = "incident_detail"; st.rerun()
                            else:
                                st.error(resa.get("detail", "Assignment failed"))
                        except Exception as e:
                            st.error(f"API error: {e}")
        except Exception as e:
            st.error(f"API error: {e}")
        
        st.subheader("📂 My Assigned Tickets")
        try:
            r = requests.get(f"{API}/incidents/assigned", params={"email": st.session_state["user_email"]})
            res = r.json()
            assigned = res.get("assigned_incidents", [])
            cols = st.columns(3)
            for idx, inc in enumerate(assigned):
             c = cols[idx % 3]
             with c:
                st.markdown(f"### #{inc['id']} — {inc['title']}")
                st.caption(f"Group: {inc.get('group')}")
                st.write(inc.get("description", ""))
                st.caption(f"Status: {inc['status']}")
                if st.button(f"Open #{inc['id']}", key=f"open_assigned_{inc['id']}"):
                    st.session_state["incident_id"] = inc["id"]
                    st.session_state["page"] = "incident_detail"; st.rerun()
        except Exception as e:
            st.error(f"API error: {e}")

# Incident detail with prediction
elif st.session_state["page"] == "incident_detail":
    require_login()
    inc_id = st.session_state.get("incident_id")
    if not inc_id:
        st.warning("No incident selected."); st.session_state["page"] = "dashboard"; st.rerun()

    st.title(f"📄 Incident #{inc_id} Details")
    with st.sidebar:
        if st.button("⬅ Dashboard"): st.session_state["page"] = "dashboard"; st.rerun()
        if st.button("🏠 Home"): st.session_state["page"] = "home"; st.rerun()

    try:
        r = requests.get(f"{API}/incident/{inc_id}")
        res = r.json()
        inc = res["incident"]
        journals = res.get("journals", [])

        st.markdown(f"**Title:** {inc['title']}")
        st.markdown(f"**Description:** {inc['description']}")
        st.markdown(f"**Status:** {inc['status']}")
        st.markdown(f"**Group:** {inc.get('group')}")
        st.markdown(f"**Assigned To:** {inc.get('assigned_to') or 'Unassigned'}")

        # Prediction call
        # Type inferred in backend training; you can send a guessed type here as well
        ptype = "General"
        try:
            pr = requests.post(f"{API}/predict_resolution_time", json={
                "title": inc["title"],
                "description": inc["description"],
                "group": inc.get("group") or "Unknown",
                "type": ptype
            })
            pres = pr.json()
            if pr.status_code == 200:
                st.info(f"⏳ Projected Resolution Time: {pres['predicted_resolution_hours']:.1f} hours")
            else:
                st.warning(f"Prediction unavailable: {pres.get('detail')}")
        except Exception as e:
            st.warning(f"Prediction failed: {e}")

        # Timeline
        st.subheader("🕒 Timeline")
        tl = []
        if inc.get("created_at"): tl.append(("Created", inc["created_at"]))
        if inc.get("updated_at"): tl.append(("Updated", inc["updated_at"]))
        if inc.get("closed_at"): tl.append(("Closed", inc["closed_at"]))
        if tl:
            for label, ts in tl: st.markdown(f"- **{label}:** {ts}")
        else:
            st.info("No timeline data available.")

        # Progress bar
        progress_map = {"open": 15, "assigned": 35, "in-progress": 65, "resolved": 85, "closed": 100}
        st.progress(progress_map.get(inc["status"], 25))

        # Journal
        st.subheader("📝 Journal")
        if journals:
            for j in journals:
                st.markdown(f"- {j['created_at']} — **{j['author']}** — {j.get('status') or ''}")
                st.write(j["comment"])
        else:
            st.info("No journal entries yet.")

        # Analyst update
        if st.session_state["role"] == "analyst":
            st.subheader("🔧 Update Status and Add Comment")
            new_status = st.selectbox("New Status", ["assigned", "in-progress", "resolved", "closed"])
            comment = st.text_area("Comment", placeholder="What changed? What did you do?")
            if st.button("Update Incident"):
                try:
                    ru = requests.post(f"{API}/incidents/{inc_id}/update", params={"author_email": st.session_state["user_email"]}, json={"status": new_status, "comment": comment})
                    resu = ru.json()
                    if ru.status_code == 200:
                        st.success("Incident updated"); st.session_state["page"] = "incident_detail"; st.rerun()
                    else:
                        st.error(resu.get("detail", "Update failed"))
                except Exception as e:
                    st.error(f"API error: {e}")

    except Exception as e:
        st.error(f"API error: {e}")
