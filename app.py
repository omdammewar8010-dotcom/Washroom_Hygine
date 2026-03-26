import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import plotly.express as px

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Smart Washroom Dashboard",
    layout="wide",
    page_icon="🚻"
)

# ------------------ FIREBASE INIT ------------------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["firebase"]["databaseURL"]
    })

# ------------------ FETCH DATA ------------------
def fetch_data():
    ref = db.reference("/")
    data = ref.get()

    main_data = []
    
    for key, value in data.items():
        if key != "cleaning_history":
            for entry_id, entry in value.items():
                main_data.append(entry)

    return pd.DataFrame(main_data)

def fetch_cleaning():
    ref = db.reference("/cleaning_history")
    data = ref.get()
    if data:
        return pd.DataFrame(data.values())
    return pd.DataFrame()

df = fetch_data()
clean_df = fetch_cleaning()

# ------------------ HEADER ------------------
st.title("🚻 Smart Washroom Hygiene Monitoring System")
st.markdown("Real-time IoT-based cleanliness tracking")

# ------------------ METRICS ------------------
if not df.empty:

    avg_score = round(df["score"].mean(), 2)
    total_usage = df["presence"].sum()
    busy_count = (df["status"] == "BUSY").sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("🧼 Avg Hygiene Score", avg_score)
    col2.metric("🚽 Total Usage", int(total_usage))
    col3.metric("🚻 Busy Count", int(busy_count))

# ------------------ ALERTS ------------------
st.subheader("🚨 Low Hygiene Alerts")

alerts = df[df["score"] < 50]

if not alerts.empty:
    st.error(f"{len(alerts)} Low hygiene events detected!")
    st.dataframe(alerts[["washroom_id", "score", "timestamp"]])
else:
    st.success("✅ All washrooms are clean")

# ------------------ SCORE TREND ------------------
st.subheader("📊 Hygiene Score Trend")

df["timestamp"] = pd.to_numeric(df["timestamp"], errors='coerce')

fig = px.line(df, x="timestamp", y="score", color="washroom_id")
st.plotly_chart(fig, use_container_width=True)

# ------------------ SENSOR ANALYTICS ------------------
st.subheader("🌡️ Sensor Analytics")

sensor_df = pd.json_normalize(df["component_scores"])

fig2 = px.line(sensor_df, title="Sensor Readings")
st.plotly_chart(fig2, use_container_width=True)

# ------------------ STATUS PIE ------------------
st.subheader("🚻 Washroom Status Distribution")

status_fig = px.pie(df, names="status")
st.plotly_chart(status_fig, use_container_width=True)

# ------------------ CLEANING HISTORY ------------------
st.subheader("🧹 Cleaning History")

if not clean_df.empty:
    st.dataframe(clean_df)
else:
    st.info("No cleaning data available")

# ------------------ DOWNLOAD ------------------
st.subheader("📥 Download Data")

csv = df.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV", csv, "washroom_data.csv", "text/csv")

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("Smart Washroom System | Firebase + Streamlit")
