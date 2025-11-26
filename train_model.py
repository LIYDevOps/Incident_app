import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib

# Example: load your incident data
# Replace with your actual CSV file
df = pd.read_csv("incidents_raw.csv", parse_dates=["created_at", "resolved_at"])

# Create target variable
df["resolution_hours"] = (df["resolved_at"] - df["created_at"]).dt.total_seconds() / 3600
df = df.dropna(subset=["resolution_hours"])

# Simple features
df["hour"] = df["created_at"].dt.hour
df["dayofweek"] = df["created_at"].dt.dayofweek
df["title_len"] = df["title"].fillna("").str.len()

X = df[["hour", "dayofweek", "title_len"]]
y = df["resolution_hours"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save model + feature list in the same folder
joblib.dump(model, "incident_time_model.joblib")
joblib.dump(list(X.columns), "feature_list.joblib")

print("✅ Model saved successfully in F:\\incident_app")
