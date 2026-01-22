"""Profile Comparison page - Track resume changes over time."""

import streamlit as st
from pathlib import Path

# Page config
st.set_page_config(page_title="Profile Comparison", page_icon="📊", layout="wide")

st.title("📊 Profile Comparison")
st.markdown("Track how your resume evolves over time with automatic versioning.")

st.divider()

# Coming soon notice
st.info(
    "🚧 **Coming Soon:** Profile comparison and version tracking features are under development."
)

st.markdown("""
### Planned Features:
- **Automatic Versioning**: Last 10 profile versions saved automatically
- **Side-by-Side Comparison**: Visual diff showing current vs selected version
- **Skill Evolution**: Track skill additions and removals with color coding
- **Timeline View**: Chart showing skill count and changes over time
- **Keyword Density**: Compare keyword frequency between versions
- **Experience Changes**: Highlight title and experience updates

### How It Will Work:
1. Each time you upload a new resume, previous version is automatically archived
2. Select any of your last 10 versions from dropdown
3. View side-by-side comparison with color-coded changes:
   - 🟢 Green: Skills/keywords added
   - 🔴 Red: Skills/keywords removed
   - 🟡 Yellow: Modified content
4. See "Resume Evolution" timeline showing trends over time
5. Export comparison report as PDF or Markdown

### Version Management:
- Last 10 versions kept automatically
- Stored in `~/.job-scout/profile/history/`
- Timestamp-based filenames
- Oldest version deleted when limit reached
- No manual snapshots needed
""")

st.divider()

# Placeholder comparison
st.subheader("Compare Versions (Coming Soon)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📄 Current Profile")
    st.caption("Upload a resume in Job Search to enable comparisons")

with col2:
    st.markdown("### 📄 Previous Version")
    st.selectbox(
        "Select version to compare",
        ["2026-01-20 14:30", "2026-01-15 10:45", "2026-01-10 09:20"],
        disabled=True,
    )

st.divider()

st.markdown("### Resume Evolution Timeline (Coming Soon)")
st.caption("Timeline chart showing skill count and major changes will appear here")

st.info(
    "💡 **Tip:** Upload your first resume in Job Search to start tracking versions automatically!"
)
