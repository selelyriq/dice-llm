"""ScriptClub Scout - Local-first job search assistant with market intelligence.

This is the main landing page for the multi-page Streamlit application.
Navigate to specific features using the sidebar.
"""

import streamlit as st

# Page config
st.set_page_config(
    page_title="ScriptClub Scout", page_icon="🎯", layout="wide", initial_sidebar_state="expanded"
)

# Glass-morphism styling
st.markdown(
    """
<style>
    .stApp { background: #000000 !important; }
    .main .block-container { background: linear-gradient(180deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.03) 50%, transparent 100%); padding-top: 3rem !important; border-radius: 20px; }
    section[data-testid="stSidebar"] { background: rgba(15, 20, 35, 0.4) !important; backdrop-filter: blur(20px) saturate(180%) !important; -webkit-backdrop-filter: blur(20px) saturate(180%) !important; border-right: 1px solid rgba(255, 255, 255, 0.2) !important; box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3) !important; }
    section[data-testid="stSidebar"] > div { background: transparent !important; }
    [data-testid="stExpander"] { background: rgba(102, 126, 234, 0.05) !important; backdrop-filter: blur(10px) !important; -webkit-backdrop-filter: blur(10px) !important; border: 1px solid rgba(255, 255, 255, 1) !important; border-radius: 15px !important; padding: 1rem !important; margin: 1rem 0 !important; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important; }
    [data-testid="stExpander"]:hover { background: rgba(102, 126, 234, 0.08) !important; border-color: rgba(255, 255, 255, 1) !important; }
    [data-testid="stMetric"] { background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15)) !important; backdrop-filter: blur(15px) !important; border-radius: 15px !important; padding: 1.5rem !important; border: 1px solid rgba(255, 255, 255, 1) !important; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important; }
    [data-testid="stAlert"] { background: rgba(102, 126, 234, 0.08) !important; backdrop-filter: blur(15px) !important; border: 1px solid rgba(255, 255, 255, 1) !important; border-radius: 15px !important; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important; }
    h1 { color: #ffffff !important; font-weight: 700 !important; text-shadow: 0 0 30px rgba(102, 126, 234, 0.3) !important; }
    h2, h3 { color: #667eea !important; font-weight: 600 !important; }
    p, li, span, div { color: #ffffff !important; }
    .stButton > button { background: linear-gradient(135deg, rgba(102, 126, 234, 0.8), rgba(118, 75, 162, 0.8)) !important; border: 1px solid rgba(102, 126, 234, 0.5) !important; border-radius: 10px !important; color: white !important; transition: all 0.3s ease !important; }
    .stButton > button:hover { background: linear-gradient(135deg, rgba(102, 126, 234, 1), rgba(118, 75, 162, 1)) !important; box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4) !important; transform: translateY(-2px) !important; }
    [data-testid="column"] { background: rgba(255, 255, 255, 0.02); border-radius: 15px; padding: 1.5rem; border: 1px solid rgba(255, 255, 255, 1) !important; }
    [data-testid="stDataFrame"], [data-testid="stTable"] { border: 1px solid rgba(255, 255, 255, 1) !important; border-radius: 10px !important; }
    [data-testid="stTabs"] { border-bottom: 2px solid rgba(255, 255, 255, 1) !important; }
    [data-testid="stFileUploader"] { border: 1px solid rgba(255, 255, 255, 1) !important; border-radius: 10px !important; }
    div[class*="css"] { border-color: rgba(255, 255, 255, 0.2) !important; }
    textarea, input[type="text"], input[type="number"], select { border-color: rgba(255, 255, 255, 0.2) !important; }
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] > div, div[data-baseweb="textarea"] > div { border-color: rgba(255, 255, 255, 0.2) !important; }
    div[data-baseweb="tag"] { border-color: rgba(255, 255, 255, 0.2) !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# Header
st.title("ScriptClub Scout")
st.markdown("""
Welcome to **ScriptClub Scout** - your privacy-first job search and market intelligence platform.

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
st.subheader("Getting Started")

st.markdown("""
1. **Configure Settings** (in sidebar)
   - Add your Anthropic API key
   - Adjust retention policies (24hr default)

2. **Start Job Search** (in sidebar)
   - Upload your resume PDF
   - Optionally add LinkedIn profile
   - Generate AI queries
   - Execute search & view ranked results

3. **Analyze Market** (in sidebar)
   - No profile needed
   - Enter job titles or skills
   - View demand trends & insights

4. **Track Progress** (in sidebar)
   - Review search history
   - Rerun successful searches
""")

st.divider()

# Privacy notice
st.info("""
**Privacy First:** 
- All data stored locally in `~/.job-scout/`
- 24-hour cache by default (configurable)
- Auto-cleanup at 1GB
- Export your data anytime
""")

# Footer
st.caption("ScriptClub Scout v0.1.0 | Built with Streamlit, Claude, and Dice MCP")
