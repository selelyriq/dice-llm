"""Visualization library with dual-engine support (Plotly/Altair)."""

from typing import Dict, List, Literal, Any
import pandas as pd
import streamlit as st

# Import both visualization libraries
try:
    import plotly.express as px
    import plotly.graph_objects as go

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import altair as alt

    ALTAIR_AVAILABLE = True
except ImportError:
    ALTAIR_AVAILABLE = False


def get_chart_engine() -> Literal["plotly", "altair"]:
    """Get current chart engine preference from session state."""
    if "chart_engine" not in st.session_state:
        # Default to Plotly if available, otherwise Altair
        st.session_state.chart_engine = "plotly" if PLOTLY_AVAILABLE else "altair"
    return st.session_state.chart_engine


def render_chart_with_toggle(chart_func, *args, chart_key=None, **kwargs):
    """
    Wrapper that renders chart using the global engine preference.
    Note: The chart engine toggle should be placed once at the page level, not per chart.

    Args:
        chart_func: Chart creation function
        *args: Arguments passed to chart function
        chart_key: Unique key for this chart instance (required for multiple charts)
        **kwargs: Keyword arguments passed to chart function
    """
    # Generate unique key if not provided
    if chart_key is None:
        chart_key = f"{chart_func.__name__}_{id(args)}"

    # Create chart with selected engine
    chart = chart_func(*args, engine=get_chart_engine(), **kwargs)

    # Display the chart
    if chart is not None:
        engine = get_chart_engine()
        if engine == "plotly":
            st.plotly_chart(chart, use_container_width=True, key=chart_key)
        elif engine == "altair":
            st.altair_chart(chart, use_container_width=True, key=chart_key)

    return chart


def create_skill_chart(
    skill_counts: Dict[str, int], engine: Literal["plotly", "altair"] = "plotly", top_n: int = 20
) -> Any:
    """
    Create horizontal bar chart of top skills.

    Args:
        skill_counts: Dict mapping skill names to counts
        engine: Visualization engine to use
        top_n: Number of top skills to show

    Returns:
        Plotly or Altair chart object
    """
    # Sort and get top N skills
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    df = pd.DataFrame(sorted_skills, columns=["Skill", "Count"])

    if engine == "plotly" and PLOTLY_AVAILABLE:
        fig = px.bar(
            df,
            x="Count",
            y="Skill",
            orientation="h",
            title=f"Top {top_n} Skills in Demand",
            color="Count",
            color_continuous_scale="Blues",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
        return fig

    elif engine == "altair" and ALTAIR_AVAILABLE:
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("Count:Q", title="Number of Jobs"),
                y=alt.Y("Skill:N", sort="-x", title="Skill"),
                color=alt.Color("Count:Q", scale=alt.Scale(scheme="blues")),
                tooltip=["Skill", "Count"],
            )
            .properties(title=f"Top {top_n} Skills in Demand", height=600)
        )
        return chart

    else:
        st.error(f"Chart engine '{engine}' not available")
        return None


def create_salary_boxplot(
    salaries: List[Dict[str, Any]], engine: Literal["plotly", "altair"] = "plotly"
) -> Any:
    """
    Create box plot of salary distributions.

    Args:
        salaries: List of salary dicts with 'min', 'max', 'currency'
        engine: Visualization engine to use

    Returns:
        Plotly or Altair chart object
    """
    # Prepare data
    salary_data = []
    for sal in salaries:
        if sal.get("min"):
            salary_data.append({"value": sal["min"], "type": "Minimum"})
        if sal.get("max"):
            salary_data.append({"value": sal["max"], "type": "Maximum"})

    if not salary_data:
        st.info("No salary data available")
        return None

    df = pd.DataFrame(salary_data)

    if engine == "plotly" and PLOTLY_AVAILABLE:
        fig = px.box(
            df,
            y="value",
            x="type",
            title="Salary Distribution",
            labels={"value": "Salary (USD)", "type": ""},
            color="type",
        )
        fig.update_layout(height=400)
        return fig

    elif engine == "altair" and ALTAIR_AVAILABLE:
        chart = (
            alt.Chart(df)
            .mark_boxplot()
            .encode(
                x=alt.X("type:N", title=""),
                y=alt.Y("value:Q", title="Salary (USD)"),
                color="type:N",
            )
            .properties(title="Salary Distribution", height=400)
        )
        return chart

    else:
        st.error(f"Chart engine '{engine}' not available")
        return None


def create_workplace_distribution(
    workplace_counts: Dict[str, int], engine: Literal["plotly", "altair"] = "plotly"
) -> Any:
    """
    Create pie chart of workplace type distribution.

    Args:
        workplace_counts: Dict mapping workplace types to counts
        engine: Visualization engine to use

    Returns:
        Plotly or Altair chart object
    """
    df = pd.DataFrame(list(workplace_counts.items()), columns=["Type", "Count"])

    if engine == "plotly" and PLOTLY_AVAILABLE:
        fig = px.pie(
            df,
            values="Count",
            names="Type",
            title="Workplace Type Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        return fig

    elif engine == "altair" and ALTAIR_AVAILABLE:
        chart = (
            alt.Chart(df)
            .mark_arc()
            .encode(
                theta=alt.Theta("Count:Q"), color=alt.Color("Type:N"), tooltip=["Type", "Count"]
            )
            .properties(title="Workplace Type Distribution", height=400)
        )
        return chart

    else:
        st.error(f"Chart engine '{engine}' not available")
        return None


def create_trend_timeseries(
    trend_data: List[Dict[str, Any]], engine: Literal["plotly", "altair"] = "plotly"
) -> Any:
    """
    Create line chart showing trends over time.

    Args:
        trend_data: List of dicts with 'date', 'metric', 'value'
        engine: Visualization engine to use

    Returns:
        Plotly or Altair chart object
    """
    df = pd.DataFrame(trend_data)

    if df.empty:
        st.info("No trend data available")
        return None

    df["date"] = pd.to_datetime(df["date"])

    if engine == "plotly" and PLOTLY_AVAILABLE:
        fig = px.line(
            df,
            x="date",
            y="value",
            color="metric",
            title="Market Trends Over Time",
            labels={"date": "Date", "value": "Count", "metric": "Metric"},
        )
        fig.update_layout(height=400)
        return fig

    elif engine == "altair" and ALTAIR_AVAILABLE:
        chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("value:Q", title="Count"),
                color="metric:N",
                tooltip=["date", "metric", "value"],
            )
            .properties(title="Market Trends Over Time", height=400)
        )
        return chart

    else:
        st.error(f"Chart engine '{engine}' not available")
        return None
