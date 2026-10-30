import re
import shutil
import subprocess  # nosec B404
import time
from datetime import datetime
from typing import Tuple, Optional

import pandas as pd
import plotly.graph_objects as go
import psutil
import streamlit as st

# ==========================================
# 1. KONFIGURASI & SETUP HALAMAN
# ==========================================
st.set_page_config(
    page_title="NOC Network Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS untuk UI/UX (Dark Theme, Glassmorphism, Metric Cards)
st.markdown(
    """
<style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172aa3; border-right: 1px solid #334155; }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 700 !important; color: #e2e8f0; }
    [data-testid="stMetricDelta"] { font-size: 1rem !important; }
    .status-badge-online {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        background-color: rgba(16, 185, 129, 0.15); color: #10b981;
        font-weight: 600; font-size: 0.9rem; border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .status-badge-offline {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        background-color: rgba(239, 68, 68, 0.15); color: #ef4444;
        font-weight: 600; font-size: 0.9rem; border: 1px solid rgba(239, 68, 68, 0.3);
    }
    hr { border-top: 1px solid #334155; margin: 2rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. INISIALISASI STATE (CACHE SEMENTARA)
# ==========================================
if "history_data" not in st.session_state:
    st.session_state.history_data = pd.DataFrame(columns=["Timestamp", "Target", "Latency", "Status"])

if "prev_net_io" not in st.session_state:
    st.session_state.prev_net_io = psutil.net_io_counters()
    st.session_state.prev_time = time.time()

# Ambil path absolute untuk eksekusi ping di Windows
PING_EXEC = shutil.which("ping") or r"C:\Windows\System32\ping.exe"


# ==========================================
# 3. FUNGSI INTI (CORE LOGIC)
# ==========================================
def ping_host(host: str) -> Tuple[Optional[float], str]:
    """
    Melakukan ping ke target host untuk mengecek status dan latency.
    Aman dari command injection (nosec B603 diabaikan karena argumen berupa list).
    """
    try:
        output = subprocess.check_output(  # nosec B603
            [PING_EXEC, "-n", "1", "-w", "1000", str(host)],
            universal_newlines=True,
            stderr=subprocess.STDOUT,
        )

        match = re.search(r"(?:time|waktu)[=<]\s*([0-9]+)\s*ms", output, re.IGNORECASE)
        
        if match:
            return float(match.group(1)), "ONLINE"
        elif "time<1ms" in output.lower() or "waktu<1ms" in output.lower():
            return 0.5, "ONLINE"
        else:
            return None, "OFFLINE"
            
    except (subprocess.SubprocessError, OSError):
        return None, "OFFLINE"


def get_bandwidth_usage() -> Tuple[float, float]:
    """
    Menghitung selisih byte yang dikirim/diterima untuk mendapatkan
    kecepatan upload dan download real-time dalam satuan Mbps.
    """
    current_io = psutil.net_io_counters()
    current_time = time.time()

    elapsed = current_time - st.session_state.prev_time
    if elapsed == 0:
        elapsed = 1.0

    bytes_sent = current_io.bytes_sent - st.session_state.prev_net_io.bytes_sent
    bytes_recv = current_io.bytes_recv - st.session_state.prev_net_io.bytes_recv

    upload_speed = (bytes_sent * 8) / (1024 * 1024 * elapsed)
    download_speed = (bytes_recv * 8) / (1024 * 1024 * elapsed)

    st.session_state.prev_net_io = current_io
    st.session_state.prev_time = current_time

    return round(upload_speed, 2), round(download_speed, 2)


# ==========================================
# 4. RENDER ANTARMUKA (UI)
# ==========================================

# --- SIDEBAR: Control Panel ---
with st.sidebar:
    st.title("Control Center")
    st.markdown("Atur parameter monitoring di sini.")
    
    st.markdown("### Target Hosts")
    targets_input = st.text_area(
        "Masukkan IP/Domain (pisahkan dengan Enter):",
        value="1.1.1.1\n8.8.8.8\ngoogle.com",
        height=100,
        label_visibility="collapsed"
    )
    target_hosts = [target.strip() for target in targets_input.split("\n") if target.strip()]

    st.markdown("### Polling Rate")
    refresh_rate = st.slider(
        "Interval Pembaruan (detik):", min_value=1, max_value=10, value=2,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    active_interfaces = list(psutil.net_if_addrs().keys())
    if active_interfaces:
        st.info(f"Active Interface:\n{active_interfaces[0]}")


# --- HEADER ---
col_title, col_time = st.columns([3, 1])
with col_title:
    st.title("Enterprise Network Status")
    st.markdown("Real-time ICMP Latency & Throughput Monitoring")
with col_time:
    st.caption("Last Sync:")
    st.subheader(f"{datetime.now().strftime('%H:%M:%S')}")

st.markdown("<hr>", unsafe_allow_html=True)


# --- SECTION 1: Status Card Ping ---
cols = st.columns(len(target_hosts))
current_timestamp = datetime.now().strftime("%H:%M:%S")

for idx, host in enumerate(target_hosts):
    latency, status = ping_host(host)

    new_entry = pd.DataFrame([{
        "Timestamp": current_timestamp,
        "Target": host,
        "Latency": latency if latency is not None else 0,
        "Status": status,
    }])
    st.session_state.history_data = pd.concat([st.session_state.history_data, new_entry], ignore_index=True)

    with cols[idx]:
        with st.container(border=True):
            st.markdown(f"**Host:** `{host}`")
            if status == "ONLINE":
                st.metric(
                    label="Latency",
                    value=f"{latency} ms",
                    delta="Normal" if latency < 100 else "High",
                    delta_color="normal" if latency < 100 else "inverse",
                )
                st.markdown("<div class='status-badge-online'>ONLINE</div>", unsafe_allow_html=True)
            else:
                st.metric(label="Latency", value="ERR", delta="Timeout", delta_color="inverse")
                st.markdown("<div class='status-badge-offline'>OFFLINE</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# --- SECTION 2: Bandwidth Gauge & Latency Chart ---
col_left, col_right = st.columns([1, 2])

with col_left:
    with st.container(border=True):
        st.subheader("Bandwidth Utilization")
        upload_speed, download_speed = get_bandwidth_usage()

        fig_dl = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = download_speed,
            title = {'text': "Download (Mbps)", 'font': {'size': 14}},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#3b82f6"},
                'steps': [
                    {'range': [0, 20], 'color': "rgba(59, 130, 246, 0.1)"},
                    {'range': [20, 80], 'color': "rgba(59, 130, 246, 0.2)"},
                ]
            }
        ))
        fig_dl.update_layout(height=180, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "#f8fafc"})
        st.plotly_chart(fig_dl, use_container_width=True)
        st.markdown(f"**Upload:** `{upload_speed} Mbps`")


with col_right:
    with st.container(border=True):
        st.subheader("Latency Jitter (ms)")

        recent_data = st.session_state.history_data.tail(40)
        fig_lat = go.Figure()
        colors = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6"]
        
        for i, host in enumerate(target_hosts):
            host_df = recent_data[recent_data["Target"] == host]
            fig_lat.add_trace(go.Scatter(
                x=host_df["Timestamp"], y=host_df["Latency"],
                mode="lines+markers", name=host,
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=6)
            ))

        fig_lat.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=300, margin={"l": 10, "r": 10, "t": 10, "b": 10},
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(gridcolor="#334155", title="ms"),
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.05, "xanchor": "right", "x": 1},
            hovermode="x unified"
        )
        st.plotly_chart(fig_lat, use_container_width=True)

# Eksekusi trigger auto-refresh
time.sleep(refresh_rate)
st.rerun()