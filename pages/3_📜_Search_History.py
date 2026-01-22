"""Search History page - View and manage past job searches."""

import streamlit as st
from pathlib import Path
import json
from datetime import datetime

# Page config
st.set_page_config(page_title="Search History", page_icon="📜", layout="wide")

st.title("📜 Search History")
st.markdown("View your past job searches, rerun successful queries, and track your progress.")

st.divider()

# Coming soon notice
st.info("🚧 **Coming Soon:** Full search history management features are under development.")

st.markdown("""
### Planned Features:
- **Timeline View**: Chronological list of all searches with dates
- **Search Details**: Expandable cards showing queries, constraints, and results
- **Quick Stats**: Total searches, average score, top matches
- **Filtering**: Filter by date range, score threshold, or keywords
- **Rerun Searches**: Load past constraints and queries back to Job Search page
- **Delete History**: Remove individual searches or clear all history

### How It Will Work:
1. View table of past searches with timestamp, queries, and result counts
2. Click any search to expand full details
3. Filter searches by date or minimum score
4. Click "Rerun Search" to load that search back into Job Search page
5. Delete individual searches or export history as JSON

### Data Storage:
- Searches stored in `~/.job-scout/searches/`
- Organized by month (e.g., `2026-01.jsonl`)
- Retention policy configurable in Settings
- JSONL format for easy parsing and analysis
""")

st.divider()

# Placeholder view
st.subheader("Recent Searches (Coming Soon)")

# Mock data for preview
mock_searches = [
    {
        "timestamp": "2026-01-22 14:30:00",
        "queries": ["Senior Python Developer", "Backend Engineer"],
        "total_results": 45,
        "top_score": 92,
    },
    {
        "timestamp": "2026-01-21 10:15:00",
        "queries": ["DevOps Engineer Remote", "Cloud Infrastructure"],
        "total_results": 38,
        "top_score": 88,
    },
]

for search in mock_searches:
    with st.expander(
        f"🔍 {search['timestamp']} - {search['total_results']} results (Top: {search['top_score']})",
        expanded=False,
    ):
        st.markdown(f"**Queries:** {', '.join(search['queries'])}")
        st.button("Rerun Search", key=search["timestamp"], disabled=True)
        st.button("Delete", key=f"del_{search['timestamp']}", disabled=True)

st.caption("Actual search history will appear here once you start using Job Search!")
