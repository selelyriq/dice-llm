"""Reusable UI components for Job Scout Streamlit pages."""

import streamlit as st
from typing import Optional, Dict, Any, List
from datetime import datetime
from core.schemas import ResumeProfile, JobMatch, ScoringWeights


def render_page_header(title: str, icon: str, description: str):
    """Render consistent page header across all pages."""
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    st.title(f"{icon} {title}")
    st.markdown(description)
    st.divider()


def render_profile_status(profile: Optional[ResumeProfile], namespace: str = ""):
    """
    Display current profile status with name and dates.

    Args:
        profile: Current resume profile
        namespace: Session state namespace for this component
    """
    if not profile:
        st.info("📄 No profile loaded. Upload your resume in the Job Search page.")
        return

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"**Current Profile:** {profile.name}")

    with col2:
        if hasattr(profile, "sources") and profile.sources.get("resume_date"):
            date_str = profile.sources["resume_date"]
            st.caption(f"📄 Resume: {date_str[:10]}")

    with col3:
        if hasattr(profile, "sources") and profile.sources.get("linkedin_date"):
            date_str = profile.sources["linkedin_date"]
            st.caption(f"💼 LinkedIn: {date_str[:10]}")


def render_score_breakdown(score_breakdown: Dict[str, float]):
    """
    Render score breakdown with progress bars.

    Args:
        score_breakdown: Dict of score components
    """
    score_labels = {
        "role_fit": "Role/Title Fit",
        "skill_overlap": "Skill Overlap",
        "seniority_match": "Seniority Match",
        "constraints_match": "Constraints Match",
        "freshness": "Freshness",
    }

    for key, label in score_labels.items():
        if key in score_breakdown:
            score = score_breakdown[key]
            st.progress(score / 100, text=f"{label}: {score:.0f}/100")


def render_job_card(match: JobMatch, namespace: str = ""):
    """
    Render a job match as an expandable card.

    Args:
        match: JobMatch object with job details and scores
        namespace: Session state namespace for this component
    """
    job = match.job
    score = match.total_score

    # Color code based on score
    if score >= 80:
        score_color = "🟢"
    elif score >= 60:
        score_color = "🟡"
    else:
        score_color = "🔴"

    title = job.get("title", "Unknown Title")
    company = job.get("companyName", "Unknown Company")

    with st.expander(f"{score_color} **{title}** at {company} - Score: {score:.0f}"):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**{title}**")
            st.markdown(f"🏢 {company}")
            location = job.get("location", "Unknown")
            st.caption(f"📍 {location}")

            if job.get("salary"):
                st.caption(f"💰 {job['salary']}")

        with col2:
            posted_date = job.get("postedDate", "Unknown")
            st.caption(f"📅 Posted: {posted_date}")

            if job.get("jobType"):
                st.caption(f"💼 {job['jobType']}")

        # Score breakdown
        st.subheader("Score Breakdown")
        render_score_breakdown(match.score_breakdown)

        # Matched skills
        if match.matched_skills:
            st.subheader("✅ Matched Skills")
            st.write(", ".join(match.matched_skills))

        # Missing keywords
        if match.missing_keywords:
            st.subheader("❌ Missing Keywords")
            st.write(", ".join(match.missing_keywords))

        # Match explanation
        if match.explanation:
            st.subheader("💡 Match Explanation")
            st.markdown(match.explanation)

        # Link to job
        if job.get("detailUrl"):
            st.link_button("View Job on Dice", job["detailUrl"])


def render_constraints_form(namespace: str = "job_search") -> Dict[str, Any]:
    """
    Render constraint filters form.

    Args:
        namespace: Session state namespace for storing values

    Returns:
        Dict of constraint values
    """
    state_key = f"{namespace}_constraints"

    if state_key not in st.session_state:
        st.session_state[state_key] = {}

    constraints = {}

    st.subheader("Search Constraints")

    # Workplace types
    constraints["workplace_types"] = st.multiselect(
        "Workplace Type",
        ["Remote", "Hybrid", "On-Site"],
        default=st.session_state[state_key].get("workplace_types", ["Remote"]),
        key=f"{namespace}_workplace",
    )

    # Employment types
    constraints["employment_types"] = st.multiselect(
        "Employment Type",
        ["FULLTIME", "CONTRACTS", "PARTTIME", "THIRD_PARTY"],
        default=st.session_state[state_key].get("employment_types", ["FULLTIME"]),
        key=f"{namespace}_employment",
    )

    # Location
    constraints["location"] = st.text_input(
        "Location (optional)",
        value=st.session_state[state_key].get("location", ""),
        placeholder="e.g., San Francisco, CA",
        key=f"{namespace}_location",
    )

    # Radius
    if constraints["location"]:
        constraints["radius"] = st.slider(
            "Search Radius (miles)",
            min_value=1,
            max_value=100,
            value=st.session_state[state_key].get("radius", 25),
            key=f"{namespace}_radius",
        )

    # Posted date
    constraints["posted_date"] = st.selectbox(
        "Posted Within",
        ["ONE", "THREE", "SEVEN"],
        index=["ONE", "THREE", "SEVEN"].index(
            st.session_state[state_key].get("posted_date", "THREE")
        ),
        format_func=lambda x: {"ONE": "1 day", "THREE": "3 days", "SEVEN": "7 days"}[x],
        key=f"{namespace}_posted",
    )

    # Store in session state
    st.session_state[state_key] = constraints

    return constraints


def render_storage_warning(usage_mb: float, threshold_mb: float = 500):
    """
    Display storage warning based on usage.

    Args:
        usage_mb: Current storage usage in MB
        threshold_mb: Warning threshold in MB
    """
    if usage_mb >= 900:
        st.error(
            f"⚠️ Storage usage is very high ({usage_mb:.1f} MB). "
            "Auto-cleanup will remove oldest data soon. "
            "Visit Settings to adjust retention policies."
        )
    elif usage_mb >= threshold_mb:
        st.warning(
            f"⚠️ Storage usage is {usage_mb:.1f} MB. "
            "Consider reviewing retention settings to free up space."
        )


def render_privacy_notice():
    """Display privacy notice about 24-hour default retention."""
    st.info(
        "🔒 **Privacy Mode Active:** Market data is cached for 24 hours by default. "
        "Visit Settings to adjust retention policies."
    )


def render_filter_sidebar(namespace: str = "filters") -> Dict[str, Any]:
    """
    Render common filter controls in sidebar.

    Args:
        namespace: Session state namespace

    Returns:
        Dict of filter values
    """
    with st.sidebar:
        st.header("Filters")

        filters = {}

        # Date range
        filters["date_from"] = st.date_input("From Date", key=f"{namespace}_date_from")

        filters["date_to"] = st.date_input(
            "To Date", value=datetime.now().date(), key=f"{namespace}_date_to"
        )

        # Min score
        filters["min_score"] = st.slider(
            "Minimum Score", min_value=0, max_value=100, value=0, key=f"{namespace}_min_score"
        )

        return filters
