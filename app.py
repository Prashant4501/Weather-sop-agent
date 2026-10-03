import os
import json
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

from agent import WeatherAdvisoryAgent
from sop_engine import SOPEngine
from weather_service import fetch_live_weather

# Page configuration
st.set_page_config(
    page_title="MediBuddy Weather Advisory Support Bot",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv(override=True)

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history_langchain" not in st.session_state:
    st.session_state.chat_history_langchain = []

if "last_location" not in st.session_state:
    st.session_state.last_location = None

if "last_activity" not in st.session_state:
    st.session_state.last_activity = None

# Custom Modern CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1100px;
    }

    /* Hero Banner */
    .hero-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 60%, #1E293B 100%);
        border-radius: 18px;
        padding: 2rem 2.2rem;
        margin-bottom: 2rem;
        color: #FFFFFF;
        box-shadow: 0 12px 35px -8px rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.08);
        position: relative;
        overflow: hidden;
    }
    .hero-container::before {
        content: "";
        position: absolute;
        top: -60px;
        right: -60px;
        width: 180px;
        height: 180px;
        background: radial-gradient(circle, rgba(56, 189, 248, 0.25) 0%, rgba(56, 189, 248, 0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(56, 189, 248, 0.15);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.35);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 0.8rem;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0 0 0.5rem 0;
        background: linear-gradient(to right, #FFFFFF, #E2E8F0, #93C5FD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 0.96rem;
        color: #94A3B8;
        line-height: 1.5;
        margin-bottom: 1.2rem;
        max-width: 750px;
    }
    .hero-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    .hero-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.76rem;
        color: #CBD5E1;
        font-weight: 500;
    }

    /* Context Retained Chip */
    .context-bar {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        color: #166534;
        border-radius: 10px;
        padding: 0.6rem 1rem;
        font-size: 0.82rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 1.5rem;
    }

    /* Weather Stat Grid */
    .weather-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
        gap: 10px;
        margin: 0.9rem 0;
    }
    .weather-stat-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 0.75rem 0.85rem;
        text-align: center;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .weather-stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    .weather-stat-icon {
        font-size: 1.2rem;
        margin-bottom: 2px;
    }
    .weather-stat-value {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0F172A;
    }
    .weather-stat-label {
        font-size: 0.72rem;
        color: #64748B;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    /* SOP Alert Banner */
    .sop-alert-card {
        border-radius: 12px;
        padding: 0.85rem 1.1rem;
        margin-top: 0.8rem;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        font-size: 0.88rem;
    }
    .sop-alert-CRITICAL {
        background: #FEF2F2;
        border: 1px solid #FCA5A5;
        color: #991B1B;
    }
    .sop-alert-HIGH {
        background: #FFF7ED;
        border: 1px solid #FDBA74;
        color: #9A3412;
    }
    .sop-alert-MEDIUM {
        background: #FEFCE8;
        border: 1px solid #FDE047;
        color: #854D0E;
    }
    .sop-alert-LOW {
        background: #EEF2FF;
        border: 1px solid #C7D2FE;
        color: #3730A3;
    }
    .sop-alert-NONE {
        background: #F1F5F9;
        border: 1px solid #CBD5E1;
        color: #334155;
    }

    .sop-badge {
        display: inline-block;
        font-weight: 700;
        font-size: 0.72rem;
        padding: 2px 8px;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Welcome / Starter Cards */
    .starter-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .starter-card-desc {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 4px;
    }

    /* Sidebar Brand Card */
    .sidebar-brand-card {
        background: linear-gradient(135deg, #1E293B, #0F172A);
        border-radius: 14px;
        padding: 1.2rem;
        color: white;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .sidebar-brand-title {
        font-weight: 800;
        font-size: 1.15rem;
        margin-bottom: 0.2rem;
    }
    .sidebar-brand-status {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.75rem;
        color: #4ADE80;
        font-weight: 600;
    }

    /* Streamlit Chat Message Tweaks */
    .stChatMessage {
        border-radius: 12px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- MAIN HERO BANNER -----------------
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">✦ Deterministic SOP Policy Engine</div>
    <div class="hero-title">🌤️ MediBuddy Weather-Advisory Bot</div>
    <div class="hero-subtitle">
        Intelligent outdoor safety guidance strictly grounded in Open-Meteo live weather observations and standard operating procedures (SOPs). Zero hallucinations, deterministic safety decisions.
    </div>
    <div class="hero-pills">
        <div class="hero-pill">⚡ LangGraph State Graph</div>
        <div class="hero-pill">🌐 Open-Meteo Live API</div>
        <div class="hero-pill">🧠 LLaMA-3.3 70B (Groq)</div>
        <div class="hero-pill">📜 11 Strictly Governed SOPs</div>
        <div class="hero-pill">🛡️ Adversarial Injection Resistant</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Active Context Pill (Memory Indicator)
if st.session_state.last_location or st.session_state.last_activity:
    loc_text = st.session_state.last_location or "Not specified"
    act_text = st.session_state.last_activity or "General Outdoor"
    st.markdown(f"""
    <div class="context-bar">
        <span>🧠 <b>Active Session Context:</b> Location: <u>{loc_text}</u> • Activity: <u>{act_text}</u></span>
        <span style="margin-left: auto; font-size: 0.75rem; color: #15803D;">(Follow-up queries will automatically inherit this context)</span>
    </div>
    """, unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand-card">
        <div class="sidebar-brand-title">🛡️ System Control</div>
        <div class="sidebar-brand-status">● Live Engine Operational</div>
        <div style="font-size: 0.76rem; color: #94A3B8; margin-top: 6px;">
            Open-Meteo Geocoding & Forecast APIs Active
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Groq API Key Check
    groq_key = (os.getenv("GROQ_API_KEY") or "").strip().strip('"').strip("'")
    if not (groq_key and groq_key != "your_groq_api_key_here"):
        st.warning("⚠️ Groq API Key Missing!")
        st.info("Please set `GROQ_API_KEY` in the `.env` file.")
    else:
        st.success("🔑 Groq API Key Connected")

    # Clear Memory Button
    if st.button("🗑️ Reset Chat & Memory", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_history_langchain = []
        st.session_state.last_location = None
        st.session_state.last_activity = None
        st.rerun()

    st.markdown("---")

    # Quick Scenario Test Buttons
    st.subheader("💡 Suggested Queries")
    scenarios = [
        {"title": "🚴 High UV Cycling (Bhopal)", "query": "Is it safe to cycle today in Bhopal around 1 PM?"},
        {"title": "🔄 Follow-Up Context Query", "query": "What about this evening instead?"},
        {"title": "🏍️ High Wind Commute (Mumbai)", "query": "Can I ride my bike in Mumbai right now?"},
        {"title": "👶 Toddler Park Walk (Delhi Heat)", "query": "Is it okay to take my toddler to the park in Delhi?"},
        {"title": "♟️ Indoor Chess (Honest Fallback)", "query": "Is it safe to play indoor chess in London?"},
        {"title": "🧺 Outdoor Picnic (Bangalore)", "query": "Can I go for a picnic in Bangalore today?"}
    ]

    for item in scenarios:
        if st.button(f"👉 {item['title']}", use_container_width=True, help=item['query']):
            st.session_state.pending_query = item['query']
            st.rerun()

    st.markdown("---")

    # Active Policy Rules (SOPs) Explorer
    st.subheader("📜 Loaded SOP Rule Set")
    try:
        sop_engine = SOPEngine("sops.json")
        st.caption(f"Currently managing **{len(sop_engine.sops)} declarative SOP rules** from `sops.json`")
        
        with st.expander("🔍 Inspect Full Rule Catalog"):
            for sop in sop_engine.sops:
                sev = sop.get("severity", "LOW")
                sev_color = {
                    "CRITICAL": "#DC2626",
                    "HIGH": "#EA580C",
                    "MEDIUM": "#CA8A04",
                    "LOW": "#4F46E5"
                }.get(sev, "#64748B")
                
                st.markdown(f"**`{sop['id']}` {sop['title']}**")
                st.markdown(f"<span style='color: {sev_color}; font-weight:700; font-size:0.75rem;'>SEVERITY: {sev}</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='font-size:0.8rem; color:#475569;'>{sop['prescribed_guidance']}</span>", unsafe_allow_html=True)
                st.divider()
    except Exception as e:
        st.error(f"Error loading sops.json: {e}")

# Check if sample query was clicked
user_input = None
if "pending_query" in st.session_state and st.session_state.pending_query:
    user_input = st.session_state.pending_query
    st.session_state.pending_query = None

# Helper to render weather metrics cards
def render_weather_grid(w):
    if not w:
        return ""
    temp = w.get("temperature_2m", "N/A")
    wind = w.get("wind_speed_10m", "N/A")
    rain = w.get("precipitation", "N/A")
    uv = w.get("uv_index", "N/A")
    loc = w.get("location_name", "Live Station")

    # UV Badge label
    try:
        uv_val = float(uv)
        if uv_val >= 8:
            uv_tag = "🔴 Extreme"
        elif uv_val >= 6:
            uv_tag = "🟠 High"
        elif uv_val >= 3:
            uv_tag = "🟡 Moderate"
        else:
            uv_tag = "🟢 Low"
    except Exception:
        uv_tag = "UV"

    return f"""
    <div style="margin-top: 0.6rem; margin-bottom: 0.4rem;">
        <span style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">
            📍 Verified Real-Time Weather Fact-Check ({loc}):
        </span>
    </div>
    <div class="weather-grid">
        <div class="weather-stat-card">
            <div class="weather-stat-icon">🌡️</div>
            <div class="weather-stat-value">{temp}°C</div>
            <div class="weather-stat-label">Temperature</div>
        </div>
        <div class="weather-stat-card">
            <div class="weather-stat-icon">💨</div>
            <div class="weather-stat-value">{wind} <span style="font-size:0.75rem;">km/h</span></div>
            <div class="weather-stat-label">Wind Speed</div>
        </div>
        <div class="weather-stat-card">
            <div class="weather-stat-icon">🌧️</div>
            <div class="weather-stat-value">{rain} <span style="font-size:0.75rem;">mm</span></div>
            <div class="weather-stat-label">Precipitation</div>
        </div>
        <div class="weather-stat-card">
            <div class="weather-stat-icon">☀️</div>
            <div class="weather-stat-value">{uv}</div>
            <div class="weather-stat-label">{uv_tag}</div>
        </div>
    </div>
    """

# Helper to render SOP policy alert
def render_sop_alert(citation, severity="LOW"):
    if not citation:
        return ""
    icon = {
        "CRITICAL": "🚨",
        "HIGH": "⚠️",
        "MEDIUM": "⚡",
        "LOW": "ℹ️"
    }.get(severity, "📜")

    return f"""
    <div class="sop-alert-card sop-alert-{severity}">
        <span style="font-size: 1.3rem;">{icon}</span>
        <div>
            <div style="font-weight: 700; font-size: 0.85rem; margin-bottom: 2px;">
                STRICT POLICY CITATION ({severity})
            </div>
            <div>{citation}</div>
        </div>
    </div>
    """

# Empty State: Show interactive starter cards if no messages yet
if len(st.session_state.messages) == 0:
    st.markdown('<div class="starter-header">✨ Try a Quick Safety Scenario:</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button("🚴 High UV Cycling\n\n*Bhopal around 1 PM*", use_container_width=True):
            user_input = "Is it safe to cycle today in Bhopal around 1 PM?"
    with c2:
        if st.button("🏍️ High Wind Commute\n\n*Mumbai Two-Wheeler*", use_container_width=True):
            user_input = "Can I ride my bike in Mumbai right now?"
    with c3:
        if st.button("👶 Toddler Park Walk\n\n*Delhi High Heat*", use_container_width=True):
            user_input = "Is it okay to take my toddler to the park in Delhi?"

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Weather Stats Cards
        if "weather_info" in msg and msg["weather_info"]:
            st.markdown(render_weather_grid(msg["weather_info"]), unsafe_allow_html=True)
            
        # SOP Policy Citation
        if "sop_citation" in msg and msg["sop_citation"]:
            sev = msg.get("severity", "LOW")
            st.markdown(render_sop_alert(msg["sop_citation"], sev), unsafe_allow_html=True)

# Chat Input Box
chat_input = st.chat_input("Ask about outdoor activity safety (e.g., 'Is it safe to run in Bangalore today?')")
if chat_input:
    user_input = chat_input

if user_input:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.chat_history_langchain.append(HumanMessage(content=user_input))
    
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process with LangGraph Agent
    with st.chat_message("assistant"):
        with st.spinner("Analyzing live weather data & evaluating SOP policies..."):
            try:
                agent = WeatherAdvisoryAgent(sops_file_path="sops.json")
                out = agent.run(
                    user_query=user_input,
                    history=st.session_state.chat_history_langchain,
                    location=st.session_state.last_location,
                    activity=st.session_state.last_activity
                )
                
                # Update session carried state
                if out.get("location"):
                    st.session_state.last_location = out.get("location")
                if out.get("activity"):
                    st.session_state.last_activity = out.get("activity")

                resp_text = out.get("final_response", "No response generated.")
                weather_facts = out.get("weather_data")
                citation = out.get("sop_citation")
                matched_sop = out.get("sop_matched")
                severity = matched_sop.get("severity", "LOW") if matched_sop else "LOW"

                # Display Response
                st.markdown(resp_text)

                if weather_facts:
                    st.markdown(render_weather_grid(weather_facts), unsafe_allow_html=True)

                if citation:
                    st.markdown(render_sop_alert(citation, severity), unsafe_allow_html=True)

                # Store assistant response in history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": resp_text,
                    "weather_info": weather_facts,
                    "sop_citation": citation,
                    "severity": severity
                })
                st.session_state.chat_history_langchain.append(AIMessage(content=resp_text))

            except Exception as err:
                error_msg = f"⚠️ **Error executing agent**: {str(err)}\n\nPlease ensure your `GROQ_API_KEY` is configured correctly in `.env` file."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
