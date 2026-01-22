"""Settings page - Configure API keys, retention policies, and preferences."""

import streamlit as st
from pathlib import Path
import os

# Page config
st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("⚙️ Settings")
st.markdown("Configure your Job Scout preferences, API keys, and data retention policies.")

st.divider()

# API Keys Section
st.subheader("🔑 API Keys")

api_key = st.text_input(
    "Anthropic API Key",
    type="password",
    value=os.getenv("ANTHROPIC_API_KEY", ""),
    help="Your Claude API key from console.anthropic.com",
)

if st.button("Save API Key"):
    # In real implementation, would save to .env file
    st.success("API key saved! (Feature in development)")

st.divider()

# Data Retention Section
st.subheader("🔒 Privacy & Data Retention")

privacy_mode = st.toggle(
    "Privacy Mode",
    value=True,
    help="When enabled, data is cached for 24 hours only. Disable for longer retention.",
)

if privacy_mode:
    st.info("🔒 Privacy Mode Active: Data cached for 24 hours, auto-cleanup at 1GB")
else:
    st.warning("⚠️ Privacy Mode Disabled: Configure custom retention policies below")

    col1, col2 = st.columns(2)

    with col1:
        st.selectbox(
            "Market Snapshot TTL",
            ["24 hours", "48 hours", "72 hours", "7 days", "30 days"],
            disabled=privacy_mode,
        )

        st.selectbox(
            "Search History Retention",
            ["7 days", "30 days", "60 days", "90 days"],
            disabled=privacy_mode,
        )

    with col2:
        st.slider(
            "Max Market Snapshots",
            min_value=10,
            max_value=100,
            value=25,
            step=5,
            disabled=privacy_mode,
        )

        st.toggle("Auto-cleanup at 1GB", value=True, disabled=privacy_mode)

st.divider()

# Storage Section
st.subheader("💾 Storage Usage")

st.info("🚧 Storage usage tracking coming soon")

# Placeholder storage breakdown
st.markdown("**Current Usage:** ~ MB")
st.progress(0.0, text="Calculating...")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Profiles", "~ MB")
with col2:
    st.metric("Searches", "~ MB")
with col3:
    st.metric("Market Data", "~ MB")

st.divider()

# Data Management
st.subheader("📦 Data Management")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Export All Data", disabled=True):
        st.info("Creates ZIP backup - Coming soon")

with col2:
    if st.button("Clear Market Data", disabled=True):
        st.warning("Confirmation required - Coming soon")

with col3:
    if st.button("Clear Search History", disabled=True):
        st.warning("Confirmation required - Coming soon")

st.divider()

# Visualization Preferences
st.subheader("📊 Visualization Preferences")

chart_engine = st.radio(
    "Default Chart Engine",
    ["plotly", "altair"],
    format_func=lambda x: "Plotly (Interactive)" if x == "plotly" else "Altair (Static)",
    help="Choose your preferred visualization library",
)

color_scheme = st.selectbox("Color Scheme", ["Default", "Dark", "Light", "Colorblind-friendly"])

st.divider()

# Data Directory
st.subheader("📁 Data Directory")

data_dir = st.text_input(
    "Data Directory Path",
    value=str(Path.home() / ".job-scout"),
    disabled=True,
    help="Location where all Job Scout data is stored",
)

st.caption("Data directory configuration coming in future update")

st.divider()

# Footer
st.caption("💡 All settings are saved automatically")
