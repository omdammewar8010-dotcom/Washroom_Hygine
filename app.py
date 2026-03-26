import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import plotly.express as px
import time

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Smart Washroom Dashboard",
    layout="wide",
    page_icon="🚻"
)

# ------------------ FIREBASE INIT ------------------
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred, {
            'databaseURL': st.secrets["firebase"]["databaseURL"]
        })
    return True

init_firebase()

# ------------------ FETCH DATA ------------------
@st.cache_data(ttl=5)  # refresh every 5 sec
def fetch_data():
    try:
        ref = db.reference("/")
        data = ref.get()

        if not data:
            return pd.DataFrame()

        records = []

        for key, value in data.items():

            # Skip cleaning history
            if key == "cleaning_history":
                continue

            if isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, dict):
                        records.append(v)

        return pd.DataFrame(records)

    except Exception as e:
        st.error(f"Firebase Error: {e}")
        return pd.DataFrame()

# ------------------ FETCH CLEANING ------------------
@st.cache_data(ttl=10)
def fetch_cleaning():
    try:
        ref = db.reference("/cleaning_history")
        data = ref.get()

        if data:
            return pd.DataFrame(data.values())
        return pd.DataFrame()

    except:
        return pd.DataFrame()

# ------------------ AUTO REFRESH ------------------
refresh = st.sidebar.slider("🔄 Refresh Rate (sec)", 5, 30, 5)
time.sleep(refresh)

# ------------------ LOAD DATA ------------------
df = fetch_data()
clean_df = fetch_cleaning()

# ------------------ HEADER ------------------
st.title("🚻 Smart Washroom Hygiene Monitoring")
st.caption("Realtime IoT Dashboard using Firebase")

# ------------------ METRICS ------------------
if not df.empty:

    avg_score = round(df["score"].mean(), 2)
    usage = int(df["presence"].sum())
    busy = int((df["status"] == "BUSY").sum())

    c1, c2, c3 = st.columns(3)

    c1.metric("🧼 Avg Score", avg_score)
    c2.metric("🚽 Usage", usage)
    c3.metric("🚻 Busy", busy)

# ------------------ ALERTS ------------------
st.subheader("🚨 Alerts")

if not df.empty:
    alerts = df[df["score"] < 50]

    if len(alerts) > 0:
        st.error(f"{len(alerts)} washrooms need cleaning!")
        st.dataframe(alerts[["washroom_id", "score", "status"]])
    else:
        st.success("All washrooms are clean ✅")

# ------------------ TREND ------------------
st.subheader("📊 Hygiene Score Trend")

if not df.empty:
    df["timestamp"] = pd.to_numeric(df["timestamp"], errors='coerce')

    fig = px.line(df, x="timestamp", y="score", color="washroom_id")
    st.plotly_chart(fig, use_container_width=True)

# ------------------ SENSOR ------------------
st.subheader("🌡 Sensor Data")

if "component_scores" in df:
    sensor_df = pd.json_normalize(df["component_scores"])

    fig2 = px.line(sensor_df)
    st.plotly_chart(fig2, use_container_width=True)

# ------------------ STATUS ------------------
st.subheader("🚻 Status Distribution")

if not df.empty:
    fig3 = px.pie(df, names="status")
    st.plotly_chart(fig3, use_container_width=True)

# ------------------ CLEANING ------------------
st.subheader("🧹 Cleaning History")

if not clean_df.empty:
    st.dataframe(clean_df)
else:
    st.info("No cleaning data")

# ------------------ DOWNLOAD ------------------
if not df.empty:
    st.download_button(
        "📥 Download CSV",
        df.to_csv(index=False),
        "washroom_data.csv"
    )

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("Smart Washroom System 🚀 | Firebase Realtime DB Connected")
