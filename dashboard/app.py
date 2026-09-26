import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st




# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="QuantumProtect | Post-Quantum Secure Smart Energy",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ==============================================================================
# SHINY SILVER THEME
# Palette: #A8A9AD · #B5B7BB · #CCCCCC · #D8D8D8 · #757575 · #AFB1AE
# ==============================================================================

CUSTOM_CSS = """
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

<style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap'
    );

    /* ================================================================ */
    /* GLOBAL                                                           */
    /* ================================================================ */
    html { overflow-y: scroll !important; }

    html, body, [class*="css"] {
        font-family: 'JetBrains Mono', monospace !important;
    }

    .stApp {
        background-color: #DDE0E5 !important;
        color: #0F172A !important;
    }

    /* ================================================================ */
    /* HEADER / TOOLBAR                                                 */
    /* ================================================================ */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        border-bottom: none !important;
    }
    [data-testid="stToolbar"] { visibility: hidden !important; }

    /* ================================================================ */
    /* SIDEBAR – hidden                                                 */
    /* ================================================================ */
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    button[aria-label="Close sidebar"],
    button[aria-label="Open sidebar"] { display: none !important; }

    /* ================================================================ */
    /* MAIN CONTAINER                                                   */
    /* ================================================================ */
    .stMain, [data-testid="stMain"], section.main {
        margin-left: 0 !important;
        width: 100% !important;
    }
    .block-container {
        padding-top: 1.0rem !important;
        padding-bottom: 3.0rem !important;
        padding-left: 2.4rem !important;
        padding-right: 2.4rem !important;
        max-width: 100% !important;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 10px !important;
    }
    div[data-testid="stElementContainer"] {
        margin-bottom: 0 !important;
    }

    /* ================================================================ */
    /* TOP NAVIGATION BAR                                               */
    /* ================================================================ */
    .top-nav-bar {
        background: #FFFFFF;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 50px;
        padding: 5px 6px;
        margin: 0 auto 16px auto;
        width: fit-content;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.05);
    }
    .nav-brand {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        text-decoration: none !important;
        padding-right: 12px;
        border-right: 1px solid rgba(0, 0, 0, 0.09);
        cursor: pointer;
    }
    .nav-links { display: flex; align-items: center; gap: 8px; }
    .nav-link-item {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 8px 20px;
        border-radius: 25px;
        color: #64748B;
        text-decoration: none;
        font-size: 0.88rem;
        font-weight: 500;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }
    .nav-link-item i { font-size: 0.95rem; }
    .nav-link-item:hover {
        background: #F1F5F9;
        color: #0F172A;
        text-decoration: none;
    }
    .nav-link-item.active {
        background: #0F172A;
        color: #FFFFFF;
        border: 1px solid #0F172A;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.15);
    }

    /* ================================================================ */
    /* TOP HEADER CARD                                                  */
    /* ================================================================ */
    .top-header-card {
        background-color: #FFFFFF;
        border: 1px solid rgba(0, 0, 0, 0.07);
        border-radius: 16px;
        padding: 20px 26px;
        margin-bottom: 8px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
    }
    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }
    .header-left { display: flex; align-items: center; gap: 16px; }
    .header-icon-box {
        width: 48px; height: 48px;
        border-radius: 12px;
        background: #FEF3C7;
        border: 1px solid #FCD34D;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.5rem; color: #D97706;
    }
    .header-title-group h1 {
        font-size: 1.65rem; font-weight: 700;
        color: #0F172A;
        margin: 0; line-height: 1.2;
        letter-spacing: -0.02em;
        font-family: 'Inter', sans-serif;
    }
    .header-title-group p {
        font-size: 0.88rem;
        color: #64748B;
        margin: 4px 0 0 0;
        letter-spacing: 0.01em; font-weight: 400;
    }
    .header-right { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

    /* ================================================================ */
    /* STATUS BADGES                                                    */
    /* ================================================================ */
    .status-badge {
        display: inline-flex; align-items: center; gap: 7px;
        padding: 7px 16px; border-radius: 20px;
        font-size: 0.82rem; font-weight: 600;
        letter-spacing: 0.01em; border: 1px solid;
        transition: all 0.2s ease;
    }
    .status-badge.live    { background: #DCFCE7; color: #15803D; border-color: #86EFAC; }
    .status-badge.waiting { background: #FEF3C7; color: #B45309; border-color: #FCD34D; }
    .status-badge.meter   { background: #EDE9FE; color: #6D28D9; border-color: #C4B5FD; }
    .status-badge.disconnected { background: #FEE2E2; color: #B91C1C; border-color: #FCA5A5; }
        .badge-pill {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 4px 12px; border-radius: 20px;
        font-size: 0.76rem; font-weight: 600;
        letter-spacing: 0.02em; border: 1px solid;
    }
    .badge-pill.pill-live {
        background: #DCFCE7;
        color: #15803D;
        border-color: #86EFAC;
    }
    .badge-pill.pill-stale {
        background: #FEF3C7;
        color: #B45309;
        border-color: #FCD34D;
    }

    .status-badge.timestamp {
        background: #F1F5F9;
        color: #475569;
        border-color: #CBD5E1;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
    }

    /* ================================================================ */
    /* KPI / CARD PANELS                                                */
    /* ================================================================ */
    .card-panel, .kpi-container {
        overflow: hidden !important;
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }
    .card-panel::-webkit-scrollbar,
    .kpi-container::-webkit-scrollbar { display: none !important; width: 0 !important; height: 0 !important; }

    .kpi-container {
        background-color: #FFFFFF;
        border: 1px solid rgba(0, 0, 0, 0.07);
        border-radius: 16px;
        padding: 22px 24px;
        min-height: 154px;
        display: flex; flex-direction: column; justify-content: space-between;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
        margin-bottom: 8px;
    }
    .kpi-container:hover {
        box-shadow: 0 8px 26px -4px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
    }
    .kpi-top { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
    .kpi-icon-circle {
        width: 38px; height: 38px; border-radius: 50%;
        background: #F1F5F9;
        border: 1px solid #E2E8F0;
        display: flex; align-items: center; justify-content: center;
        color: #334155; font-size: 1.05rem; flex-shrink: 0;
    }
    .kpi-label {
        font-size: 0.74rem; font-weight: 700;
        letter-spacing: 0.06em; text-transform: uppercase;
        color: #64748B;
    }
    .kpi-value-row { display: flex; align-items: baseline; gap: 6px; margin: 2px 0 6px 0; }
    .kpi-value {
        font-size: 2.05rem; font-weight: 700;
        color: #0F172A;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.02em; line-height: 1.1;
    }
    .kpi-unit-clean { font-size: 0.95rem; font-weight: 500; color: #64748B; margin-left: 2px; }
    .kpi-delta { font-size: 0.74rem; color: #64748B; display: flex; align-items: center; gap: 5px; }
    .delta-green { color: #16A34A; font-weight: 600; }
    .delta-red   { color: #DC2626; font-weight: 600; }

    /* ================================================================ */
    /* SECTION TITLES                                                   */
    /* ================================================================ */
    .section-header-title {
        font-size: 0.78rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.08em;
        color: #475569;
        display: flex; align-items: center; gap: 8px;
        margin-bottom: 14px; margin-top: 4px;
    }

    /* ================================================================ */
    /* PLOTLY CONTAINER                                                 */
    /* ================================================================ */
    div[data-testid="stPlotlyChart"] {
        background-color: #FFFFFF !important;
        border: 1px solid rgba(0, 0, 0, 0.07) !important;
        border-radius: 16px !important;
        padding: 14px 16px 20px 16px !important;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 10px !important;
        overflow: hidden !important;
    }

    .card-panel-top {
        background-color: #FFFFFF !important;
        border: 1px solid rgba(0, 0, 0, 0.07) !important;
        border-bottom: none !important;
        border-top-left-radius: 16px !important;
        border-top-right-radius: 16px !important;
        border-bottom-left-radius: 0px !important;
        border-bottom-right-radius: 0px !important;
        padding: 0 !important;
        box-shadow: 0 2px 10px -2px rgba(0, 0, 0, 0.03) !important;
        margin-bottom: 0px !important;
    }

    div[data-testid="stElementContainer"]:has(.card-panel-top) + div[data-testid="stElementContainer"] div[data-testid="stPlotlyChart"] {
        border-top-left-radius: 0px !important;
        border-top-right-radius: 0px !important;
        border-top: none !important;
        margin-top: 0px !important;
        box-shadow: 0 8px 20px -2px rgba(0, 0, 0, 0.05) !important;
    }

    /* ================================================================ */
    /* GENERIC CARD PANEL                                               */
    /* ================================================================ */
    .card-panel {
        background-color: #FFFFFF;
        border: 1px solid rgba(0, 0, 0, 0.07);
        border-radius: 16px;
        padding: 22px 24px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
        margin-bottom: 22px;
    }
    .card-panel-title {
        font-size: 0.92rem; font-weight: 700;
        color: #0F172A;
        margin-bottom: 14px;
        display: flex; justify-content: space-between; align-items: center;
    }

    /* ================================================================ */
    /* STATUS ROWS                                                      */
    /* ================================================================ */
    .status-row { margin-bottom: 12px; }
    .status-row:last-child { margin-bottom: 0; }
    .status-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 2px;
    }
    .status-value {
        font-size: 0.85rem;
        font-weight: 600;
        color: #0F172A;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ================================================================ */
    /* PIPELINE NODES                                                   */
    /* ================================================================ */
    .pipeline-grid { display: flex; align-items: center; justify-content: space-between; gap: 8px; width: 100%; }
    .pipeline-node {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px; padding: 12px; flex: 1;
        min-width: 88px; display: flex; flex-direction: column;
        justify-content: space-between; height: 82px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .node-title { font-size: 0.72rem; font-weight: 600; color: #0F172A; line-height: 1.3; }
    .node-status-row { display: flex; align-items: center; gap: 4px; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; }
    .node-arrow { color: #94A3B8; font-size: 0.9rem; padding: 0 2px; }

    /* ================================================================ */
    /* SPEC GRID                                                        */
    /* ================================================================ */
    .spec-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 16px; }
    .spec-col { display: flex; flex-direction: column; gap: 4px; }
    .spec-item-label { font-size: 0.70rem; color: #64748B; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; }
    .spec-item-value { font-size: 0.85rem; font-weight: 600; color: #0F172A; line-height: 1.35; }

    /* ================================================================ */
    /* STATUS DOTS                                                      */
    /* ================================================================ */
    .dot-green  { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #16A34A; box-shadow: 0 0 6px rgba(22,163,74,0.45); margin-right: 5px; }
    .dot-amber  { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #D97706; margin-right: 5px; }
    .dot-purple { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #7C3AED; margin-right: 5px; }

    /* ================================================================ */
    /* EXPANDER                                                         */
    /* ================================================================ */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border: 1px solid rgba(0, 0, 0, 0.07) !important;
        border-radius: 12px !important;
        color: #0F172A !important;
        font-weight: 600 !important;
    }

    /* ================================================================ */
    /* DOWNLOAD BUTTON                                                  */
    /* ================================================================ */
    .stDownloadButton button {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
        padding: 9px 18px !important;
        transition: all 0.2s ease !important;
    }
    .stDownloadButton button:hover {
        background-color: #E2E8F0 !important;
        border-color: #94A3B8 !important;
        color: #000000 !important;
    }

    /* ================================================================ */
    /* STREAMLIT NATIVE WIDGETS                                        */
    /* ================================================================ */
    [data-testid="stCheckbox"] label,
    [data-testid="stSlider"] label,
    .stMarkdown p,
    [class*="stText"] {
        color: #0F172A !important;
        font-weight: 500 !important;
    }
    [data-testid="stButton"] > button {
        background: #0F172A !important;
        color: #FFFFFF !important;
        border: 1px solid #0F172A !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stButton"] > button:hover {
        background: #1E293B !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.2) !important;
    }

</style>
"""


# Inject CSS
st.html(CUSTOM_CSS)


# ==============================================================================
# TELEMETRY INGESTION
# ==============================================================================
def get_readings_file_path() -> Path:
    """Return the resolved path to server/readings.json."""
    return (
        Path(__file__).resolve().parent.parent
        / "server"
        / "readings.json"
    )


def load_readings(
    max_retries: int = 3,
    retry_delay: float = 0.1
) -> list:
    """
    Safely load telemetry from server/readings.json.

    Handles:
    - missing file
    - empty file
    - partial JSON during concurrent writes
    - permission / OS access problems
    """
    file_path = get_readings_file_path()

    if not file_path.exists():
        return []

    for attempt in range(max_retries):

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read().strip()

            if not content:
                return []

            data = json.loads(content)

            if isinstance(data, list):
                return data

            return []

        except (
            json.JSONDecodeError,
            OSError,
            PermissionError
        ):

            if attempt < max_retries - 1:
                time.sleep(retry_delay)

    return []


# ==============================================================================
# SAFE NUMBER HELPER
# ==============================================================================
def safe_float(value, default: float = 0.0) -> float:
    """Convert a value to float without crashing the dashboard."""
    try:

        result = float(value)

        if pd.isna(result):
            return default

        return result

    except (
        TypeError,
        ValueError
    ):

        return default


# ==============================================================================
# QUERY PARAMETER / PAGE ROUTING
# ==============================================================================
query_page = st.query_params.get(
    "page",
    "Dashboard"
)

valid_pages = [
    "Dashboard",
    "Security",
]

current_page = (
    query_page
    if query_page in valid_pages
    else "Dashboard"
)


# ==============================================================================
# HORIZONTAL NAVIGATION BAR
# ==============================================================================

# Initialize default values for refresh controls
auto_refresh = True
refresh_interval = 3

# Build navigation HTML
nav_items = [
    ("Dashboard", "fa-solid fa-house"),
    ("Security", "fa-solid fa-shield-halved"),
]

nav_links_html = ""
for page_name, page_icon in nav_items:
    active_class = "active" if current_page == page_name else ""
    nav_links_html += f'''
        <a href="?page={page_name}"
           target="_self"
           class="nav-link-item {active_class}">
            <i class="{page_icon}"></i>
            <span>{page_name}</span>
        </a>
    '''

st.html(
    f"""
    <div class="top-nav-bar">
        <div class="nav-links">
            {nav_links_html}
        </div>
    </div>
    """
)


# ==============================================================================
# LOAD TELEMETRY
# ==============================================================================
raw_readings = load_readings()

total_count = len(raw_readings)

now = datetime.now()

STALE_THRESHOLD_SECONDS = 15.0


# ==============================================================================
# TELEMETRY STATUS
# ==============================================================================
if not raw_readings:

    telemetry_status = "WAITING"

    status_pill_html = (
        '<span class="badge-pill pill-stale">'
        '<span class="dot-amber"></span>'
        ' WAITING'
        '</span>'
    )

    age_str = "No telemetry received"

    age_seconds = None

    meter_id = "SM001"

    latest_ts_str = "N/A"

else:

    # --------------------------------------------------------------------------
    # MOST RECENTLY RECEIVED PACKET
    #
    # IMPORTANT:
    # Do not sort raw_readings by timestamp here.
    #
    # The Smart Meter can restart and generate timestamps that are older
    # than previously stored records. Arrival order is therefore the source
    # of truth for the current packet.
    # --------------------------------------------------------------------------

    latest_record = raw_readings[-1]

    latest_ts = str(
        latest_record.get(
            "timestamp",
            "N/A"
        )
    )

    meter_id = str(
        latest_record.get(
            "meter_id",
            "SM001"
        )
    )


    # --------------------------------------------------------------------------
    # DISPLAY PACKET TIMESTAMP
    # --------------------------------------------------------------------------
    try:

        last_dt = pd.to_datetime(
            latest_ts,
            errors="coerce"
        )

        if pd.isna(last_dt):
            raise ValueError(
                "Invalid telemetry timestamp"
            )

        latest_ts_str = last_dt.strftime(
            "%a, %d %b %Y\n%I:%M:%S %p"
        )

    except Exception:

        latest_ts_str = "Timestamp unavailable"


    # --------------------------------------------------------------------------
    # FILE MODIFICATION TIME
    #
    # This is used to determine whether telemetry is actually arriving.
    # It is more reliable than the embedded packet timestamp.
    # --------------------------------------------------------------------------
    try:

        file_mtime = get_readings_file_path().stat().st_mtime

        age_seconds = max(
            0.0,
            time.time() - file_mtime
        )

    except OSError:

        age_seconds = None


    # --------------------------------------------------------------------------
    # HUMAN-READABLE FRESHNESS
    # --------------------------------------------------------------------------
    if age_seconds is None:

        age_str = "N/A"

    elif age_seconds < 60:

        age_str = f"{int(age_seconds)}s ago"

    elif age_seconds < 3600:

        age_str = (
            f"{int(age_seconds // 60)}m ago"
        )

    else:

        age_str = (
            f"{int(age_seconds // 3600)}h ago"
        )


    # --------------------------------------------------------------------------
    # LIVE / STALE STATUS
    # --------------------------------------------------------------------------
    if (
        age_seconds is not None
        and age_seconds <= STALE_THRESHOLD_SECONDS
    ):

        telemetry_status = "LIVE / ACTIVE"

        status_pill_html = (
            '<span class="badge-pill pill-live">'
            '<span class="dot-green"></span>'
            ' LIVE / ACTIVE'
            '</span>'
        )

    else:

        telemetry_status = "STALE"

        status_pill_html = (
            '<span class="badge-pill pill-stale">'
            '<span class="dot-amber"></span>'
            ' STALE'
            '</span>'
        )


# ==============================================================================
# TOP COCKPIT HEADER
# ==============================================================================
header_timestamp = now.strftime(
    "%I:%M:%S %p"
)

# Determine status badge class and text
if telemetry_status == "LIVE / ACTIVE":
    status_class = "live"
    status_text = "Live"
    status_dot = '<span class="dot-green"></span>'
elif telemetry_status == "WAITING":
    status_class = "waiting"
    status_text = "Waiting"
    status_dot = '<span class="dot-amber"></span>'
else:
    status_class = "waiting"
    status_text = "Simulated"
    status_dot = '<span class="dot-amber"></span>'


st.html(
    f"""
    <div class="top-header-card">
        <div class="top-header">

            <div class="header-left" style="align-items: center; gap: 18px;">

                <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxNzAgMTcwIiBmaWxsPSJub25lIj48ZWxsaXBzZSBjeD0iODAiIGN5PSI4MCIgcng9IjcyIiByeT0iMjYiIHN0cm9rZT0iIzU0NjU1QiIgc3Ryb2tlLXdpZHRoPSI1LjUiIHRyYW5zZm9ybT0icm90YXRlKC0yNiA4MCA4MCkiIC8+PGNpcmNsZSBjeD0iMTI4IiBjeT0iNDIiIHI9IjgiIGZpbGw9IiM1NDY1NUIiIC8+PGNpcmNsZSBjeD0iODAiIGN5PSI4MCIgcj0iNDYiIHN0cm9rZT0iIzE5MjAyNCIgc3Ryb2tlLXdpZHRoPSIxNiIgZmlsbD0ibm9uZSIgLz48bGluZSB4MT0iNjQiIHkxPSI2NCIgeDI9IjExNCIgeTI9IjExNCIgc3Ryb2tlPSIjMTkyMDI0IiBzdHJva2Utd2lkdGg9IjE2IiBzdHJva2UtbGluZWNhcD0ic3F1YXJlIiAvPjwvc3ZnPg=="
                     width="72" height="72" style="flex-shrink:0;" alt="QuantumProtect" />

                <div class="header-title-group" style="display: flex; flex-direction: column; justify-content: center;">

                    <div style="display: flex; align-items: baseline; font-family: 'Inter', sans-serif; line-height: 1.1;">
                        <span style="font-size: 2.1rem; font-weight: 400; color: #161B22; letter-spacing: -0.02em;">Quantum</span>
                        <span style="font-size: 2.1rem; font-weight: 800; color: #161B22; letter-spacing: -0.02em;">Protect</span>
                    </div>

                    <div style="font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 700; color: #4B5C52; letter-spacing: 0.24em; text-transform: uppercase; margin-top: 4px;">
                        POST-QUANTUM SECURE SMART ENERGY
                    </div>

                </div>

            </div>


            <div class="header-right">

                <div class="status-badge {status_class}">
                    {status_dot}
                    {status_text}
                </div>

                <div class="status-badge meter">
                    <i class="fa-solid fa-microchip" style="font-size:0.85rem;"></i>
                    Meter: {meter_id}
                </div>

                <div class="status-badge timestamp">
                    {header_timestamp}
                </div>

            </div>

        </div>
    </div>
    """
)


# ==============================================================================
# STAGED PAGE ROUTING
# ==============================================================================
if current_page != "Dashboard":

    # ------------------------------------------------------------------
    # SECURITY PAGE  –  full ML-KEM-512 demonstration
    # ------------------------------------------------------------------
    if current_page == "Security":
        import base64 as _b64
        import os as _os
        from pathlib import Path as _Path
        import sys as _sys

        _PROJECT_ROOT = _Path(__file__).resolve().parents[1]
        if str(_PROJECT_ROOT) not in _sys.path:
            _sys.path.insert(0, str(_PROJECT_ROOT))

        # ---- load handshake session ----
        _HANDSHAKE_FILE = _PROJECT_ROOT / "server" / "mlkem_handshake_session.json"
        _hs = None
        if _HANDSHAKE_FILE.exists():
            try:
                with open(_HANDSHAKE_FILE, "r", encoding="utf-8") as _f:
                    _hs = json.load(_f)
            except Exception:
                _hs = None

        _has_handshake_data = _hs is not None and "wire_artifacts" in (_hs or {})
        _is_live_session = _has_handshake_data and (telemetry_status == "LIVE / ACTIVE")

        if _has_handshake_data:
            _artifacts = _hs["wire_artifacts"]
            _specs     = _hs.get("security_specs", {})
            _pk_b64    = _artifacts.get("public_key_b64", "")
            _ct_b64    = _artifacts.get("ciphertext_b64", "")
            _pk_len    = _artifacts.get("public_key_bytes_len", 800)
            _ct_len    = _artifacts.get("ciphertext_bytes_len", 768)
            _ss_len    = _specs.get("shared_secret_size_bytes", 32)
            _sk_len    = _specs.get("secret_key_size_bytes", 1632)
            _alg       = _hs.get("algorithm", "ML-KEM-512")
            _std       = _hs.get("pqc_standard", "NIST FIPS 203")
            _ts        = _hs.get("session_established_at", "Unknown")
            _host      = _hs.get("server_host", "192.168.2.1")
            _port      = _hs.get("server_port", 5000)
            _pk_snippet = _pk_b64[:48] + "..."
            _ct_snippet = _ct_b64[:48] + "..."
        else:
            _pk_len = 800; _ct_len = 768; _ss_len = 32; _sk_len = 1632
            _alg = "ML-KEM-512"; _std = "NIST FIPS 203"
            _ts = "Session not captured yet"; _host = "192.168.2.1"; _port = 5000
            _pk_snippet = "(run server to capture real key)"
            _ct_snippet = "(run server to capture real ciphertext)"

        # ---- run cryptographic validation ----
        _val_secret_nonexposure = False
        _val_invalid_tag        = False
        _val_secret_match       = False
        _val_error              = None
        try:
            from crypto.mlkem import generate_keys as _gk, encapsulate as _enc, decapsulate as _dec
            from crypto.secure_data import encrypt_data as _edata, decrypt_data as _ddata
            from cryptography.exceptions import InvalidTag as _IT

            _pk_v, _sk_v  = _gk()
            _ct_v, _ss_m  = _enc(_pk_v)
            _ss_s         = _dec(_sk_v, _ct_v)

            # secret not in public wire data
            _val_secret_nonexposure = (
                _ss_m not in _pk_v and
                _ss_m not in _ct_v
            )

            # adversary with random key cannot decrypt
            _adv_key   = _os.urandom(32)
            _enc_data  = _edata(_ss_m, {"meter_id": "SM001", "payload": "demo"}, "json")
            try:
                _ddata(_adv_key, _enc_data, "json")
            except _IT:
                _val_invalid_tag = True

            # legitimate server matches secret
            _val_secret_match = (_ss_s == _ss_m)

        except Exception as _e:
            _val_error = str(_e)

        _all_pass = _val_secret_nonexposure and _val_invalid_tag and _val_secret_match

        # ---- helper: badge HTML ----
        def _vbadge(ok, label):
            if ok:
                return (f'<span style="display:inline-flex;align-items:center;gap:6px;'
                        f'background:#DCFCE7;color:#15803D;border:1px solid #86EFAC;'
                        f'padding:5px 14px;border-radius:20px;font-size:0.79rem;font-weight:700;'
                        f'letter-spacing:0.04em;">'
                        f'<i class="fa-solid fa-circle-check"></i> {label} PASS</span>')
            else:
                return (f'<span style="display:inline-flex;align-items:center;gap:6px;'
                        f'background:#FEE2E2;color:#B91C1C;border:1px solid #FCA5A5;'
                        f'padding:5px 14px;border-radius:20px;font-size:0.79rem;font-weight:700;'
                        f'letter-spacing:0.04em;">'
                        f'<i class="fa-solid fa-circle-xmark"></i> {label} FAIL</span>')

        # ---- session source badge & title ----
        if _is_live_session:
            _session_title = "Live Handshake Session"
            _src_badge = (
                '<span style="background:#DCFCE7;color:#15803D;border:1px solid #86EFAC;'
                'padding:4px 12px;border-radius:20px;font-size:0.76rem;font-weight:700;'
                'display:inline-flex;align-items:center;gap:6px;">'
                '<i class="fa-solid fa-circle" style="font-size:0.6rem;color:#16A34A;"></i> Live Session</span>'
            )
            _validation_title = "Cryptographic Validation &mdash; Live Test"
            _banner_html = ""
        else:
            _session_title = "Last Recorded Handshake"
            _src_badge = (
                '<span style="background:#FEF3C7;color:#B45309;border:1px solid #FCD34D;'
                'padding:4px 12px;border-radius:20px;font-size:0.76rem;font-weight:700;'
                'display:inline-flex;align-items:center;gap:6px;">'
                '<i class="fa-solid fa-circle-pause" style="font-size:0.7rem;color:#D97706;"></i> No Active Session</span>'
            )
            _validation_title = "Cryptographic Validation &mdash; Last Test"
            _banner_html = f"""
            <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;padding:12px 18px;margin-bottom:16px;display:flex;align-items:center;gap:12px;">
                <i class="fa-solid fa-clock-rotate-left" style="color:#D97706;font-size:1.1rem;"></i>
                <div style="font-size:0.80rem;color:#92400E;">
                    <span style="font-weight:700;">Historical Evidence:</span> Displaying security artifacts from the last completed PYNQ-Z2 &harr; Server session (Timestamp: <code style="background:#FEF3C7;padding:1px 5px;border-radius:4px;color:#78350F;">{_ts[:19] if len(_ts) > 10 else _ts}</code>). Telemetry feed is currently offline.
                </div>
            </div>
            """

        _overall_badge = (
            '<span style="background:#DCFCE7;color:#15803D;border:1px solid #86EFAC;'
            'padding:6px 18px;border-radius:20px;font-size:0.82rem;font-weight:700;">'
            '<i class="fa-solid fa-shield-check"></i>&nbsp; ALL CHECKS PASSED</span>'
        ) if _all_pass else (
            '<span style="background:#FEE2E2;color:#B91C1C;border:1px solid #FCA5A5;'
            'padding:6px 18px;border-radius:20px;font-size:0.82rem;font-weight:700;">'
            '<i class="fa-solid fa-triangle-exclamation"></i>&nbsp; VALIDATION INCOMPLETE</span>'
        )

        # ============================================================
        # RENDER
        # ============================================================

        # --- Section header
        st.html(f"""
        <div style="margin-bottom:24px;">
            <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px;">
                <div style="width:44px;height:44px;border-radius:12px;
                            background:#EDE9FE;border:1px solid #C4B5FD;
                            display:flex;align-items:center;justify-content:center;">
                    <i class="fa-solid fa-shield-halved" style="color:#6D28D9;font-size:1.3rem;"></i>
                </div>
                <div>
                    <h2 style="margin:0;font-size:1.45rem;font-weight:700;
                               color:#0F172A;font-family:'Inter',sans-serif;">Security Demonstrations</h2>
                    <p style="margin:2px 0 0 0;font-size:0.84rem;color:#64748B;">
                        Scenario 2 &mdash; ML-KEM-512 Post-Quantum Key Interception Resistance
                    </p>
                </div>
            </div>
        </div>
        {_banner_html}
        """)

        # --- Session meta card
        st.html(f"""
        <div class="card-panel" style="margin-bottom:20px;padding:18px 24px;">
            <div style="display:flex;justify-content:space-between;align-items:center;
                        flex-wrap:wrap;gap:12px;margin-bottom:14px;">
                <span class="section-header-title" style="margin:0;">
                    <i class="fa-solid fa-tower-broadcast" style="color:#6D28D9;"></i>
                    {_session_title}
                </span>
                {_src_badge}
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:16px;">
                <div>
                    <div class="spec-item-label">Algorithm</div>
                    <div class="spec-item-value">{_alg}</div>
                </div>
                <div>
                    <div class="spec-item-label">Standard</div>
                    <div class="spec-item-value">{_std}</div>
                </div>
                <div>
                    <div class="spec-item-label">Endpoint</div>
                    <div class="spec-item-value">{_host}:{_port}</div>
                </div>
                <div>
                    <div class="spec-item-label">Recorded At</div>
                    <div class="spec-item-value" style="font-size:0.78rem;">{_ts[:19] if len(_ts) > 10 else _ts}</div>
                </div>
            </div>
        </div>
        """)

        # --- Handshake flow visual
        st.html(f"""
        <div class="card-panel" style="margin-bottom:20px;">
            <div class="card-panel-title">
                <span><i class="fa-solid fa-diagram-project" style="color:#6D28D9;margin-right:8px;"></i>PYNQ-Z2 &harr; Utility Server &mdash; ML-KEM Handshake Flow</span>
            </div>

            <!-- PYNQ box -->
            <div style="display:flex;align-items:stretch;gap:0;position:relative;">

                <!-- Left node: PYNQ-Z2 -->
                <div style="flex:1;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                            padding:18px 16px;display:flex;flex-direction:column;align-items:center;
                            gap:8px;min-width:110px;">
                    <i class="fa-solid fa-microchip" style="font-size:1.6rem;color:#6D28D9;"></i>
                    <div style="font-size:0.80rem;font-weight:700;color:#0F172A;">PYNQ-Z2</div>
                    <div style="font-size:0.71rem;color:#64748B;">Smart Meter</div>
                    <div style="font-size:0.71rem;color:#64748B;">192.168.2.99</div>
                </div>

                <!-- Arrows column -->
                <div style="flex:3;display:flex;flex-direction:column;justify-content:space-around;
                            padding:8px 18px;gap:10px;">

                    <!-- Frame 1: Server -> PYNQ (pk) -->
                    <div style="background:#EDE9FE;border:1px solid #C4B5FD;border-radius:10px;
                                padding:12px 16px;">
                        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                            <span style="font-size:0.72rem;font-weight:700;color:#6D28D9;
                                         background:#F5F3FF;padding:3px 10px;border-radius:20px;
                                         border:1px solid #DDD6FE;">Frame 1 &rarr;</span>
                            <span style="font-size:0.78rem;font-weight:600;color:#1E1B4B;">Server &rarr; PYNQ-Z2</span>
                            <span style="font-size:0.72rem;color:#64748B;font-family:'JetBrains Mono',monospace;">[mlkem_public_key]</span>
                        </div>
                        <div style="margin-top:8px;display:flex;gap:18px;flex-wrap:wrap;">
                            <div>
                                <div class="spec-item-label">Size (raw bytes)</div>
                                <div style="font-size:1.05rem;font-weight:700;color:#6D28D9;">{_pk_len} B</div>
                            </div>
                            <div style="flex:1;min-width:0;">
                                <div class="spec-item-label">Wire snippet</div>
                                <div style="font-size:0.71rem;color:#475569;font-family:'JetBrains Mono',monospace;
                                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{_pk_snippet}</div>
                            </div>
                        </div>
                    </div>

                    <!-- Frame 2: PYNQ -> Server (ct) -->
                    <div style="background:#F0F9FF;border:1px solid #BAE6FD;border-radius:10px;
                                padding:12px 16px;">
                        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                            <span style="font-size:0.72rem;font-weight:700;color:#0284C7;
                                         background:#E0F2FE;padding:3px 10px;border-radius:20px;
                                         border:1px solid #BAE6FD;">&larr; Frame 2</span>
                            <span style="font-size:0.78rem;font-weight:600;color:#0C4A6E;">PYNQ-Z2 &rarr; Server</span>
                            <span style="font-size:0.72rem;color:#64748B;font-family:'JetBrains Mono',monospace;">[mlkem_ciphertext]</span>
                        </div>
                        <div style="margin-top:8px;display:flex;gap:18px;flex-wrap:wrap;">
                            <div>
                                <div class="spec-item-label">Size (raw bytes)</div>
                                <div style="font-size:1.05rem;font-weight:700;color:#0284C7;">{_ct_len} B</div>
                            </div>
                            <div style="flex:1;min-width:0;">
                                <div class="spec-item-label">Wire snippet</div>
                                <div style="font-size:0.71rem;color:#475569;font-family:'JetBrains Mono',monospace;
                                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{_ct_snippet}</div>
                            </div>
                        </div>
                    </div>

                    <!-- Frame 3: confirmation -->
                    <div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:10px;
                                padding:12px 16px;">
                        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                            <span style="font-size:0.72rem;font-weight:700;color:#15803D;
                                         background:#DCFCE7;padding:3px 10px;border-radius:20px;
                                         border:1px solid #86EFAC;">Frame 3 &rarr;</span>
                            <span style="font-size:0.78rem;font-weight:600;color:#14532D;">Server &rarr; PYNQ-Z2</span>
                            <span style="font-size:0.72rem;color:#64748B;font-family:'JetBrains Mono',monospace;">[secure_session: established]</span>
                        </div>
                        <div style="margin-top:8px;display:flex;gap:8px;align-items:center;">
                            <i class="fa-solid fa-lock" style="color:#15803D;"></i>
                            <span style="font-size:0.80rem;font-weight:600;color:#14532D;">
                                Shared symmetric key derived locally on both ends &mdash; never transmitted
                            </span>
                        </div>
                    </div>

                </div>

                <!-- Right node: Utility Server -->
                <div style="flex:1;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;
                            padding:18px 16px;display:flex;flex-direction:column;align-items:center;
                            gap:8px;min-width:110px;">
                    <i class="fa-solid fa-server" style="font-size:1.6rem;color:#0284C7;"></i>
                    <div style="font-size:0.80rem;font-weight:700;color:#0F172A;">Utility Server</div>
                    <div style="font-size:0.71rem;color:#64748B;">Laptop</div>
                    <div style="font-size:0.71rem;color:#64748B;">192.168.2.1:{_port}</div>
                </div>

            </div>

            <!-- Shared secret row -->
            <div style="margin-top:16px;background:#0F172A;border-radius:10px;padding:14px 20px;
                        display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
                <i class="fa-solid fa-key" style="color:#FCD34D;font-size:1.2rem;"></i>
                <div>
                    <div style="font-size:0.72rem;font-weight:700;color:#94A3B8;letter-spacing:0.06em;
                                text-transform:uppercase;">32-Byte Shared Secret</div>
                    <div style="font-size:0.84rem;color:#FFFFFF;font-weight:600;">
                        Derived locally / <span style="color:#FCD34D;">NOT transmitted</span> over the wire
                    </div>
                </div>
                <div style="margin-left:auto;">
                    <span style="background:#1E293B;color:#94A3B8;padding:4px 14px;
                                 border-radius:20px;font-size:0.76rem;font-family:'JetBrains Mono',monospace;
                                 border:1px solid #334155;">
                        [REDACTED &mdash; {_ss_len} bytes]
                    </span>
                </div>
            </div>
        </div>
        """)

        # --- Two-column: Attacker view | Authorized server view
        _col_att, _col_auth = st.columns(2, gap="medium")

        with _col_att:
            st.html(f"""
            <div class="card-panel" style="border-top:3px solid #EF4444;">
                <div class="card-panel-title">
                    <span><i class="fa-solid fa-user-secret" style="color:#EF4444;margin-right:8px;"></i>Attacker View</span>
                    <span style="background:#FEE2E2;color:#B91C1C;padding:3px 12px;border-radius:20px;
                                 font-size:0.74rem;font-weight:700;border:1px solid #FCA5A5;">Network Adversary</span>
                </div>

                <div style="margin-bottom:12px;">
                    <div class="status-label" style="margin-bottom:6px;">Captured from wire</div>
                    <div style="display:flex;flex-direction:column;gap:8px;">
                        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                                    padding:10px 14px;display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-size:0.80rem;color:#0F172A;font-weight:600;">
                                <i class="fa-solid fa-eye" style="color:#64748B;margin-right:6px;"></i>
                                ML-KEM Public Key
                            </span>
                            <span style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                                         color:#6D28D9;font-weight:600;">{_pk_len} B</span>
                        </div>
                        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                                    padding:10px 14px;display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-size:0.80rem;color:#0F172A;font-weight:600;">
                                <i class="fa-solid fa-eye" style="color:#64748B;margin-right:6px;"></i>
                                Encapsulated Ciphertext
                            </span>
                            <span style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                                         color:#0284C7;font-weight:600;">{_ct_len} B</span>
                        </div>
                    </div>
                </div>

                <div>
                    <div class="status-label" style="margin-bottom:6px;">NOT available to attacker</div>
                    <div style="display:flex;flex-direction:column;gap:8px;">
                        <div style="background:#FEF2F2;border:1px solid #FCA5A5;border-radius:8px;
                                    padding:10px 14px;display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-size:0.80rem;color:#991B1B;font-weight:600;">
                                <i class="fa-solid fa-eye-slash" style="margin-right:6px;"></i>
                                Private Secret Key
                            </span>
                            <span style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                                         color:#991B1B;font-weight:600;">{_sk_len} B</span>
                        </div>
                        <div style="background:#FEF2F2;border:1px solid #FCA5A5;border-radius:8px;
                                    padding:10px 14px;display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-size:0.80rem;color:#991B1B;font-weight:600;">
                                <i class="fa-solid fa-eye-slash" style="margin-right:6px;"></i>
                                Shared Symmetric Secret
                            </span>
                            <span style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                                         color:#991B1B;font-weight:600;">{_ss_len} B</span>
                        </div>
                    </div>
                </div>

                <div style="margin-top:14px;background:#FEF2F2;border:1px solid #FCA5A5;
                            border-radius:8px;padding:10px 14px;">
                    <span style="font-size:0.78rem;color:#991B1B;font-weight:600;">
                        <i class="fa-solid fa-triangle-exclamation" style="margin-right:6px;"></i>
                        Decryption attempt raises <code style="background:#fee2e2;padding:1px 5px;
                        border-radius:4px;">InvalidTag</code> &mdash; telemetry inaccessible
                    </span>
                </div>
            </div>
            """)

        with _col_auth:
            st.html(f"""
            <div class="card-panel" style="border-top:3px solid #16A34A;">
                <div class="card-panel-title">
                    <span><i class="fa-solid fa-server" style="color:#16A34A;margin-right:8px;"></i>Authorized Server View</span>
                    <span style="background:#DCFCE7;color:#15803D;padding:3px 12px;border-radius:20px;
                                 font-size:0.74rem;font-weight:700;border:1px solid #86EFAC;">Utility Server</span>
                </div>

                <div style="margin-bottom:12px;">
                    <div class="status-label" style="margin-bottom:6px;">Decapsulation process</div>
                    <div style="display:flex;flex-direction:column;gap:8px;">
                        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                                    padding:10px 14px;">
                            <div style="font-size:0.78rem;color:#0F172A;font-weight:600;margin-bottom:4px;">
                                <i class="fa-solid fa-circle-check" style="color:#16A34A;margin-right:6px;"></i>
                                Receives ciphertext ({_ct_len} B)
                            </div>
                            <div style="font-size:0.72rem;color:#64748B;">
                                ML-KEM.Decaps(SK, CT) &rarr; shared_secret
                            </div>
                        </div>
                        <div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;
                                    padding:10px 14px;">
                            <div style="font-size:0.78rem;color:#15803D;font-weight:600;margin-bottom:4px;">
                                <i class="fa-solid fa-lock" style="margin-right:6px;"></i>
                                Derives matching {_ss_len}-byte secret locally
                            </div>
                            <div style="font-size:0.72rem;color:#64748B;">
                                Secret is identical on both ends &mdash; never crossed the wire
                            </div>
                        </div>
                        <div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;
                                    padding:10px 14px;">
                            <div style="font-size:0.78rem;color:#15803D;font-weight:600;margin-bottom:4px;">
                                <i class="fa-solid fa-shield-check" style="margin-right:6px;"></i>
                                AES-256-GCM decryption succeeds
                            </div>
                            <div style="font-size:0.72rem;color:#64748B;">
                                Telemetry authenticated &amp; decrypted correctly
                            </div>
                        </div>
                    </div>
                </div>

                <div style="background:#0F172A;border-radius:8px;padding:12px 16px;">
                    <div style="font-size:0.72rem;color:#94A3B8;font-weight:700;letter-spacing:0.06em;
                                text-transform:uppercase;margin-bottom:6px;">Decapsulation Result</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:#FCD34D;">
                        shared_secret = ML-KEM.Decaps(sk, ct)
                    </div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                                color:#86EFAC;margin-top:4px;">
                        # [REDACTED &mdash; {_ss_len} bytes] &mdash; match confirmed
                    </div>
                </div>
            </div>
            """)

        # --- Validation results
        st.html(f"""
        <div class="card-panel" style="margin-top:4px;">
            <div style="display:flex;justify-content:space-between;align-items:center;
                        flex-wrap:wrap;gap:12px;margin-bottom:16px;">
                <span class="card-panel-title" style="margin:0;">
                    <i class="fa-solid fa-flask" style="color:#6D28D9;margin-right:8px;"></i>
                    {_validation_title}
                </span>
                {_overall_badge}
            </div>

            <div style="display:flex;flex-direction:column;gap:10px;">

                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;
                            padding:14px 18px;display:flex;justify-content:space-between;
                            align-items:center;flex-wrap:wrap;gap:10px;">
                    <div>
                        <div style="font-size:0.84rem;font-weight:700;color:#0F172A;margin-bottom:3px;">
                            Secret Non-Exposure
                        </div>
                        <div style="font-size:0.76rem;color:#64748B;">
                            32-byte shared secret not present in public key or ciphertext bytes
                        </div>
                    </div>
                    {_vbadge(_val_secret_nonexposure, "SECRET ISOLATION")}
                </div>

                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;
                            padding:14px 18px;display:flex;justify-content:space-between;
                            align-items:center;flex-wrap:wrap;gap:10px;">
                    <div>
                        <div style="font-size:0.84rem;font-weight:700;color:#0F172A;margin-bottom:3px;">
                            Unauthorized Decryption Failure
                        </div>
                        <div style="font-size:0.76rem;color:#64748B;">
                            Adversary with random 32-byte key raises <code>cryptography.exceptions.InvalidTag</code>
                        </div>
                    </div>
                    {_vbadge(_val_invalid_tag, "INVALIDTAG")}
                </div>

                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;
                            padding:14px 18px;display:flex;justify-content:space-between;
                            align-items:center;flex-wrap:wrap;gap:10px;">
                    <div>
                        <div style="font-size:0.84rem;font-weight:700;color:#0F172A;margin-bottom:3px;">
                            Legitimate Shared-Secret Match
                        </div>
                        <div style="font-size:0.76rem;color:#64748B;">
                            Server decapsulation produces byte-identical secret to meter encapsulation
                        </div>
                    </div>
                    {_vbadge(_val_secret_match, "SECRET MATCH")}
                </div>

            </div>

            {'<div style="margin-top:12px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;padding:10px 16px;font-size:0.78rem;color:#92400E;"><i class="fa-solid fa-triangle-exclamation" style="margin-right:6px;"></i>Validation error: ' + _val_error + '</div>' if _val_error else ''}
        </div>
        """)

        # --- PQC Spec table
        st.html(f"""
        <div class="card-panel" style="margin-top:4px;">
            <div class="card-panel-title">
                <span><i class="fa-solid fa-list-check" style="color:#6D28D9;margin-right:8px;"></i>ML-KEM-512 Cryptographic Specifications</span>
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px;">
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:14px 16px;">
                    <div class="spec-item-label">Public Key</div>
                    <div style="font-size:1.55rem;font-weight:700;color:#6D28D9;font-family:'JetBrains Mono',monospace;">{_pk_len}</div>
                    <div style="font-size:0.72rem;color:#64748B;">bytes</div>
                </div>
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:14px 16px;">
                    <div class="spec-item-label">Ciphertext</div>
                    <div style="font-size:1.55rem;font-weight:700;color:#0284C7;font-family:'JetBrains Mono',monospace;">{_ct_len}</div>
                    <div style="font-size:0.72rem;color:#64748B;">bytes</div>
                </div>
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:14px 16px;">
                    <div class="spec-item-label">Shared Secret</div>
                    <div style="font-size:1.55rem;font-weight:700;color:#16A34A;font-family:'JetBrains Mono',monospace;">{_ss_len}</div>
                    <div style="font-size:0.72rem;color:#64748B;">bytes &mdash; not transmitted</div>
                </div>
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:14px 16px;">
                    <div class="spec-item-label">Private Key (server only)</div>
                    <div style="font-size:1.55rem;font-weight:700;color:#DC2626;font-family:'JetBrains Mono',monospace;">{_sk_len}</div>
                    <div style="font-size:0.72rem;color:#64748B;">bytes &mdash; never leaves server</div>
                </div>
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:14px 16px;">
                    <div class="spec-item-label">PQC Standard</div>
                    <div style="font-size:0.92rem;font-weight:700;color:#0F172A;margin-top:6px;">{_std}</div>
                    <div style="font-size:0.72rem;color:#64748B;">Post-quantum secure</div>
                </div>
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:14px 16px;">
                    <div class="spec-item-label">Security Level</div>
                    <div style="font-size:0.92rem;font-weight:700;color:#0F172A;margin-top:6px;">Category 1</div>
                    <div style="font-size:0.72rem;color:#64748B;">AES-128 equivalent</div>
                </div>
            </div>
        </div>
        """)

        st.stop()

    # ------------------------------------------------------------------


# ==============================================================================
# EMPTY TELEMETRY HANDLING  –  inject demo data so the layout is always visible
# ==============================================================================
_DEMO_MODE = not raw_readings

if _DEMO_MODE:

    # Show a non-intrusive banner at the top
    st.html(
        """
        <div style="
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            border-radius: 12px;
            padding: 11px 20px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
        ">
            <span style="font-size:1.1rem;">🔌</span>
            <span style="background:#DBEAFE; color:#1D4ED8; font-weight:700; font-size:0.78rem; padding:3px 10px; border-radius:12px; letter-spacing:0.04em;">
                DEMO MODE
            </span>
            <span style="color:#1E3A8A; font-size:0.85rem; font-weight:500;">
                No live connection — displaying sample data.
                Start <code style="background:#DBEAFE; color:#1E40AF; padding:2px 6px; border-radius:4px; font-weight:600;">server/server.py</code> and
                <code style="background:#DBEAFE; color:#1E40AF; padding:2px 6px; border-radius:4px; font-weight:600;">smart_meter/smart_meter.py</code>
                to switch to live telemetry.
            </span>
        </div>
        """
    )

    # ------------------------------------------------------------------
    # Realistic synthetic readings  (30 packets, 3-second cadence)
    # ------------------------------------------------------------------
    import random, math
    _base_ts = now.timestamp() - 90
    raw_readings = []
    for _i in range(30):
        _t = _base_ts + _i * 3
        _v = 229.5 + 1.8 * math.sin(_i / 5) + random.uniform(-0.3, 0.3)
        _c = 14.2 + 0.9 * math.cos(_i / 4) + random.uniform(-0.2, 0.2)
        _p = _v * _c
        raw_readings.append({
            "timestamp":        datetime.fromtimestamp(_t).isoformat(),
            "meter_id":         "SM001",
            "voltage":          round(_v, 3),
            "current":          round(_c, 3),
            "power":            round(_p, 2),
            "energy_kwh":       round(0.004 * _i, 4),
            "frequency":        round(50.0 + random.uniform(-0.05, 0.05), 3),
            "power_factor":     round(0.97 + random.uniform(-0.02, 0.02), 3),
            "kem_algorithm":    "ML-KEM-512",
            "kem_status":       "SUCCESS",
            "session_id":       f"SID-DEMO-{_i:03d}",
            "fpga_latency_us":  round(120 + random.uniform(-10, 10), 1),
            "hrr_verified":     True,
            "tamper_detected":  False,
            "replay_detected":  False,
            "packet_index":     _i,
        })
    # ------------------------------------------------------------------


# ==============================================================================
# DATAFRAME
# ==============================================================================
df = pd.DataFrame(
    raw_readings
)


# ==============================================================================
# PARSE TIMESTAMPS
# ==============================================================================
if "timestamp" in df.columns:

    df["datetime"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

else:

    df["datetime"] = pd.date_range(
        end=now,
        periods=len(df),
        freq="3s"
    )


# ==============================================================================
# TIMESTAMP REMAPPING  –  compensate for PYNQ-Z2 / board clock drift
#
# If the file is being actively written (age_seconds <= STALE_THRESHOLD_SECONDS)
# but the embedded timestamps are significantly behind wall-clock time, the board
# clock is drifted.  We shift ALL datetimes by the lag so the graphs always show
# the current wall-clock time on the x-axis.
#
# readings.json is NEVER modified — this is a display-only correction.
# ==============================================================================
_CLOCK_DRIFT_TOLERANCE_S = 60   # ignore sub-60-second drift (normal NTP jitter)

if (
    "datetime" in df.columns
    and age_seconds is not None
    and age_seconds <= STALE_THRESHOLD_SECONDS   # file is live
    and df["datetime"].notna().any()
):
    # Use the latest ARRIVED packet timestamp rather than global .max()
    _latest_embedded_ts = df["datetime"].dropna().iloc[-1]
    _wall_now           = pd.Timestamp.now()
    _drift_seconds      = (_wall_now - _latest_embedded_ts).total_seconds()

    if _drift_seconds > _CLOCK_DRIFT_TOLERANCE_S or _drift_seconds < -_CLOCK_DRIFT_TOLERANCE_S:
        # Board clock has drifted — shift timestamps to align with current wall clock
        _shift = pd.Timedelta(seconds=_drift_seconds)
        df["datetime"] = df["datetime"] + _shift


# ==============================================================================
# NUMERIC NORMALIZATION
# ==============================================================================
for numeric_column in [
    "voltage",
    "current",
    "power",
    "energy_kwh",
]:

    if numeric_column in df.columns:

        df[numeric_column] = pd.to_numeric(
            df[numeric_column],
            errors="coerce"
        )


# ==============================================================================
# PRESERVE ARRIVAL ORDER
# ==============================================================================
df = df.reset_index(drop=True)


# ==============================================================================
# LATEST / PREVIOUS RECEIVED PACKETS
# ==============================================================================
latest = df.iloc[-1]

prev = (
    df.iloc[-2]
    if len(df) > 1
    else latest
)


# ==============================================================================
# KPI VALUES
# ==============================================================================
power_val = safe_float(
    latest.get(
        "power",
        0.0
    )
)

voltage_val = safe_float(
    latest.get(
        "voltage",
        0.0
    )
)

current_val = safe_float(
    latest.get(
        "current",
        0.0
    )
)

energy_val = safe_float(
    latest.get(
        "energy_kwh",
        0.0
    )
)

meter_status = str(
    latest.get(
        "status",
        "ONLINE"
    )
)


power_delta = round(
    power_val
    - safe_float(
        prev.get(
            "power",
            power_val
        ),
        power_val
    ),
    2
)


# ==============================================================================
# STATISTICS
# ==============================================================================
if "power" in df.columns:

    power_series = pd.to_numeric(
        df["power"],
        errors="coerce"
    ).dropna()

else:

    power_series = pd.Series(
        dtype=float
    )


if power_series.empty:

    avg_power = 0.0
    max_power = 0.0
    min_power = 0.0

else:

    avg_power = round(
        float(power_series.mean()),
        2
    )

    max_power = round(
        float(power_series.max()),
        2
    )

    min_power = round(
        float(power_series.min()),
        2
    )


# ==============================================================================
# CONNECTION STATE — drives ALL chart rendering below
# is_live = True  → feed is fresh, show real data growing progressively
# is_live = False → feed is stale/offline, show clean flatline + overlay
# ==============================================================================
is_live = (
    telemetry_status == "LIVE / ACTIVE"
    and not df.empty
)

# When live: take the active sliding window from the most recently ARRIVED packets
# MAX_CHART_POINTS = 30 (~90s at 3s cadence) creates a clean, real-time moving window
MAX_CHART_POINTS = 30

if is_live and not df.empty:
    # Always take the newest arrived records at the tail of df (arrival order)
    live_df = df.tail(MAX_CHART_POINTS).copy().reset_index(drop=True)
    n_pts = len(live_df)
    _now = pd.Timestamp.now()
    # Provide monotonic, real-time sequential timestamps ending at current wall clock time
    live_df["datetime"] = [
        _now - pd.Timedelta(seconds=(n_pts - 1 - i) * 3)
        for i in range(n_pts)
    ]
else:
    live_df = pd.DataFrame()

# ── Flatline placeholder used when offline ─────────────────────────────────
_now_ts = pd.Timestamp.now()
_flat_x = [_now_ts - pd.Timedelta(minutes=2), _now_ts]
_flat_y = [0.0, 0.0]

# ── Offline overlay annotation ─────────────────────────────────────────────
def _offline_annotation():
    return [
        dict(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text=(
                "<span style='font-size:13px;color:#94A3B8;font-weight:700;letter-spacing:0.04em;'>"
                "⬤ &nbsp;OFFLINE — DISCONNECTED</span><br>"
                "<span style='font-size:11px;color:#64748B;'>"
                "Waiting for telemetry stream to connect…</span>"
            ),
            showarrow=False,
            xanchor="center",
            yanchor="middle",
            align="center",
        )
    ]

def _offline_shape():
    """Subtle striped background when offline."""
    return []   # keep clean — annotation is enough


# ==============================================================================
# MAIN KPI & ELECTRICAL MEASUREMENTS (INSIDE BIG CARD)
# ==============================================================================
delta_prefix = (
    "+"
    if power_delta >= 0
    else ""
)

delta_class = (
    "delta-green"
    if power_delta >= 0
    else "delta-red"
)

delta_arrow = (
    "▲"
    if power_delta >= 0
    else "▼"
)

sync_str = "Just now" if (age_seconds is None or age_seconds <= 15.0) else "Offline"
status_dot = (
    '<span class="dot-green"></span>'
    if telemetry_status == "LIVE / ACTIVE"
    else '<span class="dot-amber"></span>'
)
status_color = (
    "#16A34A"
    if telemetry_status == "LIVE / ACTIVE"
    else "#D97706"
)

# When offline, show 0.00 baseline values with muted styling
_disp_power   = f"{power_val:,.2f}"   if is_live else "0.00"
_disp_voltage = f"{voltage_val:.2f}"  if is_live else "0.00"
_disp_current = f"{current_val:.2f}"  if is_live else "0.00"
_disp_energy  = f"{energy_val * 1000.0:,.2f}" if is_live else "0.00"

power_subtext = (
    f'<span class="{delta_class}">{delta_arrow} {delta_prefix}{power_delta:.2f} W</span> vs prior<br>Sync: <strong style="color: #0F172A;">{sync_str}</strong>'
    if is_live
    else '<span style="color: #94A3B8;">● Inactive</span> · Standby<br>Sync: <strong style="color: #64748B;">Offline</strong>'
)

st.html(
    f"""
    <div class="card-panel" style="margin-bottom: 6px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <span style="font-size: 0.95rem; font-weight: 700; color: #0F172A; font-family: 'JetBrains Mono', monospace; display: flex; align-items: center; gap: 8px;">
                ⚡ Electrical Telemetry &amp; Diagnostics
            </span>
            <i class="fa-solid fa-server" style="color: #64748B; font-size: 0.95rem;"></i>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px;">
            <!-- 1. Power -->
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 18px; display: flex; flex-direction: column; justify-content: space-between; min-height: 138px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="display: flex; align-items: center; gap: 7px; font-size: 0.85rem; font-weight: 700; color: #0F172A;">
                    <i class="fa-solid fa-bolt" style="color: #D97706; font-size: 0.85rem;"></i>
                    <span>Power</span>
                </div>
                <div style="font-size: 1.7rem; font-weight: 700; color: {'#0F172A' if is_live else '#94A3B8'}; font-family: 'JetBrains Mono', monospace; line-height: 1.15; margin: 6px 0;">
                    {_disp_power} <span style="font-size: 0.85rem; color: #64748B; font-weight: 500;">W</span>
                </div>
                <div style="font-size: 0.72rem; color: #64748B; line-height: 1.5;">
                    {power_subtext}
                </div>
            </div>

            <!-- 2. Voltage -->
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 18px; display: flex; flex-direction: column; justify-content: space-between; min-height: 138px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="display: flex; align-items: center; gap: 7px; font-size: 0.85rem; font-weight: 700; color: #0F172A;">
                    <i class="fa-solid fa-wave-square" style="color: #059669; font-size: 0.85rem;"></i>
                    <span>Voltage</span>
                </div>
                <div style="font-size: 1.7rem; font-weight: 700; color: {'#0F172A' if is_live else '#94A3B8'}; font-family: 'JetBrains Mono', monospace; line-height: 1.15; margin: 6px 0;">
                    {_disp_voltage} <span style="font-size: 0.85rem; color: #64748B; font-weight: 500;">V</span>
                </div>
                <div style="font-size: 0.72rem; color: #64748B; line-height: 1.5;">
                    Nominal 230V ± 5% (RMS)<br>
                    Sync: <strong style="color: {'#0F172A' if is_live else '#64748B'};">{sync_str}</strong>
                </div>
            </div>

            <!-- 3. Current -->
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 18px; display: flex; flex-direction: column; justify-content: space-between; min-height: 138px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="display: flex; align-items: center; gap: 7px; font-size: 0.85rem; font-weight: 700; color: #0F172A;">
                    <i class="fa-solid fa-gauge-high" style="color: #0284C7; font-size: 0.85rem;"></i>
                    <span>Current</span>
                </div>
                <div style="font-size: 1.7rem; font-weight: 700; color: {'#0F172A' if is_live else '#94A3B8'}; font-family: 'JetBrains Mono', monospace; line-height: 1.15; margin: 6px 0;">
                    {_disp_current} <span style="font-size: 0.85rem; color: #64748B; font-weight: 500;">A</span>
                </div>
                <div style="font-size: 0.72rem; color: #64748B; line-height: 1.5;">
                    Dynamic consumer load<br>
                    Sync: <strong style="color: {'#0F172A' if is_live else '#64748B'};">{sync_str}</strong>
                </div>
            </div>

            <!-- 4. Energy -->
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 18px; display: flex; flex-direction: column; justify-content: space-between; min-height: 138px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="display: flex; align-items: center; gap: 7px; font-size: 0.85rem; font-weight: 700; color: #0F172A;">
                    <i class="fa-solid fa-chart-line" style="color: #7C3AED; font-size: 0.85rem;"></i>
                    <span>Energy</span>
                </div>
                <div style="font-size: 1.55rem; font-weight: 700; color: {'#0F172A' if is_live else '#94A3B8'}; font-family: 'JetBrains Mono', monospace; line-height: 1.15; margin: 6px 0;">
                    {_disp_energy} <span style="font-size: 0.85rem; color: #64748B; font-weight: 500;">Wh</span>
                </div>
                <div style="font-size: 0.72rem; color: #64748B; line-height: 1.5;">
                    Energy accumulator · Cadence 3s<br>
                    Sync: <strong style="color: {'#0F172A' if is_live else '#64748B'};">{sync_str}</strong>
                </div>
            </div>

            <!-- 5. Meter Status -->
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 18px; display: flex; flex-direction: column; justify-content: space-between; min-height: 138px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="display: flex; align-items: center; gap: 7px; font-size: 0.85rem; font-weight: 700; color: #0F172A;">
                    <i class="fa-solid fa-bullseye" style="color: #059669; font-size: 0.85rem;"></i>
                    <span>Meter {meter_id}</span>
                </div>
                <div style="font-size: 1.55rem; font-weight: 700; color: {status_color}; font-family: 'JetBrains Mono', monospace; line-height: 1.15; margin: 6px 0;">
                    {meter_status}
                </div>
                <div style="font-size: 0.72rem; color: #64748B; line-height: 1.5;">
                    ID: {meter_id} · {total_count} pkts<br>
                    Sync: <strong style="color: {'#0F172A' if is_live else '#64748B'};">{sync_str}</strong>
                </div>
            </div>
        </div>
    </div>
    """
)


(
    col_chart_power,
    col_chart_vc,
) = st.columns(
    [1, 1]
)


# ==============================================================================
# 1. ACTIVE POWER CHART
# ==============================================================================
with col_chart_power:

    fig_power = go.Figure()

    if is_live and not live_df.empty:
        # If just reconnected with 1 reading, ramp up from 0 baseline
        if len(live_df) == 1:
            plot_power_x = [live_df["datetime"].iloc[0] - pd.Timedelta(seconds=2), live_df["datetime"].iloc[0]]
            plot_power_y = [0.0, float(live_df["power"].iloc[0])]
        else:
            plot_power_x = live_df["datetime"]
            plot_power_y = live_df["power"]

        # ── LIVE: real data with area fill ──
        fig_power.add_trace(
            go.Scatter(
                x=plot_power_x,
                y=plot_power_y,
                mode="lines",
                fill="tozeroy",
                fillcolor="rgba(2, 132, 199, 0.08)",
                line=dict(color="rgba(56, 189, 248, 0)", width=0),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig_power.add_trace(
            go.Scatter(
                x=plot_power_x,
                y=plot_power_y,
                mode="lines+markers",
                name="Power",
                line=dict(color="#0284C7", width=2.0),
                marker=dict(size=4, color="#0EA5E9"),
                hovertemplate="<b>%{x|%H:%M:%S}</b><br>Power: %{y:.2f} W<extra></extra>",
            )
        )
        # Average + peak only when live
        fig_power.add_hline(
            y=avg_power,
            line_dash="dash",
            line_color="#64748B",
            line_width=1.2,
            annotation_text=f"Avg: {avg_power:.0f}W",
            annotation_position="bottom right",
            annotation_font=dict(color="#64748B", size=10),
        )
        if "power" in live_df.columns and live_df["power"].notna().any():
            peak_idx = live_df["power"].idxmax()
            fig_power.add_trace(
                go.Scatter(
                    x=[live_df.loc[peak_idx, "datetime"]],
                    y=[live_df["power"].max()],
                    mode="text",
                    text=[f"✦ Peak: {live_df['power'].max():.0f}W"],
                    textposition="top center",
                    textfont=dict(color="#0284C7", size=11, family="Inter"),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
        _power_annotations = []
        _power_yaxis = dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
            tickfont=dict(color="#64748B", size=10),
            title=dict(text="Watts (W)", font=dict(color="#64748B", size=11)),
            rangemode="tozero",
        )
    else:
        # ── OFFLINE: clean straight flat line at 0 ──
        fig_power.add_trace(
            go.Scatter(
                x=_flat_x,
                y=_flat_y,
                mode="lines",
                name="Power (W)",
                line=dict(color="#94A3B8", width=2.5),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        _power_annotations = _offline_annotation()
        _power_yaxis = dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
            tickfont=dict(color="#64748B", size=10),
            title=dict(text="Watts (W)", font=dict(color="#64748B", size=11)),
            range=[-20, 500],
        )

    fig_power.update_layout(
        title=dict(
            text="Active Power Consumption",
            font=dict(size=14, color="#0F172A", family="Inter"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=45, r=20, t=35, b=55),
        height=380,
        autosize=True,
        annotations=_power_annotations,
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
            tickfont=dict(color="#64748B", size=10),
            tickformat="%H:%M:%S",
        ),
        yaxis=_power_yaxis,
        showlegend=False,
    )

    st.plotly_chart(
        fig_power,
        width="stretch",
        config={"displayModeBar": False, "responsive": True},
    )


# ==============================================================================
# 2. VOLTAGE & CURRENT CHART
# ==============================================================================
with col_chart_vc:

    fig_vc = go.Figure()

    if is_live and not live_df.empty:
        # If just reconnected with 1 reading, ramp up from 0 baseline
        if len(live_df) == 1:
            plot_vc_x = [live_df["datetime"].iloc[0] - pd.Timedelta(seconds=2), live_df["datetime"].iloc[0]]
            plot_v_y  = [0.0, float(live_df["voltage"].iloc[0])]
            plot_c_y  = [0.0, float(live_df["current"].iloc[0])]
        else:
            plot_vc_x = live_df["datetime"]
            plot_v_y  = live_df["voltage"]
            plot_c_y  = live_df["current"]

        # ── LIVE: real voltage + current traces ──
        fig_vc.add_trace(
            go.Scatter(
                x=plot_vc_x,
                y=plot_v_y,
                name="Voltage (V)",
                mode="lines+markers",
                line=dict(color="#0D9488", width=1.8),
                marker=dict(size=3, color="#0F766E"),
                hovertemplate="Voltage: %{y:.2f} V<extra></extra>",
            )
        )
        fig_vc.add_trace(
            go.Scatter(
                x=plot_vc_x,
                y=plot_c_y,
                name="Current (A)",
                yaxis="y2",
                mode="lines+markers",
                line=dict(color="#7C3AED", width=1.8),
                marker=dict(size=3, color="#6D28D9"),
                hovertemplate="Current: %{y:.2f} A<extra></extra>",
            )
        )
        _vc_annotations = []
        _vc_yaxis = dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
            tickfont=dict(color="#0D9488", size=10),
            title=dict(text="Volts (V)", font=dict(color="#0D9488", size=11)),
            rangemode="tozero",
        )
        _vc_yaxis2 = dict(
            tickfont=dict(color="#7C3AED", size=10),
            title=dict(text="Amps (A)", font=dict(color="#7C3AED", size=11)),
            overlaying="y",
            side="right",
            showgrid=False,
            rangemode="tozero",
        )
    else:
        # ── OFFLINE: clean straight flat line at 0 ──
        fig_vc.add_trace(
            go.Scatter(
                x=_flat_x,
                y=_flat_y,
                mode="lines",
                name="Voltage (V)",
                line=dict(color="#94A3B8", width=2.5),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        _vc_annotations = _offline_annotation()
        _vc_yaxis = dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
            tickfont=dict(color="#0D9488", size=10),
            title=dict(text="Volts (V)", font=dict(color="#0D9488", size=11)),
            range=[-10, 260],
        )
        _vc_yaxis2 = dict(
            overlaying="y",
            side="right",
            showgrid=False,
            showticklabels=False,
        )

    fig_vc.update_layout(
        title=dict(
            text="Voltage & Current",
            font=dict(size=14, color="#0F172A", family="Inter"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=45, r=40, t=35, b=55),
        height=380,
        autosize=True,
        annotations=_vc_annotations,
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
            tickfont=dict(color="#64748B", size=10),
            tickformat="%H:%M:%S",
        ),
        yaxis=_vc_yaxis,
        yaxis2=_vc_yaxis2,
        legend=dict(
            font=dict(color="#475569", size=10),
            orientation="h",
            y=1.12,
            x=0.42,
        ),
        showlegend=is_live,
    )

    st.plotly_chart(
        fig_vc,
        width="stretch",
        config={"displayModeBar": False, "responsive": True},
    )


# ==============================================================================
# ENERGY CONSUMPTION PROFILE
# ==============================================================================
if is_live and not live_df.empty:
    # Use actual meter cumulative energy converted to Wh (Watt-hours)
    if "energy_kwh" in live_df.columns:
        _raw_energy = live_df["energy_kwh"].astype(float)
    else:
        _raw_energy = pd.Series([0.0] * len(live_df))

    _plot_y = _raw_energy * 1000.0
    _unit_lbl = "Wh"
    _tick_fmt = ".2f"
    _badge_lbl = "Wh"

    _energy_count = len(live_df)
    _energy_last  = float(_plot_y.iloc[-1]) if not _plot_y.empty else 0.0
    _energy_first = float(_plot_y.iloc[0])  if not _plot_y.empty else 0.0
    _energy_delta = _energy_last - _energy_first
    _delta_sign   = "+" if _energy_delta >= 0 else ""
    _delta_color  = "#16A34A" if _energy_delta >= 0 else "#DC2626"

    fig_energy = go.Figure()

    # If just reconnected with 1 reading, ramp up from 0 baseline
    if len(live_df) == 1:
        plot_energy_x = [live_df["datetime"].iloc[0] - pd.Timedelta(seconds=2), live_df["datetime"].iloc[0]]
        plot_energy_y = [0.0, _energy_last]
    else:
        plot_energy_x = live_df["datetime"]
        plot_energy_y = _plot_y

    fig_energy.add_trace(
        go.Scatter(
            x=plot_energy_x,
            y=plot_energy_y,
            mode="lines+markers",
            name=f"Energy ({_unit_lbl})",
            fill="tozeroy",
            fillcolor="rgba(124, 58, 237, 0.07)",
            line=dict(
                color="#7C3AED",
                width=2.2,
                shape="spline",
                smoothing=0.6,
            ),
            marker=dict(
                size=4,
                color="#7C3AED",
                line=dict(width=1, color="#FFFFFF"),
            ),
            hovertemplate=(
                "<b>%{x|%H:%M:%S}</b>"
                f"<br>Energy: %{{y:{_tick_fmt}}} {_unit_lbl}"
                "<extra></extra>"
            ),
        )
    )

    _energy_annotations = [
        # Title + Unit Badge (Top Left)
        dict(
            x=0.0,
            y=1.28,
            xref="paper",
            yref="paper",
            text=(
                f"<b style='font-size:14px;color:#0F172A;font-family:Inter,sans-serif;'>Energy Consumption Profile</b>"
                f"&nbsp;&nbsp;<span style='background:#EDE9FE;color:#5B21B6;font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;border:1px solid #DDD6FE;'>{_badge_lbl}</span>"
            ),
            showarrow=False,
            xanchor="left",
            yanchor="top",
        ),
        # Summary Stats (Top Right)
        dict(
            x=1.0,
            y=1.29,
            xref="paper",
            yref="paper",
            text=(
                f"<span style='font-size:9px;color:#94A3B8;font-weight:600;letter-spacing:0.05em;'>METER TOTAL &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; WINDOW Δ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; SAMPLES</span><br>"
                f"<b style='font-size:13px;color:#0F172A;font-family:JetBrains Mono;'>{_energy_last:.2f} {_unit_lbl}</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                f"<b style='font-size:13px;color:{_delta_color};font-family:JetBrains Mono;'>{_delta_sign}{_energy_delta:.2f} {_unit_lbl}</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                f"<b style='font-size:13px;color:#0F172A;font-family:JetBrains Mono;'>{_energy_count} pkts</b>"
            ),
            showarrow=False,
            xanchor="right",
            yanchor="top",
        ),
        # Legend Row (Below Header)
        dict(
            x=0.0,
            y=1.09,
            xref="paper",
            yref="paper",
            text=(
                f"<span style='color:#7C3AED;font-weight:900;font-size:14px;'>━</span> <span style='font-size:11px;color:#334155;font-weight:600;'>Cumulative Energy ({_unit_lbl})</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                f"<span style='color:rgba(124,58,237,0.35);font-weight:900;font-size:14px;'>■</span> <span style='font-size:11px;color:#64748B;'>Area Fill</span>"
            ),
            showarrow=False,
            xanchor="left",
            yanchor="top",
        ),
    ]

    _y_min = float(_plot_y.min()) if not _plot_y.empty else 0.0
    _y_max = float(_plot_y.max()) if not _plot_y.empty else 1.0
    _y_pad = max(0.5, (_y_max - _y_min) * 0.15) if _y_max > _y_min else 1.0

    _energy_yaxis = dict(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.06)",
        griddash="solid",
        gridwidth=1,
        zeroline=False,
        showline=True,
        linecolor="#CBD5E1",
        linewidth=1,
        tickfont=dict(color="#475569", size=10, family="JetBrains Mono"),
        tickformat=_tick_fmt,
        nticks=6,
        ticksuffix=f" {_unit_lbl}",
        range=[_y_min - _y_pad, _y_max + _y_pad],
    )
else:
    # ── OFFLINE: clean straight flat line at 0 ──
    fig_energy = go.Figure()
    fig_energy.add_trace(
        go.Scatter(
            x=_flat_x,
            y=_flat_y,
            mode="lines",
            name="Energy (Wh)",
            line=dict(color="#94A3B8", width=2.5),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    _energy_annotations = _offline_annotation() + [
        dict(
            x=0.0,
            y=1.28,
            xref="paper",
            yref="paper",
            text=(
                "<b style='font-size:14px;color:#0F172A;font-family:Inter,sans-serif;'>Energy Consumption Profile</b>"
                "&nbsp;&nbsp;<span style='background:#F1F5F9;color:#64748B;font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;border:1px solid #CBD5E1;'>OFFLINE</span>"
            ),
            showarrow=False,
            xanchor="left",
            yanchor="top",
        ),
        dict(
            x=1.0,
            y=1.29,
            xref="paper",
            yref="paper",
            text=(
                "<span style='font-size:9px;color:#94A3B8;font-weight:600;letter-spacing:0.05em;'>CUMULATIVE &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; SESSION Δ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; SAMPLES</span><br>"
                "<b style='font-size:13px;color:#94A3B8;font-family:JetBrains Mono;'>0.00 Wh</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                "<b style='font-size:13px;color:#94A3B8;font-family:JetBrains Mono;'>0.00 Wh</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                "<b style='font-size:13px;color:#94A3B8;font-family:JetBrains Mono;'>0</b>"
            ),
            showarrow=False,
            xanchor="right",
            yanchor="top",
        ),
    ]

    _energy_yaxis = dict(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.06)",
        range=[-0.2, 5.0],
        tickfont=dict(color="#64748B", size=10, family="JetBrains Mono"),
        ticksuffix=" Wh",
        zeroline=True,
        zerolinecolor="rgba(0,0,0,0.15)",
        zerolinewidth=1,
    )

fig_energy.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=65, r=25, t=95, b=55),
    height=440,
    autosize=True,
    annotations=_energy_annotations,
    shapes=[
        # Horizontal divider under header
        dict(
            type="line",
            xref="paper",
            yref="paper",
            x0=0,
            y0=1.14,
            x1=1,
            y1=1.14,
            line=dict(color="#F1F5F9", width=1),
        ),
        # Horizontal divider under legend
        dict(
            type="line",
            xref="paper",
            yref="paper",
            x0=0,
            y0=1.03,
            x1=1,
            y1=1.03,
            line=dict(color="#F8FAFC", width=1),
        ),
    ],
    xaxis=dict(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.06)",
        griddash="solid",
        gridwidth=1,
        zeroline=False,
        showline=True,
        linecolor="#CBD5E1",
        linewidth=1,
        tickfont=dict(color="#475569", size=10, family="JetBrains Mono"),
        tickformat="%H:%M:%S",
        nticks=6,
    ),
    yaxis=_energy_yaxis,
    showlegend=False,
)

st.plotly_chart(
    fig_energy,
    width="stretch",
    config={
        "displayModeBar": False,
        "responsive": True,
    },
)


# ==============================================================================
# SYSTEM PIPELINE & ARCHITECTURE WORKFLOW
# ==============================================================================
st.html(
    """
    <div class="card-panel" style="margin-bottom:22px;">
        <div class="card-panel-title" style="margin-bottom:14px;">
            <span>
                🗺️ System Pipeline &amp; Implementation Architecture
                <span style="font-size:0.75rem; color:#16A34A; font-weight:600; background:rgba(22,163,74,0.1); padding:2px 8px; border-radius:6px; border:1px solid rgba(22,163,74,0.25); margin-left:8px;">
                    ● CURRENT IMPLEMENTED SYSTEM
                </span>
            </span>
        </div>

        <!-- TOP PIPELINE CARDS (7 STAGES) -->
        <div style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:8px;
            flex-wrap:nowrap;
            overflow-x:auto;
            padding-bottom:6px;
        ">
            <!-- 1. Smart Meter -->
            <div class="pipeline-node" style="flex:1; min-width:105px;">
                <div class="node-title">
                    Smart Meter<br>
                    <span style="color:#64748B;">PYNQ-Z2</span>
                </div>
                <div class="node-status-row" style="color:#16A34A;">
                    <span class="dot-green"></span> LIVE
                </div>
                <div style="font-size:0.62rem; color:#64748B;">
                    Operational
                </div>
            </div>

            <div class="node-arrow">➔</div>

            <!-- 2. ML-KEM-512 -->
            <div class="pipeline-node" style="flex:1; min-width:105px;">
                <div class="node-title">
                    ML-KEM-512<br>
                    <span style="color:#64748B;">ARM Software</span>
                </div>
                <div class="node-status-row" style="color:#16A34A;">
                    <span class="dot-green"></span> LIVE
                </div>
                <div style="font-size:0.62rem; color:#64748B;">
                    Operational
                </div>
            </div>

            <div class="node-arrow">➔</div>

            <!-- 3. FPGA / HRR -->
            <div class="pipeline-node" style="flex:1; min-width:105px;">
                <div class="node-title">
                    FPGA / HRR<br>
                    <span style="color:#64748B;">HW Accelerator</span>
                </div>
                <div class="node-status-row" style="color:#16A34A;">
                    <span class="dot-green"></span> LIVE
                </div>
                <div style="font-size:0.62rem; color:#16A34A; font-weight:600;">
                    Verified
                </div>
            </div>

            <div class="node-arrow">➔</div>

            <!-- 4. Shared Secret -->
            <div class="pipeline-node" style="flex:1; min-width:105px;">
                <div class="node-title">
                    Shared Secret<br>
                    <span style="color:#64748B;">32-Byte Key</span>
                </div>
                <div class="node-status-row" style="color:#16A34A;">
                    <span class="dot-green"></span> LIVE
                </div>
                <div style="font-size:0.62rem; color:#16A34A; font-weight:600;">
                    Established
                </div>
            </div>

            <div class="node-arrow">➔</div>

            <!-- 5. Symmetric Encryption -->
            <div class="pipeline-node" style="flex:1; min-width:105px;">
                <div class="node-title">
                    Symmetric Enc.<br>
                    <span style="color:#64748B;">AES-256-GCM</span>
                </div>
                <div class="node-status-row" style="color:#16A34A;">
                    <span class="dot-green"></span> LIVE
                </div>
                <div style="font-size:0.62rem; color:#64748B;">
                    Operational
                </div>
            </div>

            <div class="node-arrow">➔</div>

            <!-- 6. Utility Server -->
            <div class="pipeline-node" style="flex:1; min-width:105px;">
                <div class="node-title">
                    Utility Server<br>
                    <span style="color:#64748B;">192.168.2.1:5000</span>
                </div>
                <div class="node-status-row" style="color:#16A34A;">
                    <span class="dot-green"></span> LIVE
                </div>
                <div style="font-size:0.62rem; color:#64748B;">
                    Operational
                </div>
            </div>

            <div class="node-arrow">➔</div>

            <!-- 7. Dashboard -->
            <div class="pipeline-node" style="flex:1; min-width:105px;">
                <div class="node-title">
                    Dashboard<br>
                    <span style="color:#64748B;">Streamlit Cockpit</span>
                </div>
                <div class="node-status-row" style="color:#16A34A;">
                    <span class="dot-green"></span> LIVE
                </div>
                <div style="font-size:0.62rem; color:#64748B;">
                    Operational
                </div>
            </div>
        </div>

        <!-- DETAILED IMPLEMENTED ARCHITECTURAL WORKFLOW -->
        <div style="margin-top:16px; background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px; padding:16px 18px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <span style="font-size:0.82rem; font-weight:700; color:#0F172A; text-transform:uppercase; letter-spacing:0.04em;">
                    ⚡ Physical System Architecture &amp; Dataflow
                </span>
                <span style="font-size:0.72rem; color:#64748B; font-family:'JetBrains Mono',monospace;">
                    ARM (Software) + FPGA (Hardware) ➔ TCP/IP ➔ Windows Server
                </span>
            </div>

            <div style="display:grid; grid-template-columns: 1.15fr 0.3fr 1.15fr; gap:14px; align-items:stretch;">
                <!-- PYNQ-Z2 CONTAINER -->
                <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:14px 16px; display:flex; flex-direction:column; justify-content:space-between;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; border-bottom:1px solid #F1F5F9; padding-bottom:8px;">
                        <span style="font-weight:700; font-size:0.86rem; color:#0F172A; display:flex; align-items:center; gap:6px;">
                            <i class="fa-solid fa-microchip" style="color:#0284C7;"></i> PYNQ-Z2 (192.168.2.99)
                        </span>
                        <span style="background:#DCFCE7; color:#15803D; font-size:0.65rem; font-weight:700; padding:2px 7px; border-radius:10px; border:1px solid #BBF7D0;">
                            ● ACTIVE
                        </span>
                    </div>

                    <!-- Sub-block: ARM / Smart Meter Application -->
                    <div style="background:#F1F5F9; border-radius:8px; padding:10px 12px; margin-bottom:10px; border-left:3px solid #0284C7;">
                        <div style="font-size:0.72rem; font-weight:700; color:#0369A1; text-transform:uppercase; margin-bottom:6px; letter-spacing:0.03em;">
                            ARM Cortex-A9 · Smart Meter Application (Software)
                        </div>
                        <div style="font-size:0.73rem; color:#334155; line-height:1.45; font-family:'JetBrains Mono',monospace;">
                            • <strong>Telemetry Generation:</strong> Live V/I/W/Wh sensor sampling<br>
                            • <strong>ML-KEM-512:</strong> Post-quantum key encapsulation (ARM)<br>
                            • <strong>AES-256-GCM:</strong> Authenticated payload encryption
                        </div>
                    </div>

                    <!-- Sub-block: FPGA / HRR -->
                    <div style="background:#FEF3C7; border-radius:8px; padding:10px 12px; border-left:3px solid #D97706;">
                        <div style="font-size:0.72rem; font-weight:700; color:#92400E; text-transform:uppercase; margin-bottom:6px; letter-spacing:0.03em;">
                            FPGA Programmable Logic · HRR Accelerator (Hardware)
                        </div>
                        <div style="font-size:0.73rem; color:#78350F; line-height:1.45; font-family:'JetBrains Mono',monospace;">
                            • <strong>HRR Accelerator:</strong> Modular arithmetic modulo q=3329<br>
                            • <strong>HW/SW Interface:</strong> AXI4-Lite (<code style="background:rgba(0,0,0,0.06); padding:1px 4px; border-radius:4px;">fpga_interface.py</code>)<br>
                            • <strong>Self-Test:</strong> 7 × 9 = 63 (<span style="color:#15803D; font-weight:700;">PASS</span>) · <code style="background:rgba(0,0,0,0.06); padding:1px 4px; border-radius:4px;">hrr_bd_wrapper.bit</code>
                        </div>
                    </div>
                </div>

                <!-- NETWORK BUS (CENTER) -->
                <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; padding:8px 0;">
                    <div style="font-size:0.68rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:4px;">
                        Direct Ethernet
                    </div>
                    <i class="fa-solid fa-network-wired" style="color:#0284C7; font-size:1.1rem; margin-bottom:4px;"></i>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#0F172A; font-weight:600; background:#E2E8F0; padding:2px 6px; border-radius:6px; margin-bottom:6px;">
                        TCP :5000
                    </div>
                    <div style="font-size:0.64rem; color:#64748B; line-height:1.3;">
                        AES-256-GCM<br>Encrypted Stream<br>
                        <span style="font-size:1rem; color:#0284C7;">➔</span>
                    </div>
                </div>

                <!-- WINDOWS UTILITY SERVER & DASHBOARD -->
                <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:14px 16px; display:flex; flex-direction:column; justify-content:space-between;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; border-bottom:1px solid #F1F5F9; padding-bottom:8px;">
                        <span style="font-weight:700; font-size:0.86rem; color:#0F172A; display:flex; align-items:center; gap:6px;">
                            <i class="fa-solid fa-server" style="color:#7C3AED;"></i> Windows Host (192.168.2.1)
                        </span>
                        <span style="background:#DCFCE7; color:#15803D; font-size:0.65rem; font-weight:700; padding:2px 7px; border-radius:10px; border:1px solid #BBF7D0;">
                            ● ACTIVE
                        </span>
                    </div>

                    <!-- Sub-block: Utility Server -->
                    <div style="background:#F1F5F9; border-radius:8px; padding:10px 12px; margin-bottom:10px; border-left:3px solid #7C3AED;">
                        <div style="font-size:0.72rem; font-weight:700; color:#5B21B6; text-transform:uppercase; margin-bottom:6px; letter-spacing:0.03em;">
                            Utility Server · server/server.py (:5000)
                        </div>
                        <div style="font-size:0.73rem; color:#334155; line-height:1.45; font-family:'JetBrains Mono',monospace;">
                            • <strong>Handshake:</strong> Receives ML-KEM PK &amp; derives 32B shared secret<br>
                            • <strong>Decryption:</strong> AES-GCM MAC auth &amp; payload deciphering<br>
                            • <strong>Persistence:</strong> Validates fields ➔ <code style="background:rgba(0,0,0,0.06); padding:1px 4px; border-radius:4px;">server/readings.json</code>
                        </div>
                    </div>

                    <!-- Sub-block: Streamlit Dashboard -->
                    <div style="background:#ECFDF5; border-radius:8px; padding:10px 12px; border-left:3px solid #16A34A;">
                        <div style="font-size:0.72rem; font-weight:700; color:#15803D; text-transform:uppercase; margin-bottom:6px; letter-spacing:0.03em;">
                            Streamlit Telemetry Cockpit · dashboard/app.py
                        </div>
                        <div style="font-size:0.73rem; color:#166534; line-height:1.45; font-family:'JetBrains Mono',monospace;">
                            • <strong>Live Ingestion:</strong> Hot-reloads fresh JSON readings<br>
                            • <strong>Analytics:</strong> Real-time Power/V/I metrics &amp; session trends<br>
                            • <strong>Diagnostics:</strong> Hardware status &amp; cryptographic telemetry
                        </div>
                    </div>
                </div>
            </div>

            <!-- ARCHITECTURAL NOTE -->
            <div style="margin-top:12px; padding:9px 12px; background:#F1F5F9; border-left:3px solid #0284C7; border-radius:6px; font-size:0.74rem; color:#334155; line-height:1.5;">
                <strong style="color:#0F172A;">Architecture Note:</strong> ML-KEM-512 and AES-256-GCM execute on the PYNQ ARM processor, while HRR modular arithmetic is accelerated in FPGA hardware.
            </div>
        </div>
    </div>
    """
)


# ==============================================================================
# SECURITY + FPGA SUMMARY
# ==============================================================================
col_sec_summary, col_fpga_summary = st.columns(2)


# ==============================================================================
# SECURITY SUMMARY
# ==============================================================================
with col_sec_summary:

    st.html(
        """
        <div class="card-panel">
            <div class="card-panel-title">
                <span>🛡️ Quick Security Overview</span>
                <span class="badge-pill pill-live" style="background:#EDE9FE; color:#6D28D9; border:1px solid #DDD6FE;">
                    <span class="dot-purple"></span> NIST FIPS 203 + AES-GCM
                </span>
            </div>

            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:14px; margin-top:4px;">
                <div class="spec-col">
                    <div class="spec-item-label">PQC Standard</div>
                    <div class="spec-item-value" style="color:#0F172A; font-weight:700;">NIST FIPS 203</div>
                </div>

                <div class="spec-col">
                    <div class="spec-item-label">PQC Primitive</div>
                    <div class="spec-item-value" style="color:#0284C7; font-weight:700;">ML-KEM-512</div>
                </div>

                <div class="spec-col">
                    <div class="spec-item-label">PQC Role</div>
                    <div class="spec-item-value" style="color:#16A34A; font-weight:700;">Key Establishment</div>
                </div>

                <div class="spec-col">
                    <div class="spec-item-label">Symmetric Cipher</div>
                    <div class="spec-item-value" style="color:#7C3AED; font-weight:700;">AES-256-GCM</div>
                </div>

                <div class="spec-col">
                    <div class="spec-item-label">Security Purpose</div>
                    <div class="spec-item-value" style="color:#0F172A; font-size:0.80rem; font-weight:600;">
                        Confidentiality + Authenticated Integrity
                    </div>
                </div>
            </div>
        </div>
        """
    )


# ==============================================================================
# FPGA SUMMARY
# ==============================================================================
with col_fpga_summary:

    st.html(
        """
        <div class="card-panel">
            <div class="card-panel-title">
                <span>🔲 Hardware Acceleration</span>
                <span class="badge-pill pill-live">
                    <span class="dot-green"></span> Operational / Verified
                </span>
            </div>

            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:14px; margin-top:4px;">
                <div class="spec-col">
                    <div class="spec-item-label">FPGA Target</div>
                    <div class="spec-item-value" style="color:#0F172A; font-weight:700;">Xilinx Zynq-7000 / PYNQ-Z2</div>
                </div>

                <div class="spec-col">
                    <div class="spec-item-label">Accelerated Component</div>
                    <div class="spec-item-value" style="color:#D97706; font-weight:700;">HRR Modular Arithmetic</div>
                </div>

                <div class="spec-col">
                    <div class="spec-item-label">Bitstream</div>
                    <div class="spec-item-value" style="font-family:'JetBrains Mono',monospace; font-size:0.78rem; color:#0F172A;">hrr_bd_wrapper.bit</div>
                </div>

                <div class="spec-col">
                    <div class="spec-item-label">HW/SW Interface</div>
                    <div class="spec-item-value" style="font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:#0284C7; word-break:break-all;">
                        fpga_interface/fpga_interface.py
                    </div>
                </div>

                <div class="spec-col">
                    <div class="spec-item-label">Verification</div>
                    <div class="spec-item-value" style="color:#16A34A; font-size:0.80rem; font-weight:700;">
                        HRR 7 × 9 = 63 · PASS
                    </div>
                </div>

                <div class="spec-col">
                    <div class="spec-item-label">Integration Status</div>
                    <div class="spec-item-value" style="color:#16A34A; font-weight:700;">
                        Operational / Verified on PYNQ-Z2
                    </div>
                </div>
            </div>
        </div>
        """
    )


# ==============================================================================
# COCKPIT CONTROLS & SYSTEM STATUS
# ==============================================================================
st.html(
    """
    <div class="section-header-title" style="margin-top:28px;">
        <i class="fa-solid fa-sliders"></i>
        COCKPIT CONTROLS &amp; SYSTEM STATUS
    </div>
    """
)

col_ctrl, col_status = st.columns([1, 1])

with col_ctrl:
    st.html(
        """
        <div class="card-panel" style="margin-bottom:22px;">
            <div class="card-panel-title">
                🎛️ Cockpit Refresh Controls
            </div>
        """
    )

    auto_refresh_card = st.checkbox(
        "Live Polling (Auto-refresh)",
        value=auto_refresh,
        key="auto_refresh_card"
    )

    refresh_interval_card = st.slider(
        "Cadence (seconds)",
        min_value=1,
        max_value=10,
        value=refresh_interval,
        key="refresh_interval_card",
        help="Polling cadence. Matches the Smart Meter transmission interval.",
    )

    st.markdown("")

    if st.button(
        "🔄 Manual Sync Now",
        key="manual_sync_card",
        use_container_width=True
    ):
        st.rerun()

    st.html("</div>")

    auto_refresh = auto_refresh_card
    refresh_interval = refresh_interval_card


with col_status:
    readings_file = get_readings_file_path()
    file_exists = readings_file.exists()

    source_available_html = (
        '<span style="color:#15803D; font-weight:700;">✔ Yes</span>'
        if file_exists
        else '<span style="color:#DC2626; font-weight:700;">✖ No</span>'
    )

    st.html(
        f"""
        <div class="card-panel" style="margin-bottom:22px;">
            <div class="card-panel-title">
                📊 System Status
            </div>
            <div style="margin-top:8px;">
                <div class="status-row">
                    <div class="status-label">System Status</div>
                    <div class="status-value"><span class="dot-green"></span> Operational</div>
                </div>
                <div class="status-row">
                    <div class="status-label">Telemetry Source</div>
                    <div class="status-value" style="font-size:0.75rem; color:#64748B;">server/readings.json</div>
                </div>
                <div class="status-row">
                    <div class="status-label">Source Available</div>
                    <div class="status-value">{source_available_html}</div>
                </div>
                <div class="status-row">
                    <div class="status-label">Meter Sample Cadence</div>
                    <div class="status-value">3.0 seconds</div>
                </div>
                <div class="status-row">
                    <div class="status-label">Utility Server</div>
                    <div class="status-value" style="font-size:0.75rem;">TCP 192.168.2.1:5000</div>
                </div>
                <div class="status-row">
                    <div class="status-label">Total Readings</div>
                    <div class="status-value">{total_count}</div>
                </div>
                <div class="status-row">
                    <div class="status-label">Last Update</div>
                    <div class="status-value">{age_str}</div>
                </div>
            </div>
        </div>
        """
    )


# ==============================================================================
# HISTORICAL TELEMETRY (AT THE BOTTOM)
# ==============================================================================
with st.expander(
    "📋 Historical Telemetry Records & Data Export",
    expanded=False,
):

    table_cols = [
        "timestamp",
        "meter_id",
        "voltage",
        "current",
        "power",
        "energy_kwh",
        "status",
    ]

    available_cols = [
        column
        for column in table_cols
        if column in df.columns
    ]

    display_df = (
        df[available_cols]
        .copy()
    )

    # Newest RECEIVED packet first.
    display_df = (
        display_df
        .iloc[::-1]
        .reset_index(drop=True)
    )

    st.dataframe(
        display_df.style.format(
            {
                "voltage": "{:.2f} V",
                "current": "{:.2f} A",
                "power": "{:.2f} W",
                "energy_kwh": "{:.6f} kWh",
            }
        ),
        width="stretch",
        height=350,
    )

    csv_data = display_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="📥 Export Telemetry as CSV",
        data=csv_data,
        file_name=(
            "smart_meter_telemetry_"
            f"{now.strftime('%Y%m%d_%H%M%S')}.csv"
        ),
        mime="text/csv",
        width="stretch",
    )


# ==============================================================================
# AUTO REFRESH
# ==============================================================================
if auto_refresh:

    time.sleep(
        refresh_interval
    )

    st.rerun()




