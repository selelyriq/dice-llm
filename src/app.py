"""Main Streamlit application for ScriptClub Scout."""

import asyncio
import json
import streamlit as st
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

from core.schemas import (
    ResumeProfile,
    JobConstraints,
    ScoringWeights,
    JobMatch,
    SearchHistory,
)
from core.resume import (
    load_existing_profile,
    load_existing_linkedin,
    process_resume,
    get_profile_status,
    JOB_SCOUT_DIR,
)
from core.ranker import (
    generate_queries,
    rank_jobs,
    deduplicate_jobs,
    get_keyword_suggestions,
    explain_match,
)
from integrations.llm import ClaudeClient
from integrations.mcp_client import DiceMCPClient

# Page config
st.set_page_config(
    page_title="ScriptClub Scout",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "profile" not in st.session_state:
    st.session_state.profile = load_existing_profile()

if "queries" not in st.session_state:
    st.session_state.queries = []

if "job_matches" not in st.session_state:
    st.session_state.job_matches = []

if "search_executed" not in st.session_state:
    st.session_state.search_executed = False


def save_search_history(
    constraints: JobConstraints,
    queries_generated: List[str],
    queries_executed: List[str],
    matches: List[JobMatch],
):
    """Append search to history file."""
    history_path = JOB_SCOUT_DIR / "searches.jsonl"
    JOB_SCOUT_DIR.mkdir(exist_ok=True)

    history_entry = SearchHistory(
        timestamp=datetime.now(timezone.utc).isoformat(),
        constraints=constraints,
        queries_generated=queries_generated,
        queries_executed=queries_executed,
        total_results=len(matches),
        top_matches=matches[:10],
    )

    with open(history_path, "a") as f:
        f.write(history_entry.model_dump_json() + "\n")


def main():
    """Main application logic."""

    # Title
    st.title("🎯 ScriptClub Scout")
    st.markdown("*Local-first AI job search assistant powered by Dice MCP*")

    # Sidebar: Profile & Constraints
    with st.sidebar:
        st.header("📋 Your Profile")

        # Show existing profile status
        name, resume_date, linkedin_date = get_profile_status()
        if name or resume_date or linkedin_date:
            st.success(f"**Current Profile: {name or 'Unknown'}**")
            if resume_date:
                st.caption(f"Resume: {resume_date}")
            if linkedin_date:
                st.caption(f"LinkedIn: {linkedin_date}")
        else:
            st.info("No profile found. Upload your resume to get started!")

        # File uploads
        st.subheader("Upload Documents")
        resume_file = st.file_uploader("Resume PDF", type=["pdf"], key="resume_upload")
        linkedin_file = st.file_uploader(
            "LinkedIn PDF (optional)", type=["pdf"], key="linkedin_upload"
        )

        if st.button("Process Documents") and (resume_file or linkedin_file):
            with st.spinner("Extracting and normalizing profile..."):
                try:
                    # Save uploaded files temporarily
                    resume_path = None
                    linkedin_path = None

                    if resume_file:
                        resume_path = f"/tmp/resume_{datetime.now().timestamp()}.pdf"
                        with open(resume_path, "wb") as f:
                            f.write(resume_file.getbuffer())

                    if linkedin_file:
                        linkedin_path = f"/tmp/linkedin_{datetime.now().timestamp()}.pdf"
                        with open(linkedin_path, "wb") as f:
                            f.write(linkedin_file.getbuffer())

                    # Process with Claude
                    claude_client = ClaudeClient()
                    profile = process_resume(resume_path, linkedin_path, claude_client)

                    st.session_state.profile = profile
                    st.success("✅ Profile processed and saved!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Error processing documents: {str(e)}")

        st.divider()

        # Search Constraints
        st.subheader("🔍 Search Constraints")

        workplace_types = st.multiselect(
            "Workplace Type",
            options=["Remote", "Hybrid", "On-Site"],
            default=["Remote"],
        )

        employment_types = st.multiselect(
            "Employment Type",
            options=["FULLTIME", "CONTRACTS", "PARTTIME", "THIRD_PARTY"],
            default=["FULLTIME"],
        )

        min_salary = st.number_input(
            "Minimum Salary ($)", min_value=0, value=0, step=5000, help="Leave at 0 for no minimum"
        )

        location = st.text_input(
            "Location (optional)",
            placeholder="San Francisco, CA",
            help="Leave empty for remote-only search",
        )

        radius = st.slider(
            "Search Radius (miles)",
            min_value=0,
            max_value=100,
            value=25,
            disabled=not location,
        )

        posted_date = st.selectbox(
            "Posted Within",
            options=["ONE", "THREE", "SEVEN"],
            format_func=lambda x: {"ONE": "1 day", "THREE": "3 days", "SEVEN": "7 days"}[x],
            index=2,
        )

        sponsor_visa = st.checkbox("Requires Visa Sponsorship", value=False)
        easy_apply_only = st.checkbox("Easy Apply Only", value=False)

    # Main content: Three columns
    col1, col2, col3 = st.columns([1, 1, 1])

    # Column 1: Scoring Weights
    with col1:
        st.header("⚖️ Scoring Weights")
        st.caption("Adjust how jobs are ranked")

        role_fit = st.slider("Role/Title Fit", 0, 100, 25, help="Match with target titles")
        skill_overlap = st.slider(
            "Skill Overlap", 0, 100, 30, help="Your skills in job description"
        )
        seniority_match = st.slider(
            "Seniority Match", 0, 100, 15, help="Experience level alignment"
        )
        constraints_match = st.slider(
            "Constraints Match", 0, 100, 20, help="Remote/salary/location requirements"
        )
        freshness = st.slider("Freshness", 0, 100, 10, help="How recently posted")

        weights = ScoringWeights(
            role_fit=role_fit,
            skill_overlap=skill_overlap,
            seniority_match=seniority_match,
            constraints_match=constraints_match,
            freshness=freshness,
        )

        # Show normalized weights
        normalized = weights.normalize()
        st.caption(
            f"**Normalized:** Role {normalized['role_fit']:.0%}, "
            f"Skills {normalized['skill_overlap']:.0%}, "
            f"Seniority {normalized['seniority_match']:.0%}, "
            f"Constraints {normalized['constraints_match']:.0%}, "
            f"Fresh {normalized['freshness']:.0%}"
        )

    # Column 2: Query Generation
    with col2:
        st.header("🔎 Generated Queries")
        st.caption("AI-generated Dice searches (edit as needed)")

        if st.button("🤖 Generate Queries", disabled=not st.session_state.profile, type="primary"):
            with st.spinner("Generating queries..."):
                try:
                    claude_client = ClaudeClient()
                    constraints_dict = {
                        "workplace_types": workplace_types,
                        "employment_types": employment_types,
                        "location": location or None,
                        "remote_only": "Remote" in workplace_types and len(workplace_types) == 1,
                        "min_salary": min_salary if min_salary > 0 else None,
                    }

                    queries = generate_queries(
                        st.session_state.profile,
                        constraints_dict,
                        claude_client,
                    )

                    st.session_state.queries = queries
                    st.success(f"✅ Generated {len(queries)} queries!")

                except Exception as e:
                    st.error(f"Error generating queries: {str(e)}")

        # Display editable queries
        if st.session_state.queries:
            edited_queries = []
            for i, query in enumerate(st.session_state.queries):
                edited_query = st.text_area(
                    f"Query {i + 1}",
                    value=query,
                    height=80,
                    key=f"query_{i}",
                )
                if edited_query.strip():
                    edited_queries.append(edited_query.strip())

            st.session_state.queries = edited_queries

            # Execute search button
            if st.button("🚀 Execute Search", disabled=not edited_queries, type="primary"):
                with st.spinner("Searching Dice and ranking matches..."):
                    try:
                        claude_client = ClaudeClient()
                        mcp_client = DiceMCPClient()

                        all_jobs = []

                        # Execute each query
                        for query in edited_queries[:5]:  # Max 5 queries
                            try:
                                search_params = {
                                    "keyword": query,
                                    "jobs_per_page": 25,
                                    "page_number": 1,
                                }

                                if workplace_types:
                                    search_params["workplace_types"] = workplace_types
                                if employment_types:
                                    search_params["employment_types"] = employment_types
                                if location:
                                    search_params["location"] = location
                                    search_params["radius"] = radius
                                if posted_date:
                                    search_params["posted_date"] = posted_date
                                if sponsor_visa:
                                    search_params["willing_to_sponsor"] = True
                                if easy_apply_only:
                                    search_params["easy_apply"] = True

                                # Call MCP client
                                result = asyncio.run(mcp_client.search_jobs(**search_params))
                                jobs = result.get("data", [])
                                all_jobs.extend(jobs)

                            except Exception as e:
                                st.warning(f"Query '{query[:50]}...' failed: {str(e)}")
                                continue

                        # Deduplicate
                        unique_jobs = deduplicate_jobs(all_jobs)
                        st.info(
                            f"Found {len(unique_jobs)} unique jobs from {len(all_jobs)} total results"
                        )

                        # Rank jobs
                        matches = rank_jobs(
                            st.session_state.profile,
                            unique_jobs,
                            weights,
                            claude_client,
                            min_score=0.0,
                        )

                        st.session_state.job_matches = matches
                        st.session_state.search_executed = True

                        # Save to history
                        constraints = JobConstraints(
                            workplace_types=workplace_types,
                            employment_types=employment_types,
                            min_salary=min_salary if min_salary > 0 else None,
                            location=location or None,
                            radius=radius if location else None,
                            posted_date=posted_date,
                            willing_to_sponsor=sponsor_visa,
                            easy_apply=easy_apply_only,
                        )

                        save_search_history(
                            constraints,
                            st.session_state.queries,
                            edited_queries,
                            matches,
                        )

                        st.success(f"✅ Ranked {len(matches)} jobs!")

                    except Exception as e:
                        st.error(f"Error during search: {str(e)}")

    # Column 3: Results
    with col3:
        st.header("📊 Results")

        if st.session_state.search_executed and st.session_state.job_matches:
            matches = st.session_state.job_matches

            st.metric("Total Matches", len(matches))

            # Filter by minimum score
            min_score_filter = st.slider("Minimum Score", 0, 100, 0, help="Filter results")
            filtered_matches = [m for m in matches if m.total_score >= min_score_filter]

            st.caption(f"Showing {len(filtered_matches)} jobs")

            # Display matches
            for match in filtered_matches[:20]:  # Show top 20
                with st.expander(
                    f"**{match.title}** at {match.company} — Score: {match.total_score:.1f}"
                ):
                    st.markdown(f"**📍 Location:** {match.location}")
                    st.markdown(f"**💼 Workplace:** {', '.join(match.workplace_types)}")
                    if match.salary:
                        st.markdown(f"**💰 Salary:** {match.salary}")
                    st.markdown(f"**📅 Posted:** {match.posted_date}")

                    st.markdown("---")

                    # Score breakdown
                    st.markdown("**Score Breakdown:**")
                    breakdown = match.score_breakdown
                    for component, score in breakdown.items():
                        if component != "weighted_total":
                            st.progress(
                                score / 100,
                                text=f"{component.replace('_', ' ').title()}: {score:.1f}",
                            )

                    st.markdown("---")

                    # Matched skills
                    if match.matched_skills:
                        st.markdown(
                            f"**✅ Matched Skills:** {', '.join(match.matched_skills[:10])}"
                        )

                    # Missing keywords
                    if match.missing_keywords:
                        st.markdown(
                            f"**⚠️ Missing Keywords:** {', '.join(match.missing_keywords[:5])}"
                        )

                    st.markdown("---")

                    # Match explanation
                    st.markdown("**Why This Matched:**")
                    st.markdown(match.match_explanation)

                    st.markdown("---")

                    # Actions
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if match.url:
                            st.link_button("🔗 View Job", match.url)
                    with col_b:
                        if st.button("💡 Explain Match", key=f"explain_{match.job_id}"):
                            with st.spinner("Generating detailed explanation..."):
                                try:
                                    claude_client = ClaudeClient()
                                    explanation = explain_match(
                                        st.session_state.profile,
                                        match,
                                        claude_client,
                                    )
                                    st.markdown(explanation)
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")

        elif st.session_state.search_executed:
            st.info("No matches found. Try broadening your search.")

        else:
            st.info("Generate queries and execute search to see results.")

    # Bottom: Structured Commands
    st.divider()
    st.subheader("🎛️ Commands")

    cmd_col1, cmd_col2, cmd_col3, cmd_col4 = st.columns(4)

    with cmd_col1:
        if st.button("🔍 Find Roles", disabled=not st.session_state.profile):
            st.info("Use the 'Generate Queries' button above to find roles!")

    with cmd_col2:
        if st.button("📈 Broaden Search", disabled=not st.session_state.queries):
            st.info("Coming soon: Auto-broaden search by relaxing filters")

    with cmd_col3:
        if st.button("📉 Tighten Search", disabled=not st.session_state.job_matches):
            st.session_state.min_score_filter = 70
            st.rerun()

    with cmd_col4:
        if st.button("💼 Resume Keywords", disabled=not st.session_state.job_matches):
            with st.spinner("Analyzing top matches..."):
                try:
                    claude_client = ClaudeClient()
                    suggestions = get_keyword_suggestions(
                        st.session_state.profile,
                        st.session_state.job_matches[:10],
                        claude_client,
                    )
                    st.markdown("### 📝 Keyword Suggestions")
                    st.markdown(suggestions)
                except Exception as e:
                    st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
