"""Profile Comparison page - Compare current profile with archived versions."""

import streamlit as st
from datetime import datetime
from typing import Optional, List

# Add src to path
import sys
from pathlib import Path

src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from core.resume import (
    load_existing_profile,
    load_profile_history,
    archive_current_profile,
    process_resume,
)
from core.schemas import ProfileVersion, ResumeProfile
from integrations.llm import ClaudeClient


# Page config
st.set_page_config(page_title="Profile Comparison", page_icon="⚡", layout="wide")

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


def render_page_header():
    """Render page header with title and description."""
    st.title("Profile Comparison")
    st.markdown(
        """
        Compare your current profile with previous versions to track changes in skills, 
        experience, and target roles over time. The system automatically archives your 
        profile when you upload a new resume or LinkedIn PDF.
        """
    )
    st.divider()


def render_profile_upload():
    """Render profile upload section."""
    st.subheader("📤 Update Profile")

    col1, col2 = st.columns(2)

    with col1:
        resume_file = st.file_uploader(
            "Upload New Resume (PDF)",
            type=["pdf"],
            key="resume_upload",
            help="Upload a new resume to update your profile and create a new version",
        )

    with col2:
        linkedin_file = st.file_uploader(
            "Upload New LinkedIn Profile (PDF)",
            type=["pdf"],
            key="linkedin_upload",
            help="Upload LinkedIn profile export to update your profile",
        )

    if resume_file or linkedin_file:
        if st.button("🔄 Process and Archive Current Version", type="primary"):
            with st.spinner("Processing profile and archiving current version..."):
                try:
                    # Archive current profile before updating
                    archived = archive_current_profile()
                    if archived:
                        st.success(f"✅ Current profile archived as version {archived.version_id}")

                    # Initialize Claude client (loads API key from .env automatically)
                    try:
                        claude_client = ClaudeClient()
                    except ValueError as e:
                        st.error(f"❌ {str(e)}")
                        st.info("💡 Make sure ANTHROPIC_API_KEY is set in your .env file.")
                        return

                    # Save uploaded files temporarily
                    resume_path = None
                    linkedin_path = None

                    if resume_file:
                        resume_path = f"/tmp/{resume_file.name}"
                        with open(resume_path, "wb") as f:
                            f.write(resume_file.read())

                    if linkedin_file:
                        linkedin_path = f"/tmp/{linkedin_file.name}"
                        with open(linkedin_path, "wb") as f:
                            f.write(linkedin_file.read())

                    # Process profile
                    _ = process_resume(resume_path, linkedin_path, claude_client)

                    st.success("✅ Profile updated successfully!")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error processing profile: {str(e)}")


def render_version_selector(history: List[ProfileVersion]) -> Optional[ProfileVersion]:
    """Render version selector dropdown."""
    if not history:
        st.info(
            "📋 No archived versions available yet. Upload a new profile to create the first version."
        )
        return None

    # Create options for dropdown
    version_options = {}
    for version in history:
        try:
            archived_dt = datetime.fromisoformat(version.archived_at.replace("Z", "+00:00"))
            label = f"{version.version_id} - {archived_dt.strftime('%Y-%m-%d %H:%M')} UTC"
            version_options[label] = version
        except Exception:
            label = version.version_id
            version_options[label] = version

    selected_label = st.selectbox(
        "📅 Select Previous Version to Compare",
        options=list(version_options.keys()),
        key="selected_version",
        help="Choose an archived version to compare with your current profile",
    )

    return version_options[selected_label] if selected_label else None


def render_profile_summary(profile: ResumeProfile, title: str):
    """Render profile summary card."""
    st.subheader(title)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Skills", len(profile.core_skills + profile.secondary_skills))

    with col2:
        st.metric("Years Experience", profile.years_experience_estimate)

    with col3:
        st.metric("Target Roles", len(profile.target_titles))

    with st.expander("📋 View Full Details"):
        st.write("**Name:**", profile.extracted_name or "Not specified")
        st.write(
            "**Target Titles:**",
            ", ".join(profile.target_titles) if profile.target_titles else "None",
        )
        st.write(
            "**Core Skills:**",
            ", ".join(profile.core_skills[:10]) if profile.core_skills else "None",
        )
        if profile.cloud_stack:
            st.write("**Cloud Platforms:**", ", ".join(profile.cloud_stack))
        st.write("**Last Updated:**", profile.last_updated)


def render_comparison_view(current: ProfileVersion, previous: ProfileVersion):
    """Render detailed comparison between two profile versions."""
    from core.resume import compare_profiles

    comparison = compare_profiles(current, previous)

    st.subheader("🔍 Detailed Comparison")

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        skills_delta = comparison["total_skills_current"] - comparison["total_skills_previous"]
        st.metric(
            "Total Skills",
            comparison["total_skills_current"],
            delta=skills_delta,
            delta_color="normal",
        )

    with col2:
        st.metric(
            "Skills Added",
            len(comparison["skills_added"]),
            delta=len(comparison["skills_added"]) if len(comparison["skills_added"]) > 0 else None,
            delta_color="normal",
        )

    with col3:
        st.metric(
            "Skills Removed",
            len(comparison["skills_removed"]),
            delta=-len(comparison["skills_removed"])
            if len(comparison["skills_removed"]) > 0
            else None,
            delta_color="inverse",
        )

    with col4:
        exp_delta = comparison["experience_change"]
        st.metric(
            "Experience",
            f"{current.profile.years_experience_estimate} yrs",
            delta=f"{exp_delta:+d} yrs" if exp_delta != 0 else None,
            delta_color="normal",
        )

    # Skills changes
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ Skills Added")
        if comparison["skills_added"]:
            for skill in comparison["skills_added"]:
                st.markdown(f"- :green[**{skill}**]")
        else:
            st.info("No skills added")

    with col2:
        st.markdown("### ❌ Skills Removed")
        if comparison["skills_removed"]:
            for skill in comparison["skills_removed"]:
                st.markdown(f"- :red[**{skill}**]")
        else:
            st.info("No skills removed")

    # Title changes
    if comparison["title_changes"]:
        st.markdown("---")
        st.markdown("### 🎯 Target Title Changes")
        for change in comparison["title_changes"]:
            if change["type"] == "added":
                st.markdown(f"- :green[**Added:** {change['title']}]")
            else:
                st.markdown(f"- :red[**Removed:** {change['title']}]")

    # Keyword density
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔑 Keyword Density")
        keyword_delta = (
            comparison["keyword_density_current"] - comparison["keyword_density_previous"]
        )
        st.metric(
            "Current Keywords",
            comparison["keyword_density_current"],
            delta=keyword_delta,
            delta_color="normal",
        )
        if current.profile.keywords_to_emphasize:
            with st.expander("View Current Keywords"):
                st.write(", ".join(current.profile.keywords_to_emphasize))

    with col2:
        st.markdown("### 📊 Previous Keywords")
        st.metric("Previous Keywords", comparison["keyword_density_previous"])
        if previous.profile.keywords_to_emphasize:
            with st.expander("View Previous Keywords"):
                st.write(", ".join(previous.profile.keywords_to_emphasize))


def render_timeline_chart(history: List[ProfileVersion], current_profile: Optional[ResumeProfile]):
    """Render timeline chart showing profile evolution."""
    st.subheader("📈 Profile Evolution Timeline")

    # Prepare data for chart
    timeline_data = []

    # Add historical versions
    for version in reversed(history):  # Oldest to newest
        try:
            archived_dt = datetime.fromisoformat(version.archived_at.replace("Z", "+00:00"))
            total_skills = len(version.profile.core_skills + version.profile.secondary_skills)
            timeline_data.append(
                {
                    "Date": archived_dt.strftime("%Y-%m-%d"),
                    "Total Skills": total_skills,
                    "Core Skills": len(version.profile.core_skills),
                    "Years Experience": version.profile.years_experience_estimate,
                    "Version": version.version_id,
                }
            )
        except Exception:
            continue

    # Add current profile
    if current_profile:
        try:
            current_dt = datetime.fromisoformat(current_profile.last_updated.replace("Z", "+00:00"))
            total_skills = len(current_profile.core_skills + current_profile.secondary_skills)
            timeline_data.append(
                {
                    "Date": current_dt.strftime("%Y-%m-%d"),
                    "Total Skills": total_skills,
                    "Core Skills": len(current_profile.core_skills),
                    "Years Experience": current_profile.years_experience_estimate,
                    "Version": "Current",
                }
            )
        except Exception:
            pass

    if not timeline_data:
        st.info("📊 No timeline data available yet. Create more profile versions to see evolution.")
        return

    # Use Streamlit's built-in line chart
    import pandas as pd

    df = pd.DataFrame(timeline_data)

    # Display charts
    tab1, tab2, tab3 = st.tabs(["📊 Skills Over Time", "💼 Experience Over Time", "📋 Data Table"])

    with tab1:
        st.line_chart(df.set_index("Date")[["Total Skills", "Core Skills"]])

    with tab2:
        st.line_chart(df.set_index("Date")["Years Experience"])

    with tab3:
        st.dataframe(df, use_container_width=True)


def main():
    """Main function for Profile Comparison page."""
    render_page_header()

    # Load current profile and history
    current_profile = load_existing_profile()
    history = load_profile_history()

    # Profile upload section
    with st.expander("📤 Upload New Profile", expanded=not current_profile):
        render_profile_upload()

    if not current_profile:
        st.warning(
            "⚠️ No current profile found. Please upload a resume or LinkedIn profile to get started."
        )
        return

    # Create current version wrapper
    current_version = ProfileVersion(
        version_id="current",
        profile=current_profile,
        archived_at=current_profile.last_updated,
        change_summary=None,
    )

    st.markdown("---")

    # Two-column comparison view
    st.subheader("🔄 Profile Comparison")

    if not history:
        st.info(
            "📋 No archived versions available yet. Upload a new profile to create your first archived version."
        )

        # Show current profile only
        render_profile_summary(current_profile, "📄 Current Profile")
    else:
        # Version selector
        selected_previous = render_version_selector(history)

        if selected_previous:
            # Two-column layout
            col1, col2 = st.columns(2)

            with col1:
                render_profile_summary(current_profile, "📄 Current Profile")

            with col2:
                render_profile_summary(selected_previous.profile, "📅 Selected Version")

            st.markdown("---")

            # Detailed comparison
            render_comparison_view(current_version, selected_previous)

    # Timeline chart
    st.markdown("---")
    render_timeline_chart(history, current_profile)

    # Footer info
    st.markdown("---")
    st.info(
        f"💾 **Version Management:** The system automatically keeps the last 10 profile versions. "
        f"Currently storing {len(history)} archived version(s)."
    )


if __name__ == "__main__":
    main()
