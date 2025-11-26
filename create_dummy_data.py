import pandas as pd

# Create dummy incident data
data = {
    "created_at": pd.date_range("2025-01-01", periods=10, freq="D"),
    "resolved_at": pd.date_range("2025-01-01", periods=10, freq="D") + pd.to_timedelta(range(10), unit="h"),
    "title": [f"Issue {i}" for i in range(10)],
    "description": [f"Description {i}" for i in range(10)],
}
df = pd.DataFrame(data)

# Save to CSV
df.to_csv("incidents_raw.csv", index=False)
print("✅ Dummy incidents_raw.csv created")
