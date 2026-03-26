"""
Smart Washroom Hygiene Monitoring System
Streamlit Admin Dashboard (Realtime DB Fixed Version)
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import os

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Washroom Hygiene Dashboard",
    page_icon="🚻",
    layout="wide"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    font-weight: bold;
    text-align: center;
    color: #4F46E5;
}
.good {color: #10B981; font-size: 2rem; font-weight: bold;}
.medium {color: #F59E0B; font-size: 2rem; font-weight: bold;}
.bad {color: #EF4444; font-size: 2rem; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ==================== FIREBASE INIT ====================
@st.cache_resource
def init_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        # 🔥 USE SECRETS (Streamlit Cloud) OR LOCAL FILE
        if "firebase" in st.secrets:
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
        else:
            cred = credentials.Certificate("serviceAccountKey.json")

        firebase_admin.initialize_app(cred, {
            # ✅ IMPORTANT: replace if needed
            "databaseURL": "https://smart-washroom-hygiene-s-4af6a-default-rtdb.asia-southeast1.firebasedatabase.app"
        })

    return db.reference()

db_ref = init_firebase()

# ==================== DATA FUNCTIONS ====================
@st.cache_data(ttl=5)
def fetch_all_data():
    try:
        data = db_ref.get()
        return data if data else {}
    except Exception as e:
        st.error(f"Firebase Error: {e}")
        return {}

def get_washrooms(data):
    return list(data.keys())

def get_current(data, washroom):
    wr = data.get(washroom, {})
    return wr.get("current", wr)

# ==================== SCORE LOGIC ====================
def score_class(score):
    if score >= 70:
        return "good"
    elif score >= 50:
        return "medium"
    return "bad"

def predict_score(score, footfall):
    return max(score - (footfall * 0.05), 0)

# ==================== MAIN ====================
def main():

    st.markdown('<div class="main-header">🚻 Smart Washroom Dashboard</div>', unsafe_allow_html=True)

    data = fetch_all_data()

    if not data:
        st.warning("⚠️ No data found in Firebase")
        st.stop()

    washrooms = get_washrooms(data)

    # ================= SIDEBAR =================
    with st.sidebar:
        st.title("⚙️ Controls")

        selected = st.selectbox("Select Washroom", washrooms)

        auto_refresh = st.checkbox("Auto Refresh", True)

        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()

    # ================= CURRENT =================
    st.header(f"📍 {selected}")

    current = get_current(data, selected)

    if not current:
        st.error("No current data available")
        return

    score = current.get("score", 0)
    comp = current.get("component_scores", {})
    anomalies = current.get("anomalies", [])
    footfall = current.get("sensor_data", {}).get("footfall_count", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.write("### Hygiene Score")
        st.markdown(f"<div class='{score_class(score)}'>{score:.1f}%</div>", unsafe_allow_html=True)

    with col2:
        st.metric("Air", comp.get("air_quality", 0))

    with col3:
        st.metric("Floor", comp.get("floor_moisture", 0))

    with col4:
        st.metric("Humidity", comp.get("humidity", 0))

    # ================= PREDICTION =================
    st.subheader("🤖 Prediction")

    predicted = predict_score(score, footfall)

    st.metric("Next Score", f"{predicted:.1f}%")

    if predicted < 50:
        st.error("🚨 Cleaning Required")
    elif predicted < 70:
        st.warning("⚠️ Schedule Cleaning")
    else:
        st.success("✅ Stable")

    # ================= ANOMALIES =================
    if anomalies:
        st.subheader("⚠️ Alerts")
        for a in anomalies:
            st.error(a.get("message", "Unknown"))

    # ================= CHART =================
    st.subheader("📊 Components")

    fig = go.Figure()

    names = ["Air", "Floor", "Humidity", "Temp"]
    vals = [
        comp.get("air_quality", 0),
        comp.get("floor_moisture", 0),
        comp.get("humidity", 0),
        comp.get("temperature", 0),
    ]

    fig.add_bar(x=names, y=vals, text=vals, textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

    # ================= OVERVIEW =================
    st.header("🏢 All Washrooms")

    rows = []

    for w in washrooms:
        c = get_current(data, w)
        rows.append({
            "Washroom": w,
            "Score": c.get("score", 0),
            "Anomalies": len(c.get("anomalies", []))
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    st.metric("Average Score", f"{df['Score'].mean():.1f}%")

    # ================= AUTO REFRESH =================
    if auto_refresh:
        time.sleep(10)
        st.rerun()


# ==================== RUN ====================
if __name__ == "__main__":
    main()
