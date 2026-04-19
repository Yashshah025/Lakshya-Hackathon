import streamlit as st
import os
import pandas as pd
import requests
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuration
BACKEND_URL = "http://backend:5000" if os.getenv("DOCKER") else "http://localhost:5000"

st.set_page_config(page_title="CrowdShield - Real-Time Intelligence", layout="wide", page_icon="🛡️")

# Styling
st.markdown("""
<style>
    .main { background-color: #0b0f19; color: #f0f2f6; font-family: 'Inter', sans-serif;}
    .stAlert { border-radius: 8px; }
    .agency-card { 
        padding: 18px; border-radius: 12px; border: 1px solid #1e253c; 
        background-color: #121826; margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .risk-high { border-left: 6px solid #ff2b2b; }
    .risk-warning { border-left: 6px solid #ffb300; }
    .title-glow {
        text-shadow: 0 0 10px rgba(0, 209, 255, 0.5);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='title-glow'>🛡️ CrowdShield: Decision Intelligence</h1>", unsafe_allow_html=True)
st.caption("AI-Powered Temple & Pilgrimage Crowd Crush Prevention System")

# Sidebar Controls code
with st.sidebar:
    st.header("🎮 Scenario Control")
    st.write("Control the flow of the real-time simulation engine.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start", type="primary", use_container_width=True):
            requests.post(f"{BACKEND_URL}/simulation/start")
    with col2:
        if st.button("⏹️ Stop", use_container_width=True):
            requests.post(f"{BACKEND_URL}/simulation/stop")
    
    st.divider()
    st.markdown("### ⚡ Inject Anomalies")
    if st.button("🚌 Trigger Transport Burst (What-If)", use_container_width=True):
        requests.post(f"{BACKEND_URL}/simulation/burst")
        st.toast("Scenario Updated: 20 Buses arriving now!", icon="🚨")

    st.divider()
    st.info("System predicts crowd conditions 8-12 minutes ahead using an XGBoost/RandomForest engine.")

# Data Fetching
def fetch_status():
    try:
        return requests.get(f"{BACKEND_URL}/status").json()
    except:
        return None

def fetch_alerts():
    try:
        return requests.get(f"{BACKEND_URL}/alerts").json()
    except:
        return []

status = fetch_status()
alerts = fetch_alerts()

if status:
    # Top Metrics
    st.markdown("### 📊 Live System Metrics")
    m1, m2, m3, m4 = st.columns(4)
    data = status.get('latest_data') or {}
    
    m1.metric("Live Pressure Index", f"{data.get('pressure_index', 0):.1f}")
    pred = status.get('predicted_pressure', 0)
    m2.metric("Predicted (T+10 min)", f"{pred:.1f}", 
              delta=f"{pred - data.get('pressure_index', 0):.1f}", delta_color="inverse")
    m3.metric("Entry Flow", f"{data.get('entry_rate', 0):.0f} pax/min")
    m4.metric("Capacity Util.", f"{data.get('capacity_utilization', 0)*100:.1f}%")

    st.divider()

    # Main Dashboard Area
    c1, c2 = st.columns([1.8, 1])

    with c1:
        st.subheader("📈 Real-Time Pressure Forecast")
        replay_data = requests.get(f"{BACKEND_URL}/replay").json()
        if replay_data:
            df = pd.DataFrame(replay_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=df['pressure_index'], name='Current Pressure', 
                                     line=dict(color='#00d1ff', width=3), 
                                     fill='tozeroy', fillcolor='rgba(0, 209, 255, 0.1)'))
            fig.add_trace(go.Scatter(y=df['rolling_mean_pressure'], name='Rolling Avg (5m)', 
                                     line=dict(color='#ffa500', dash='dot')))
            
            # Predictor indicator line
            fig.add_hline(y=20, line_dash="dash", line_color="red", annotation_text="HIGH RISK LIMIT")
            fig.add_hline(y=15, line_dash="dash", line_color="orange", annotation_text="WARNING")

            fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=10, b=0),
                              plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Waiting for simulation data... Click 'Start' on the left.")

    with c2:
        st.subheader("🚨 Actionable Alerts")
        if not alerts:
            st.success("✔️ All systems normal. No active alerts.")
        else:
            # We wrap this in a container to simulate a scroll box or limit length
            with st.container():
                # Display only the 4 most recent alerts so it doesn't flood the UI
                for alert in reversed(alerts[-4:]):
                    color_class = "risk-high" if alert['level'] == "HIGH RISK" else "risk-warning"
                    st.markdown(f"""
                    <div class="agency-card {color_class}">
                        <h5 style="margin-top:0px;">{alert['level']} - {alert['type']}</h5>
                        <p style="font-size: 0.9em; color: #888;">Time: {alert['timestamp']} | Pred. Pressure: {alert['predicted_pressure']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for agency, actions in alert['actions'].items():
                        is_ack = alert['acknowledged'].get(agency, False)
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.caption(f"**{agency}**: {actions}")
                        with col_b:
                            if not is_ack:
                                if st.button(f"Ack", key=f"ack_{alert['id']}_{agency}"):
                                    requests.post(f"{BACKEND_URL}/alerts/acknowledge", params={"alert_id": alert['id'], "agency": agency})
                                    st.rerun()
                            else:
                                st.write("✅ Ack'd")
                        st.markdown("<hr style='margin: 4px 0px; opacity: 0.2;'/>", unsafe_allow_html=True)

    # Replay Section
    with st.expander("🎞️ Deep Insights & Post-Event Replay"):
        if replay_data:
            df_replay = pd.DataFrame(replay_data)
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.write("Flow Dynamics (In vs Out)")
                st.line_chart(df_replay[['entry_rate', 'exit_rate']])
            with col_r2:
                st.write("Crowd Density Metrics")
                st.area_chart(df_replay[['capacity_utilization', 'density']])
        else:
            st.write("Run simulation to generate replay data.")

else:
    st.error("Cannot connect to backend. Please ensure services are running.")

# Auto-refresh
time.sleep(2)
st.rerun()
