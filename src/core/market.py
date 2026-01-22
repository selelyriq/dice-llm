"""Market intelligence analysis module."""

import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import Counter

from core.schemas import (
    MarketQuery,
    JobTrend,
    MarketSnapshot,
    SkillFrequency,
    SalaryRange,
)
from integrations.mcp_client import DiceMCPClient
from integrations.llm import ClaudeClient
from core.prompts import BATCH_MARKET_ANALYSIS_PROMPT, generate_market_insights


# Storage directory
MARKET_DIR = Path.home() / ".job-scout" / "market"
MARKET_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOTS_PATH = MARKET_DIR / "snapshots.jsonl"
CACHE_PATH = MARKET_DIR / "trends_cache.json"


async def fetch_market_snapshot(
    query: MarketQuery,
    mcp_client: DiceMCPClient,
    claude_client: ClaudeClient,
    cache_ttl_hours: int = 24,
) -> MarketSnapshot:
    """
    Fetch and analyze market snapshot for given query.

    Args:
        query: Market query parameters
        mcp_client: Dice MCP client
        claude_client: Claude AI client
        cache_ttl_hours: Cache time-to-live in hours

    Returns:
        MarketSnapshot with trends and insights
    """
    # Check cache first
    cached = load_cached_snapshot(query, cache_ttl_hours)
    if cached:
        return cached

    # Fetch jobs via MCP
    # Prepare search params - only include non-empty values
    search_params = {
        "keywords": query.keywords,
        "max_jobs_per_keyword": query.jobs_per_query,
        "delay_between_queries": 2.0,
    }

    if query.location:
        search_params["location"] = query.location
    if query.workplace_types:
        search_params["workplace_types"] = query.workplace_types
    if query.employment_types:
        search_params["employment_types"] = query.employment_types
    if query.posted_date:
        search_params["posted_date"] = query.posted_date

    result = await mcp_client.bulk_search_jobs(**search_params)

    if result is None:
        return MarketSnapshot(
            query=query,
            total_jobs_found=0,
            trends=[],
            ai_insights="Failed to fetch job data from the API.",
        )

    jobs = result.get("data", [])

    if not jobs:
        return MarketSnapshot(
            query=query,
            total_jobs_found=0,
            trends=[],
            ai_insights="No jobs found matching the criteria.",
        )

    # Batch analyze with Claude
    analysis = await batch_analyze_jobs(jobs, claude_client)

    # Build trends for each keyword
    trends = []
    for keyword in query.keywords:
        # Filter jobs relevant to this keyword - check title, description, and skills
        keyword_jobs = [
            job
            for job in jobs
            if keyword.lower() in job.get("title", "").lower()
            or keyword.lower() in job.get("description", "").lower()
            or any(keyword.lower() in skill.lower() for skill in job.get("skills", []))
        ]

        if not keyword_jobs:
            continue

        # Calculate keyword-specific metrics from filtered jobs
        keyword_skills = aggregate_skills(keyword_jobs)
        keyword_workplace_dist = Counter()
        for job in keyword_jobs:
            for workplace in job.get("workplaceTypes", []):
                keyword_workplace_dist[workplace] += 1

        trend = JobTrend(
            keyword=keyword,
            total_jobs=len(keyword_jobs),
            avg_salary=_calculate_avg_salary(keyword_jobs, analysis.get("salary_data", [])),
            top_skills=keyword_skills[:10],  # Use keyword-specific skills
            workplace_distribution=dict(
                keyword_workplace_dist
            ),  # Use keyword-specific workplace distribution
            location_distribution=_get_location_distribution(keyword_jobs, top_n=10),
            seniority_distribution=analysis.get("seniority_distribution", {}),
        )
        trends.append(trend)

    # Generate AI insights
    insights_prompt = generate_market_insights(analysis)
    insights = claude_client.generate(prompt=insights_prompt, max_tokens=2048, temperature=0.7)

    # Calculate aggregate metrics across all jobs
    all_jobs_skills = aggregate_skills(jobs)
    aggregate_workplace_dist = Counter()
    for job in jobs:
        for workplace in job.get("workplaceTypes", []):
            aggregate_workplace_dist[workplace] += 1

    # Create snapshot
    snapshot = MarketSnapshot(
        timestamp=datetime.utcnow().isoformat(),
        query=query,
        total_jobs_found=len(jobs),
        trends=trends,
        ai_insights=insights,
        cache_expiry=(datetime.utcnow() + timedelta(hours=cache_ttl_hours)).isoformat(),
        aggregate_skills=all_jobs_skills[:20],
        aggregate_workplace_distribution=dict(aggregate_workplace_dist),
    )

    # Cache snapshot
    cache_snapshot(snapshot)

    return snapshot


async def batch_analyze_jobs(
    jobs: List[Dict[str, Any]], claude_client: ClaudeClient
) -> Dict[str, Any]:
    """
    Batch analyze jobs using Claude for market intelligence.

    Args:
        jobs: List of job dicts
        claude_client: Claude AI client

    Returns:
        Dict with aggregated market data
    """
    # Prepare job summaries for analysis
    job_summaries = []
    for job in jobs:
        # Safely extract location
        job_location = job.get("jobLocation") or {}
        location = job_location.get("displayName", "") if isinstance(job_location, dict) else ""

        summary = {
            "title": job.get("title", ""),
            "description": job.get("description", "")[:500],  # Limit description length
            "skills": job.get("skills", []) or [],
            "salary": job.get("salary", ""),
            "workplaceTypes": job.get("workplaceTypes", []) or [],
            "location": location,
        }
        job_summaries.append(summary)

    jobs_json = json.dumps(job_summaries, indent=2)

    # Generate batch analysis prompt
    prompt = BATCH_MARKET_ANALYSIS_PROMPT.format(job_count=len(jobs), jobs_json=jobs_json)

    # Get analysis from Claude
    analysis_text = claude_client.generate(prompt=prompt, max_tokens=4096, temperature=0.0)

    # Parse JSON response
    try:
        analysis = json.loads(analysis_text)
    except json.JSONDecodeError:
        # Fallback to basic aggregation if Claude returns invalid JSON
        analysis = _fallback_aggregation(jobs)

    return analysis


def aggregate_skills(jobs: List[Dict[str, Any]]) -> List[SkillFrequency]:
    """
    Aggregate and count skills from job postings.

    Args:
        jobs: List of job dicts

    Returns:
        List of SkillFrequency objects sorted by count
    """
    skill_counter = Counter()
    total_jobs = len(jobs)

    for job in jobs:
        # Extract skills from various fields
        skills = []

        # From explicit skills field
        if job.get("skills"):
            skills.extend(job["skills"])

        # From title and description (basic extraction)
        text = f"{job.get('title', '')} {job.get('description', '')}"
        # Common tech skills to look for
        common_skills = [
            "Python",
            "Java",
            "JavaScript",
            "TypeScript",
            "Go",
            "Rust",
            "C++",
            "React",
            "Angular",
            "Vue",
            "Node.js",
            "Django",
            "Flask",
            "AWS",
            "Azure",
            "GCP",
            "Kubernetes",
            "Docker",
            "Terraform",
            "SQL",
            "PostgreSQL",
            "MongoDB",
            "Redis",
            "CI/CD",
            "Git",
            "Jenkins",
            "GitLab",
        ]
        for skill in common_skills:
            if skill.lower() in text.lower():
                skills.append(skill)

        for skill in skills:
            skill_counter[skill.strip()] += 1

    # Convert to SkillFrequency objects
    skill_frequencies = []
    for skill, count in skill_counter.most_common():
        skill_frequencies.append(
            SkillFrequency(
                skill=skill, count=count, percentage=round((count / total_jobs) * 100, 1)
            )
        )

    return skill_frequencies


def normalize_salaries(salary_strings: List[str]) -> List[SalaryRange]:
    """
    Normalize salary strings to structured data.

    Args:
        salary_strings: List of salary strings from job postings

    Returns:
        List of SalaryRange objects
    """
    salaries = []

    for salary_str in salary_strings:
        if not salary_str:
            continue

        # Basic parsing (can be enhanced)
        salary_range = SalaryRange()

        # Extract numbers
        import re

        numbers = re.findall(r"[\d,]+", salary_str)

        if len(numbers) >= 2:
            # Range format: "$120,000 - $150,000"
            salary_range.min_salary = float(numbers[0].replace(",", ""))
            salary_range.max_salary = float(numbers[1].replace(",", ""))
        elif len(numbers) == 1:
            # Single value
            salary_range.min_salary = float(numbers[0].replace(",", ""))
            salary_range.max_salary = salary_range.min_salary

        # Detect hourly vs annual
        if "/hr" in salary_str.lower() or "hourly" in salary_str.lower():
            salary_range.period = "hourly"
            # Convert to annual (assuming 40hrs/week, 52 weeks)
            if salary_range.min_salary:
                salary_range.min_salary *= 2080
            if salary_range.max_salary:
                salary_range.max_salary *= 2080

        if salary_range.min_salary or salary_range.max_salary:
            salaries.append(salary_range)

    return salaries


def cache_snapshot(snapshot: MarketSnapshot):
    """Cache market snapshot to disk."""
    # Append to JSONL file
    with open(SNAPSHOTS_PATH, "a") as f:
        f.write(snapshot.model_dump_json() + "\n")


def load_cached_snapshot(query: MarketQuery, cache_ttl_hours: int = 24) -> Optional[MarketSnapshot]:
    """
    Load cached snapshot if available and not expired.

    Args:
        query: Market query to match
        cache_ttl_hours: Cache TTL in hours

    Returns:
        Cached snapshot or None
    """
    if not SNAPSHOTS_PATH.exists():
        return None

    now = datetime.utcnow()

    # Read snapshots in reverse (newest first)
    with open(SNAPSHOTS_PATH, "r") as f:
        lines = f.readlines()

    for line in reversed(lines):
        try:
            snapshot_dict = json.loads(line)
            snapshot = MarketSnapshot(**snapshot_dict)

            # Check if query matches
            if (
                snapshot.query.keywords == query.keywords
                and snapshot.query.workplace_types == query.workplace_types
                and snapshot.query.posted_date == query.posted_date
            ):
                # Check expiry
                if snapshot.cache_expiry:
                    expiry = datetime.fromisoformat(snapshot.cache_expiry)
                    if now < expiry:
                        return snapshot
        except:
            continue

    return None


def _calculate_avg_salary(
    jobs: List[Dict[str, Any]], salary_data: List[Dict[str, Any]]
) -> Optional[SalaryRange]:
    """Calculate average salary from jobs."""
    salaries = []
    for job in jobs:
        salary_str = job.get("salary", "")
        if salary_str:
            salaries.append(salary_str)

    if not salaries:
        return None

    normalized = normalize_salaries(salaries)
    if not normalized:
        return None

    # Calculate average
    min_salaries = [s.min_salary for s in normalized if s.min_salary]
    max_salaries = [s.max_salary for s in normalized if s.max_salary]

    if not min_salaries and not max_salaries:
        return None

    avg_salary = SalaryRange(
        min_salary=sum(min_salaries) / len(min_salaries) if min_salaries else None,
        max_salary=sum(max_salaries) / len(max_salaries) if max_salaries else None,
    )

    return avg_salary


def _extract_top_skills(skills_data: List[Dict[str, Any]], top_n: int = 10) -> List[SkillFrequency]:
    """Extract top N skills from analysis data."""
    skills = []
    for skill_dict in skills_data[:top_n]:
        skills.append(
            SkillFrequency(
                skill=skill_dict.get("skill", ""),
                count=skill_dict.get("count", 0),
                percentage=skill_dict.get("percentage", 0.0),
            )
        )
    return skills


def _get_location_distribution(jobs: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, int]:
    """Get top N locations from jobs."""
    location_counter = Counter()

    for job in jobs:
        job_location = job.get("jobLocation") or {}
        location = job_location.get("displayName", "") if isinstance(job_location, dict) else ""
        if location:
            location_counter[location] += 1

    return dict(location_counter.most_common(top_n))


def _fallback_aggregation(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback aggregation if Claude analysis fails."""
    workplace_dist = Counter()
    for job in jobs:
        for workplace in job.get("workplaceTypes", []):
            workplace_dist[workplace] += 1

    skills = aggregate_skills(jobs)

    return {
        "top_skills": [
            {"skill": s.skill, "count": s.count, "percentage": s.percentage} for s in skills[:20]
        ],
        "salary_data": [],
        "workplace_distribution": dict(workplace_dist),
        "location_distribution": {},
        "seniority_distribution": {},
        "common_requirements": [],
        "emerging_trends": [],
    }
