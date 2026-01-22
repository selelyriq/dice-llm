"""Job Scout - Local-first job search assistant with market intelligence.

This is the main landing page for the multi-page Streamlit application.
Navigate to specific features using the sidebar.
"""

import streamlit as st
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Job Scout", page_icon="🎯", layout="wide", initial_sidebar_state="expanded"
)

# Header
st.title("🎯 Job Scout")
st.markdown("""
Welcome to **Job Scout** - your privacy-first job search and market intelligence platform.

All your data stays local in `~/.job-scout/` with smart retention policies.
""")

st.divider()

# Feature cards
st.subheader("Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 Job Search")
    st.markdown("""
    - Upload resume & LinkedIn profile
    - AI-powered query generation
    - Transparent job scoring & ranking
    - Match explanations & insights
    """)

    st.markdown("### 📜 Search History")
    st.markdown("""
    - View past searches
    - Rerun successful queries
    - Track your job search progress
    - Filter by date and score
    """)

with col2:
    st.markdown("### 📊 Market Intelligence")
    st.markdown("""
    - Analyze job market trends
    - Skill demand analysis
    - Salary distributions
    - No profile required
    """)

    st.markdown("### 📊 Profile Comparison")
    st.markdown("""
    - Track resume changes
    - Compare skill evolution
    - Auto-versioning (last 10)
    - Visual diff analysis
    """)

st.divider()

# Getting started
st.subheader("🚀 Getting Started")

st.markdown("""
1. **Configure Settings** (⚙️ in sidebar)
   - Add your Anthropic API key
   - Adjust retention policies (24hr default)

2. **Start Job Search** (🎯 in sidebar)
   - Upload your resume PDF
   - Optionally add LinkedIn profile
   - Generate AI queries
   - Execute search & view ranked results

3. **Analyze Market** (📊 in sidebar)
   - No profile needed
   - Enter job titles or skills
   - View demand trends & insights

4. **Track Progress** (📜 in sidebar)
   - Review search history
   - Rerun successful searches
""")

st.divider()

# Privacy notice
st.info("""
🔒 **Privacy First:** 
- All data stored locally in `~/.job-scout/`
- 24-hour cache by default (configurable)
- Auto-cleanup at 1GB
- Export your data anytime
""")

# Footer
st.caption("Job Scout v0.1.0 | Built with Streamlit, Claude, and Dice MCP")
