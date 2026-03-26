"""
Smart Washroom Hygiene Monitoring System
Streamlit Admin Dashboard
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, db, firestore
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="Washroom Hygiene Dashboard",
    page_icon="🚻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .good-score {
        color: #10b981;
        font-weight: bold;
        font-size: 2rem;
    }
    .fair-score {
        color: #f59e0b;
        font-weight: bold;
        font-size: 2rem;
    }
    .poor-score {
        color: #ef4444;
        font-weight: bold;
        font-size: 2rem;
    }
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== FIREBASE INITIALIZATION ====================
@st.cache_resource
def initialize_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        key_path = "[firebase]"
        
        if not os.path.exists(key_path):
            st.error(f"❌ Firebase key not found at: {key_path}")
            st.stop()
        
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://smart-washroom-hygiene-s-4af6a-default-rtdb.firebaseio.com/'
        })
    
    return db.reference(), firestore.client()

realtime_db, firestore_db = initialize_firebase()

# ==================== DATA FETCHING FUNCTIONS ====================
@st.cache_data(ttl=10)
def get_washroom_list():
    try:
        washrooms_ref = realtime_db.child('washrooms')
        washrooms = washrooms_ref.get()
        
        if washrooms:
            return list(washrooms.keys())
        return []
    except Exception as e:
        st.error(f"Error fetching washrooms: {e}")
        return []

@st.cache_data(ttl=5)
def get_current_status(washroom_id):
    try:
        current_ref = realtime_db.child(f'washrooms/{washroom_id}/current')
        data = current_ref.get()
        return data if data else {}
    except Exception as e:
        st.error(f"Error fetching status: {e}")
        return {}

# ==================== AI PREDICTION FUNCTION ====================
def predict_hygiene_drop(current_score, footfall):
    decay_factor = 0.05
    predicted_score = current_score - (footfall * decay_factor)
    return max(predicted_score, 0)

def get_score_color(score):
    if score >= 70:
        return "green"
    elif score >= 50:
        return "orange"
    return "red"

def get_score_class(score):
    if score >= 70:
        return "good-score"
    elif score >= 50:
        return "fair-score"
    return "poor-score"

# ==================== MAIN DASHBOARD ====================
def main():
    
    st.markdown('<h1 class="main-header">🚻 Smart Washroom Hygiene Dashboard</h1>', unsafe_allow_html=True)
    
    # ==================== SIDEBAR ====================
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/200/000000/toilet.png", width=150)
        st.title("Control Panel")
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        
        washroom_list = get_washroom_list()
        
        if not washroom_list:
            st.warning("No washrooms found in database")
            st.stop()
        
        selected_washroom = st.selectbox(
            "Select Washroom",
            washroom_list,
            index=0
        )
        
        st.divider()
        
        time_range = st.selectbox(
            "Historical Data Range",
            ["Last 6 Hours", "Last 12 Hours", "Last 24 Hours", "Last 7 Days"],
            index=2
        )
        
        hours_map = {
            "Last 6 Hours": 6,
            "Last 12 Hours": 12,
            "Last 24 Hours": 24,
            "Last 7 Days": 168
        }
        hours = hours_map[time_range]
        
        st.divider()
        
        auto_refresh = st.checkbox("Auto-refresh (10s)", value=True)
        
        st.divider()
        
        threshold = st.slider("Alert Threshold", 0, 100, 50)
    
    # ==================== CURRENT STATUS ====================
    st.header(f"📊 Current Status: {selected_washroom}")
    
    current_data = get_current_status(selected_washroom)
    
    if current_data:
        score = current_data.get('score', 0)
        component_scores = current_data.get('component_scores', {})
        anomalies = current_data.get('anomalies', [])
        timestamp = current_data.get('timestamp', 'N/A')
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            score_class = get_score_class(score)
            st.markdown(f"### Hygiene Score")
            st.markdown(f'<div class="{score_class}">{score:.1f}%</div>', unsafe_allow_html=True)
            
            if score >= 70:
                st.success("✅ Good")
            elif score >= 50:
                st.warning("⚠️ Fair")
            else:
                st.error("❌ Needs Cleaning")
        
        with col2:
            st.metric("Air Quality", f"{component_scores.get('air_quality', 0):.1f}%")
        
        with col3:
            st.metric("Floor Moisture", f"{component_scores.get('floor_moisture', 0):.1f}%")
        
        with col4:
            st.metric("Humidity", f"{component_scores.get('humidity', 0):.1f}%")
        
        col5, col6, col7 = st.columns(3)
        
        with col5:
            st.metric("Temperature", f"{component_scores.get('temperature', 0):.1f}%")
        
        with col6:
            st.metric("Active Anomalies", len(anomalies))
        
        with col7:
            st.info(f"🕐 Updated: {timestamp}")
        
        # ==================== AI PREDICTION ====================
        st.subheader("🤖 AI Prediction")

        footfall = current_data.get('sensor_data', {}).get('footfall_count', 0)
        predicted_score = predict_hygiene_drop(score, footfall)

        colp1, colp2 = st.columns(2)

        with colp1:
            st.metric("Predicted Score (Next Cycle)", f"{predicted_score:.1f}%")

        with colp2:
            if predicted_score < threshold:
                st.error("⚠️ Cleaning Required Soon")
            else:
                st.success("✅ No Immediate Action Needed")

        if predicted_score < 50:
            st.error("🚨 Immediate Cleaning Required!")
        elif predicted_score < 70:
            st.warning("🧹 Schedule Cleaning Soon")
        else:
            st.success("🟢 Washroom is Stable")

        # ==================== ANOMALIES ====================
        if anomalies:
            st.subheader("⚠️ Active Anomalies")
            for anomaly in anomalies:
                severity = anomaly.get('severity', 'MEDIUM')
                message = anomaly.get('message', 'Unknown anomaly')
                
                if severity == 'HIGH':
                    st.error(f"🔴 {message}")
                elif severity == 'MEDIUM':
                    st.warning(f"🟡 {message}")
                else:
                    st.info(f"🔵 {message}")
        
        # ==================== COMPONENT CHART ====================
        st.subheader("📈 Component Breakdown")
        
        fig_components = go.Figure()
        
        components = ['Air Quality', 'Floor Moisture', 'Humidity', 'Temperature']
        values = [
            component_scores.get('air_quality', 0),
            component_scores.get('floor_moisture', 0),
            component_scores.get('humidity', 0),
            component_scores.get('temperature', 0)
        ]
        colors = [get_score_color(v) for v in values]
        
        fig_components.add_trace(go.Bar(
            x=components,
            y=values,
            marker_color=colors,
            text=[f"{v:.1f}%" for v in values],
            textposition='outside'
        ))
        
        fig_components.update_layout(
            title="Component Scores",
            yaxis_title="Score (%)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_components, use_container_width=True)
        
    else:
        st.warning("No current data available for this washroom")
    
    # ==================== MULTI-WASHROOM OVERVIEW ====================
    st.header("🏢 All Washrooms Overview")
    
    washroom_overview = []
    
    for wr_id in washroom_list:
        data = get_current_status(wr_id)
        if data:
            washroom_overview.append({
                'Washroom': wr_id,
                'Score': data.get('score', 0),
                'Status': '✅ Good' if data.get('score', 0) >= 70 else 
                         '⚠️ Fair' if data.get('score', 0) >= 50 else '❌ Poor',
                'Anomalies': len(data.get('anomalies', []))
            })
    
    if washroom_overview:
        df_overview = pd.DataFrame(washroom_overview)
        
        def highlight_score(val):
            if val >= 70:
                return 'background-color: #d1fae5'
            elif val >= 50:
                return 'background-color: #fef3c7'
            return 'background-color: #fee2e2'
        
        styled_df = df_overview.style.applymap(highlight_score, subset=['Score'])
        
        st.dataframe(styled_df, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_score = df_overview['Score'].mean()
            st.metric("Average Score", f"{avg_score:.1f}%")
        
        with col2:
            good_count = (df_overview['Score'] >= 70).sum()
            st.metric("Good Washrooms", f"{good_count}/{len(df_overview)}")
        
        with col3:
            total_anomalies = df_overview['Anomalies'].sum()
            st.metric("Total Anomalies", total_anomalies)
    
    # ==================== AUTO-REFRESH ====================
    if auto_refresh:
        time.sleep(10)
        st.rerun()

# ==================== RUN APP ====================
if __name__ == "__main__":
    main()
