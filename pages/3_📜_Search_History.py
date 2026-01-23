"""Search History page - View and manage past job searches."""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from core.storage import (
    load_all_searches,
    load_searches_in_range,
    delete_search,
    get_search_stats,
    load_settings,
)
from core.schemas import SearchHistory, JobMatch

# Page config
st.set_page_config(page_title="Search History", page_icon="⚡", layout="wide")

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

st.title("Search History")
st.markdown("View your past job searches, rerun successful queries, and track your progress.")

st.divider()

# Load settings to show retention policy
settings = load_settings()

# Sidebar: Filters
with st.sidebar:
    st.header("🔍 Filters")

    # Date range filter
    st.subheader("Date Range")
    filter_range = st.radio(
        "Time period",
        ["All Time", "Last 7 Days", "Last 30 Days", "Custom Range"],
        key="date_range_filter",
    )

    start_date = None
    end_date = None

    if filter_range == "Last 7 Days":
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
    elif filter_range == "Last 30 Days":
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    elif filter_range == "Custom Range":
        col1, col2 = st.columns(2)
        with col1:
            start_input = st.date_input("From", value=None, key="start_date")
            if start_input:
                start_date = datetime.combine(start_input, datetime.min.time()).replace(
                    tzinfo=timezone.utc
                )
        with col2:
            end_input = st.date_input("To", value=None, key="end_date")
            if end_input:
                end_date = datetime.combine(end_input, datetime.max.time()).replace(
                    tzinfo=timezone.utc
                )

    # Score filter
    st.subheader("Score Filter")
    min_score = st.slider(
        "Minimum top score", min_value=0, max_value=100, value=0, step=5, key="min_score_filter"
    )

    st.divider()

    # Retention policy notice
    st.subheader("⚙️ Data Retention")
    if settings.privacy_mode:
        st.info("🔒 **Privacy Mode ON**\n\nSearches auto-delete after 24 hours")
    else:
        st.info(f"📅 Retention: {settings.search_history_retention_days} days")

    st.caption("Change settings in the Settings page →")

# Load searches based on filters
if start_date or end_date:
    searches = load_searches_in_range(start_date, end_date)
else:
    searches = load_all_searches()

# Apply score filter
if min_score > 0:
    searches = [
        s
        for s in searches
        if s.top_matches and max(m.total_score for m in s.top_matches) >= min_score
    ]

# Sort by timestamp (most recent first)
searches = sorted(searches, key=lambda s: s.timestamp, reverse=True)

# Display stats
stats = get_search_stats()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Searches", stats["total_searches"])
with col2:
    st.metric("Jobs Found", stats["total_jobs_found"])
with col3:
    st.metric("Avg Score", f"{stats['average_score']}")
with col4:
    st.metric("Top Score", f"{stats['top_score']}")

if stats["date_range"]:
    st.caption(f"📅 Date Range: {stats['date_range']}")

st.divider()

# Display searches
if not searches:
    st.info("🔍 No search history found. Start searching for jobs to build your history!")
else:
    st.subheader(f"Search History ({len(searches)} searches)")

    for idx, search in enumerate(searches):
        # Parse timestamp
        try:
            dt = datetime.fromisoformat(search.timestamp.replace("Z", "+00:00"))
            timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            timestamp_str = search.timestamp

        # Get top score
        top_score = 0
        if search.top_matches:
            top_score = max(m.total_score for m in search.top_matches)

        # Create expander title
        expander_title = (
            f"🔍 {timestamp_str} - {search.total_results} results (Top Score: {top_score:.1f})"
        )

        with st.expander(expander_title, expanded=False):
            # Display queries
            st.markdown("### 📝 Queries Used")
            if search.queries_executed:
                for query in search.queries_executed:
                    st.code(query, language="text")
            elif search.queries_generated:
                for query in search.queries_generated:
                    st.code(query, language="text")
            else:
                st.caption("No queries recorded")

            # Display constraints
            st.markdown("### ⚙️ Search Constraints")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Workplace:** {', '.join(search.constraints.workplace_types)}")
                st.markdown(f"**Employment:** {', '.join(search.constraints.employment_types)}")
                if search.constraints.min_salary:
                    st.markdown(f"**Min Salary:** ${search.constraints.min_salary:,}")

            with col2:
                if search.constraints.location:
                    st.markdown(f"**Location:** {search.constraints.location}")
                    if search.constraints.radius:
                        st.markdown(f"**Radius:** {search.constraints.radius} miles")
                st.markdown(f"**Posted:** {search.constraints.posted_date or 'Any'}")
                if search.constraints.willing_to_sponsor:
                    st.markdown("**Visa Sponsorship:** Required")

            # Display top matches
            if search.top_matches:
                st.markdown(f"### 🎯 Top {len(search.top_matches)} Matches")

                for i, match in enumerate(search.top_matches, 1):
                    match_col1, match_col2, match_col3 = st.columns([3, 1, 1])

                    with match_col1:
                        st.markdown(f"**{i}. {match.title}** at {match.company}")
                        st.caption(f"📍 {match.location}")

                    with match_col2:
                        st.metric("Score", f"{match.total_score:.1f}")

                    with match_col3:
                        st.link_button("View Job", match.url, use_container_width=True)

            st.divider()

            # Action buttons
            action_col1, action_col2, action_col3 = st.columns([2, 1, 1])

            with action_col1:
                if st.button(
                    "🔄 Rerun Search",
                    key=f"rerun_{idx}",
                    help="Load these constraints back into Job Search page",
                ):
                    # Store in session state for Job Search page to pick up
                    st.session_state["rerun_constraints"] = search.constraints
                    st.session_state["rerun_queries"] = (
                        search.queries_executed or search.queries_generated
                    )
                    st.success("✅ Loaded! Navigate to Job Search page to execute.")

            with action_col2:
                if st.button(
                    "📋 Copy Queries", key=f"copy_{idx}", help="Copy queries to clipboard"
                ):
                    queries_text = "\n".join(search.queries_executed or search.queries_generated)
                    st.code(queries_text, language="text")
                    st.caption("👆 Queries above (copy manually)")

            with action_col3:
                if st.button(
                    "🗑️ Delete",
                    key=f"delete_{idx}",
                    type="secondary",
                    help="Delete this search from history",
                ):
                    if delete_search(search.timestamp):
                        st.success("Deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete search")

st.divider()

# Export and clear options
st.subheader("🔧 Actions")

action_col1, action_col2 = st.columns(2)

with action_col1:
    if st.button("📥 Export History as JSON", use_container_width=True):
        if searches:
            export_data = [s.model_dump() for s in searches]
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

            st.download_button(
                label="⬇️ Download JSON",
                data=str(export_data),
                file_name=f"search_history_{timestamp}.json",
                mime="application/json",
                use_container_width=True,
            )
        else:
            st.warning("No searches to export")

with action_col2:
    if st.button("🗑️ Clear All History", type="secondary", use_container_width=True):
        st.warning("⚠️ This will delete all search history!")
        if st.button("✅ Confirm Delete All", key="confirm_delete_all"):
            from core.storage import clear_category_data

            if clear_category_data("searches"):
                st.success("All search history cleared!")
                st.rerun()
            else:
                st.error("Failed to clear history")
