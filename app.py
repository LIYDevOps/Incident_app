import streamlit as st
import pandas as pd
import joblib
from datetime import datetime

# Load model
model = joblib.load("incident_time_model.joblib")
feature_list = joblib.load("feature_list.joblib")

st.title("Incident Resolution Time Predictor")

# Input fields
title = st.text_input("Issue Title")
description = st.text_area("Issue Description")
category = st.selectbox("Category", ["Network", "Database", "Application", "Security", "Other"])
priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
team = st.selectbox("Team", ["Ops", "DBA", "Dev", "Security", "Unassigned"])
created_at = st.text_input("Created At (YYYY-MM-DD HH:MM)", datetime.now().strftime("%Y-%m-%d %H:%M"))

# Prediction button
if st.button("Predict Resolution Time"):
    row = {
        "created_at": pd.to_datetime(created_at),
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
        "team": team,
    }
    df_single = pd.DataFrame([row])

    # Feature engineering
    df_single["hour"] = df_single["created_at"].dt.hour
    df_single["dayofweek"] = df_single["created_at"].dt.dayofweek
    df_single["month"] = df_single["created_at"].dt.month
    df_single["is_weekend"] = df_single["dayofweek"].isin([5, 6]).astype(int)
    df_single["title_len"] = df_single["title"].str.len()
    df_single["desc_len"] = df_single["description"].str.len()

    X = df_single[[c for c in feature_list if c in df_single.columns]]
    pred_hours = float(model.predict(X)[0])

    st.success(f"Predicted resolution time: {pred_hours:.2f} hours")
