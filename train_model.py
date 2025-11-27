# train_model.py
import math
import joblib
import pandas as pd
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor

from db_config import SessionLocal, Incident, Group

def hours_between(a, b):
    if not a or not b:
        return None
    diff = (b - a).total_seconds() / 3600.0
    return diff if diff >= 0 else None

def fetch_training_data():
    db: Session = SessionLocal()
    try:
        # Use only incidents with a closed_at to compute resolution time
        incidents = db.query(Incident).filter(Incident.closed_at.isnot(None)).all()
        rows = []
        for i in incidents:
            group_name = i.assigned_group.name if i.assigned_group else "Unknown"
            rt_hours = hours_between(i.created_at, i.closed_at)
            if rt_hours is None:
                continue
            rows.append({
                "title": i.title or "",
                "description": i.description or "",
                "group": group_name or "",
                # Optional: derive type. If you have explicit type field, replace this.
                "type": infer_type(i.title, i.description),
                "resolution_time_hours": rt_hours
            })
        return pd.DataFrame(rows)
    finally:
        db.close()

def infer_type(title, description):
    text = f"{title} {description}".lower()
    if "network" in text or "vpn" in text or "wifi" in text:
        return "Network"
    if "server" in text or "database" in text or "db" in text:
        return "Infra"
    if "bug" in text or "error" in text or "ui" in text or "app" in text:
        return "Software"
    return "General"

def main():
    df = fetch_training_data()
    if df.empty:
        print("❌ No closed incidents with resolution times found. Train after you have historical data.")
        return

    X = df[["title", "description", "group", "type"]]
    y = df["resolution_time_hours"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("desc", TfidfVectorizer(max_features=1000), "description"),
            ("title", TfidfVectorizer(max_features=300), "title"),
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["group", "type"]),
        ]
    )

    model = Pipeline([
        ("prep", preprocessor),
        ("reg", RandomForestRegressor(n_estimators=300, random_state=42))
    ])

    model.fit(X, y)
    joblib.dump(model, "resolution_model.pkl")
    print(f"✅ Trained on {len(df)} incidents, saved to resolution_model.pkl")

if __name__ == "__main__":
    main()
