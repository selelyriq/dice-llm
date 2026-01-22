"""Market Intelligence page."""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
import asyncio
from datetime import datetime

from core.schemas import MarketQuery
from core.market import fetch_market_snapshot
from integrations.mcp_client import DiceMCPClient
from integrations.llm import ClaudeClient
from ui.components import render_page_header, render_privacy_notice
from ui.charts import (
    render_chart_with_toggle,
    create_skill_chart,
    create_salary_boxplot,
    create_workplace_distribution,
)


st.set_page_config(page_title="Market Intelligence", page_icon="📊", layout="wide")

# Initialize session state
if "market_namespace" not in st.session_state:
    st.session_state.market_namespace = {}
if "chart_engine" not in st.session_state:
    st.session_state.chart_engine = "plotly"

ns = st.session_state.market_namespace

# Header
render_page_header(
    "Market Intelligence",
    "📊",
    "Analyze job market trends without needing a resume. Search by keywords to discover in-demand skills, salary ranges, and emerging opportunities.",
)

# Privacy notice
render_privacy_notice()

# Chart engine toggle (in sidebar)
with st.sidebar:
    st.markdown("### Visualization Settings")
    current_engine = st.session_state.chart_engine
    new_engine = st.radio(
        "Chart Engine",
        ["plotly", "altair"],
        index=0 if current_engine == "plotly" else 1,
        help="Plotly: Interactive charts with hover/zoom\nAltair: Clean, static charts",
        key="global_chart_engine",
    )

    # Update session state if changed
    if new_engine != current_engine:
        st.session_state.chart_engine = new_engine
        st.rerun()

# Main content
st.markdown("---")

# Input section
st.markdown("### Search Parameters")

col1, col2 = st.columns([2, 1])

with col1:
    keywords_input = st.text_area(
        "Keywords (one per line)",
        value="Python Developer\nData Scientist\nMachine Learning Engineer",
        height=120,
        help="Enter job titles, skills, or roles to analyze. Each line is a separate keyword.",
    )

with col2:
    posted_date = st.selectbox(
        "Posted Date",
        ["ANY", "ONE", "TWO", "SEVEN", "FOURTEEN", "THIRTY"],
        index=0,
        help="Filter jobs by posting date",
    )

    jobs_per_query = st.number_input(
        "Jobs per Keyword",
        min_value=10,
        max_value=200,
        value=50,
        step=10,
        help="Maximum jobs to fetch per keyword",
    )

# Workplace types
workplace_types = st.multiselect(
    "Workplace Types",
    ["Remote", "Hybrid", "Onsite"],
    default=["Remote", "Hybrid"],
    help="Filter by workplace arrangement",
)

# Analyze button
analyze_button = st.button("🔍 Analyze Market Trends", type="primary", use_container_width=True)

# Process analysis
if analyze_button:
    # Parse keywords
    keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]

    if not keywords:
        st.error("Please enter at least one keyword.")
        st.stop()

    # Create query
    query = MarketQuery(
        keywords=keywords,
        workplace_types=workplace_types if workplace_types else [],
        posted_date=posted_date if posted_date != "ANY" else None,
        jobs_per_query=jobs_per_query,
    )

    # Store query
    ns["current_query"] = query

    # Fetch market data
    with st.spinner("🔍 Fetching job data and analyzing trends..."):
        try:
            # Initialize clients (sync wrappers for Streamlit)
            mcp_client = DiceMCPClient()
            claude_client = ClaudeClient()

            # Run async fetch
            snapshot = asyncio.run(
                fetch_market_snapshot(
                    query=query,
                    mcp_client=mcp_client,
                    claude_client=claude_client,
                    cache_ttl_hours=24,
                )
            )

            # Store snapshot
            ns["current_snapshot"] = snapshot

            st.success(
                f"✅ Analysis complete! Found {snapshot.total_jobs_found} jobs across {len(keywords)} keywords."
            )

        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            # Show more details in an expander for debugging
            with st.expander("Error Details"):
                import traceback

                st.code(traceback.format_exc())
            st.stop()

# Display results
if "current_snapshot" in ns:
    snapshot = ns["current_snapshot"]

    st.markdown("---")
    st.markdown("### Market Overview")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Jobs", snapshot.total_jobs_found)

    with col2:
        st.metric("Keywords Analyzed", len(snapshot.query.keywords))

    with col3:
        avg_jobs_per_keyword = (
            snapshot.total_jobs_found / len(snapshot.query.keywords)
            if snapshot.query.keywords
            else 0
        )
        st.metric("Avg Jobs/Keyword", f"{avg_jobs_per_keyword:.0f}")

    with col4:
        timestamp = datetime.fromisoformat(snapshot.timestamp)
        st.metric("Last Updated", timestamp.strftime("%Y-%m-%d %H:%M"))

    # Aggregate Overview
    st.markdown("---")
    st.markdown("### Aggregate Overview")
    st.markdown("*Combined analysis across all keywords*")

    agg_col1, agg_col2 = st.columns(2)

    with agg_col1:
        if snapshot.aggregate_skills:
            st.markdown("##### Top Skills Across All Jobs")
            # Convert to dict format expected by create_skill_chart
            agg_skills_dict = {s.skill: s.count for s in snapshot.aggregate_skills[:15]}
            render_chart_with_toggle(
                create_skill_chart,
                agg_skills_dict,
                top_n=15,
                chart_key="aggregate_skills",
            )

    with agg_col2:
        if snapshot.aggregate_workplace_distribution:
            st.markdown("##### Workplace Types Across All Jobs")
            render_chart_with_toggle(
                create_workplace_distribution,
                snapshot.aggregate_workplace_distribution,
                chart_key="aggregate_workplace",
            )

    # Trends per keyword
    st.markdown("---")
    st.markdown("### Trends by Keyword")

    for trend in snapshot.trends:
        with st.expander(f"**{trend.keyword}** ({trend.total_jobs} jobs)", expanded=True):
            # Metrics row
            tcol1, tcol2 = st.columns(2)

            with tcol1:
                if trend.avg_salary:
                    salary_text = f"${trend.avg_salary.min_salary:,.0f}"
                    if (
                        trend.avg_salary.max_salary
                        and trend.avg_salary.max_salary != trend.avg_salary.min_salary
                    ):
                        salary_text += f" - ${trend.avg_salary.max_salary:,.0f}"
                    st.markdown(f"**Average Salary:** {salary_text}")
                else:
                    st.markdown("**Average Salary:** Not available")

            with tcol2:
                if trend.top_skills:
                    top_skill = trend.top_skills[0]
                    st.markdown(f"**Top Skill:** {top_skill.skill} ({top_skill.percentage}%)")

            # Charts
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                # Top skills chart
                if trend.top_skills:
                    st.markdown(f"##### Top Skills for {trend.keyword}")
                    # Convert to dict format expected by create_skill_chart
                    skills_dict = {s.skill: s.count for s in trend.top_skills[:10]}
                    render_chart_with_toggle(
                        create_skill_chart,
                        skills_dict,
                        top_n=10,
                        chart_key=f"skills_{trend.keyword}",
                    )

            with chart_col2:
                # Workplace distribution
                if trend.workplace_distribution:
                    st.markdown("##### Workplace Types")
                    render_chart_with_toggle(
                        create_workplace_distribution,
                        trend.workplace_distribution,
                        chart_key=f"workplace_{trend.keyword}",
                    )

            # Location distribution
            if trend.location_distribution:
                st.markdown("##### Top Locations")
                loc_cols = st.columns(3)
                for idx, (location, count) in enumerate(
                    list(trend.location_distribution.items())[:6]
                ):
                    with loc_cols[idx % 3]:
                        st.markdown(f"- **{location}**: {count} jobs")

    # AI Insights
    st.markdown("---")
    st.markdown("### 🤖 AI Insights")

    with st.expander("View AI-Generated Market Analysis", expanded=True):
        st.markdown(snapshot.ai_insights)

    # Export button
    st.markdown("---")
    if st.button("📥 Export Market Data (CSV)", use_container_width=True):
        import csv
        from io import StringIO

        # Generate CSV
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)

        # Header
        writer.writerow(
            [
                "Keyword",
                "Total Jobs",
                "Avg Salary Min",
                "Avg Salary Max",
                "Top Skill",
                "Top Skill %",
            ]
        )

        # Data rows
        for trend in snapshot.trends:
            row = [
                trend.keyword,
                trend.total_jobs,
                f"${trend.avg_salary.min_salary:,.0f}" if trend.avg_salary else "N/A",
                f"${trend.avg_salary.max_salary:,.0f}"
                if trend.avg_salary and trend.avg_salary.max_salary
                else "N/A",
                trend.top_skills[0].skill if trend.top_skills else "N/A",
                f"{trend.top_skills[0].percentage}%" if trend.top_skills else "N/A",
            ]
            writer.writerow(row)

        # Download button
        st.download_button(
            label="Download CSV",
            data=csv_buffer.getvalue(),
            file_name=f"market_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

else:
    st.info("👆 Enter keywords above and click 'Analyze Market Trends' to begin.")

    # Example use cases
    st.markdown("---")
    st.markdown("### Example Use Cases")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **🎯 Career Planning**
        - Compare demand across roles
        - Identify high-growth skills
        - Understand salary expectations
        """)

    with col2:
        st.markdown("""
        **📚 Skill Development**
        - Find emerging technologies
        - Prioritize learning paths
        - Track certification value
        """)

    with col3:
        st.markdown("""
        **💼 Hiring Strategy**
        - Benchmark compensation
        - Understand talent supply
        - Optimize job postings
        """)
