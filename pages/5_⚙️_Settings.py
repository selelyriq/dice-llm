"""Settings page - Configure API keys, retention policies, and preferences."""

import streamlit as st
from pathlib import Path
import os
import sys

# Add src to path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from core.storage import (
    calculate_storage_usage,
    load_settings,
    save_settings,
    enforce_retention_policies,
    auto_cleanup_if_needed,
    export_all_data,
    clear_category_data,
)
from core.schemas import StorageSettings

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

# Load current settings
if "storage_settings" not in st.session_state:
    st.session_state.storage_settings = load_settings()

settings = st.session_state.storage_settings

privacy_mode = st.toggle(
    "Privacy Mode",
    value=settings.privacy_mode,
    key="privacy_mode_toggle",
    help="When enabled, data is cached for 24 hours only. Disable for longer retention.",
)

# Update settings if changed
if privacy_mode != settings.privacy_mode:
    settings.privacy_mode = privacy_mode
    save_settings(settings)

if privacy_mode:
    st.info("🔒 Privacy Mode Active: Data cached for 24 hours, auto-cleanup at 1GB")
else:
    st.warning("⚠️ Privacy Mode Disabled: Configure custom retention policies below")

    col1, col2 = st.columns(2)

    with col1:
        ttl_options = {
            "24 hours": 24,
            "48 hours": 48,
            "72 hours": 72,
            "7 days": 168,
            "30 days": 720,
        }
        ttl_label = st.selectbox(
            "Market Snapshot TTL",
            list(ttl_options.keys()),
            index=0,
            disabled=privacy_mode,
        )
        settings.cache_ttl_hours = ttl_options[ttl_label]

        retention_options = {
            "7 days": 7,
            "30 days": 30,
            "60 days": 60,
            "90 days": 90,
        }
        retention_label = st.selectbox(
            "Search History Retention",
            list(retention_options.keys()),
            index=1,
            disabled=privacy_mode,
        )
        settings.search_history_retention_days = retention_options[retention_label]

    with col2:
        settings.max_market_snapshots = st.slider(
            "Max Market Snapshots",
            min_value=10,
            max_value=100,
            value=settings.max_market_snapshots,
            step=5,
            disabled=privacy_mode,
        )

        settings.auto_cleanup = st.toggle(
            "Auto-cleanup at 1GB",
            value=settings.auto_cleanup,
            disabled=privacy_mode,
        )

    # Save settings if changed
    if st.button("💾 Save Retention Settings"):
        save_settings(settings)
        st.success("✅ Retention settings saved!")

st.divider()

# Storage Section
st.subheader("💾 Storage Usage")

# Calculate storage usage
with st.spinner("Calculating storage usage..."):
    usage = calculate_storage_usage()

total_mb = usage["total"]
profiles_mb = usage["profiles"]
searches_mb = usage["searches"]
market_mb = usage["market"]

# Determine warning level
warning_threshold = 500  # MB
critical_threshold = 900  # MB

if total_mb >= critical_threshold:
    st.error(f"🔴 **Storage Critical:** {total_mb:.1f} MB / 1024 MB (Auto-cleanup will run soon)")
elif total_mb >= warning_threshold:
    st.warning(f"🟡 **Storage Warning:** {total_mb:.1f} MB / 1024 MB")
else:
    st.success(f"✅ **Storage Healthy:** {total_mb:.1f} MB / 1024 MB")

# Progress bar
progress_value = min(total_mb / 1024, 1.0)
st.progress(progress_value, text=f"Using {total_mb:.1f} MB of recommended 1024 MB limit")

# Storage breakdown
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Profiles", f"{profiles_mb:.1f} MB")
with col2:
    st.metric("Searches", f"{searches_mb:.1f} MB")
with col3:
    st.metric("Market Data", f"{market_mb:.1f} MB")

# Cleanup actions
if total_mb >= warning_threshold:
    st.info("💡 Consider clearing old data or running manual cleanup to free up space.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Run Retention Policy Cleanup"):
            with st.spinner("Cleaning up old data..."):
                deleted = enforce_retention_policies(settings)
                total_deleted = sum(deleted.values())
                if total_deleted > 0:
                    st.success(f"✅ Cleaned up {total_deleted} items: {deleted}")
                    st.rerun()
                else:
                    st.info("No items to clean up based on current retention policies.")

    with col2:
        if st.button("🗑️ Force Auto-Cleanup (1GB threshold)"):
            with st.spinner("Running auto-cleanup..."):
                deleted = auto_cleanup_if_needed()
                total_deleted = sum(deleted.values())
                if total_deleted > 0:
                    st.success(f"✅ Deleted {total_deleted} old files to free space")
                    st.rerun()
                else:
                    st.info("Storage is below threshold, no cleanup needed.")

st.divider()

# Data Management
st.subheader("📦 Data Management")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Export All Data"):
        with st.spinner("Creating backup..."):
            try:
                export_path = export_all_data()
                st.success(f"✅ Backup created: {export_path.name}")
                st.info(f"📁 Location: {export_path}")
            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")

with col2:
    if st.button("🗑️ Clear Market Data"):
        if st.session_state.get("confirm_clear_market"):
            with st.spinner("Clearing market data..."):
                if clear_category_data("market"):
                    st.success("✅ Market data cleared!")
                    st.session_state.confirm_clear_market = False
                    st.rerun()
                else:
                    st.error("❌ Failed to clear market data")
        else:
            st.session_state.confirm_clear_market = True
            st.warning("⚠️ Click again to confirm deletion")

with col3:
    if st.button("🗑️ Clear Search History"):
        if st.session_state.get("confirm_clear_searches"):
            with st.spinner("Clearing search history..."):
                if clear_category_data("searches"):
                    st.success("✅ Search history cleared!")
                    st.session_state.confirm_clear_searches = False
                    st.rerun()
                else:
                    st.error("❌ Failed to clear search history")
        else:
            st.session_state.confirm_clear_searches = True
            st.warning("⚠️ Click again to confirm deletion")

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
