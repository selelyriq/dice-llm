"""Job ranking engine with transparent scoring and adjustable weights."""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from core.schemas import ResumeProfile, JobMatch, ScoringWeights
from integrations.llm import ClaudeClient
from core.prompts import JOB_RANKING_PROMPT, format_profile_summary, format_job_summary


def calculate_job_score(
    profile: ResumeProfile,
    job: Dict,
    weights: ScoringWeights,
    claude_client: ClaudeClient,
) -> JobMatch:
    """
    Calculate match score for a job against candidate profile.

    Args:
        profile: Candidate's ResumeProfile
        job: Job data from Dice API
        weights: User-configured scoring weights
        claude_client: Claude API client for AI-powered scoring

    Returns:
        JobMatch with score breakdown
    """
    # Format profile and job for Claude
    profile_summary = format_profile_summary(profile.model_dump())
    job_description = job.get("summary", "")

    # Prepare prompt
    prompt = JOB_RANKING_PROMPT.format(
        profile_summary=profile_summary,
        job_title=job.get("title", "Unknown"),
        job_company=job.get("companyName", "Unknown"),
        job_description=job_description[:2000],  # Limit description length
        job_location=job.get("jobLocation", {}).get("displayName", "Unknown"),
        job_workplace_type=", ".join(job.get("workplaceTypes", [])),
        job_posted_date=job.get("postedDate", "Unknown"),
    )

    # Get Claude's scoring
    try:
        response = claude_client.generate_json(
            prompt=prompt,
            system_prompt="You are an expert at matching candidates to jobs. Be honest and thorough.",
            max_tokens=1024,
        )

        # Parse response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        scores = json.loads(response)
    except Exception as e:
        # Fallback scoring if Claude fails
        scores = {
            "role_fit": 50,
            "skill_overlap": 50,
            "seniority_match": 50,
            "constraints_match": 50,
            "freshness": 50,
            "matched_skills": [],
            "missing_keywords": [],
            "match_explanation": f"Error calculating detailed score: {str(e)}",
        }

    # Normalize weights
    normalized_weights = weights.normalize()

    # Calculate weighted total score
    total_score = (
        scores["role_fit"] * normalized_weights["role_fit"]
        + scores["skill_overlap"] * normalized_weights["skill_overlap"]
        + scores["seniority_match"] * normalized_weights["seniority_match"]
        + scores["constraints_match"] * normalized_weights["constraints_match"]
        + scores["freshness"] * normalized_weights["freshness"]
    )

    # Create score breakdown
    score_breakdown = {
        "role_fit": scores["role_fit"],
        "skill_overlap": scores["skill_overlap"],
        "seniority_match": scores["seniority_match"],
        "constraints_match": scores["constraints_match"],
        "freshness": scores["freshness"],
        "weighted_total": round(total_score, 2),
    }

    # Create JobMatch object
    return JobMatch(
        job_id=job.get("id", "unknown"),
        title=job.get("title", "Unknown"),
        company=job.get("companyName", "Unknown"),
        location=job.get("jobLocation", {}).get("displayName", "Unknown"),
        url=job.get("detailsPageUrl", ""),
        salary=job.get("salary"),
        posted_date=job.get("postedDate", "Unknown"),
        workplace_types=job.get("workplaceTypes", []),
        total_score=round(total_score, 2),
        score_breakdown=score_breakdown,
        matched_skills=scores.get("matched_skills", []),
        missing_keywords=scores.get("missing_keywords", []),
        match_explanation=scores.get("match_explanation", ""),
    )


def rank_jobs(
    profile: ResumeProfile,
    jobs: List[Dict],
    weights: ScoringWeights,
    claude_client: ClaudeClient,
    min_score: float = 0.0,
) -> List[JobMatch]:
    """
    Rank list of jobs against profile.

    Args:
        profile: Candidate's ResumeProfile
        jobs: List of job dicts from Dice API
        weights: Scoring weights
        claude_client: Claude API client
        min_score: Minimum score threshold (0-100)

    Returns:
        List of JobMatch objects sorted by score (highest first)
    """
    matches = []

    for job in jobs:
        try:
            match = calculate_job_score(profile, job, weights, claude_client)
            if match.total_score >= min_score:
                matches.append(match)
        except Exception as e:
            print(f"Error scoring job {job.get('id', 'unknown')}: {e}")
            continue

    # Sort by total_score descending
    matches.sort(key=lambda x: x.total_score, reverse=True)

    return matches


def deduplicate_jobs(jobs: List[Dict]) -> List[Dict]:
    """
    Remove duplicate jobs by ID.

    Args:
        jobs: List of job dicts

    Returns:
        Deduplicated list
    """
    seen_ids = set()
    unique_jobs = []

    for job in jobs:
        job_id = job.get("id")
        if job_id and job_id not in seen_ids:
            seen_ids.add(job_id)
            unique_jobs.append(job)

    return unique_jobs


def generate_queries(
    profile: ResumeProfile,
    constraints: Dict,
    claude_client: ClaudeClient,
) -> List[str]:
    """
    Generate Dice search queries from profile and constraints.

    Args:
        profile: Candidate's ResumeProfile
        constraints: Search constraints dict
        claude_client: Claude API client

    Returns:
        List of 5 query strings
    """
    from .prompts import QUERY_GENERATION_PROMPT
    import random

    profile_summary = format_profile_summary(profile.model_dump())

    # Add a random seed to encourage variety in simple queries
    seed_phrases = [
        "Focus on different seniority levels.",
        "Vary between different core technologies.",
        "Try alternative job titles.",
        "Mix infrastructure and development roles.",
        "Include both specializations and general roles.",
    ]

    variety_hint = random.choice(seed_phrases)

    prompt = QUERY_GENERATION_PROMPT.format(
        profile_summary=profile_summary,
        workplace_types=", ".join(constraints.get("workplace_types", [])),
        employment_types=", ".join(constraints.get("employment_types", [])),
        location=constraints.get("location", "Not specified"),
        remote_preference=constraints.get("remote_only", False),
        min_salary=constraints.get("min_salary", "Not specified"),
    )

    # Add variety hint
    prompt += f"\n\nVariety note: {variety_hint}"

    response = claude_client.generate(
        prompt=prompt,
        system_prompt="You are a job search expert. Generate SHORT, SIMPLE, keyword-focused queries. Keep them under 6 words. Focus on job title + 1-2 technologies max.",
        max_tokens=256,
        temperature=0.8,  # Moderate temperature for some variety but more predictable
    )

    # Parse response - should be one query per line
    queries = [line.strip() for line in response.strip().split("\n") if line.strip()]

    # Remove any numbering or bullets
    queries = [q.lstrip("0123456789.-) ") for q in queries]

    # Ensure we have exactly 5 queries
    if len(queries) < 5:
        # Pad with variations of first query
        while len(queries) < 5 and queries:
            queries.append(queries[0] + " opportunities")

    return queries[:5]


def get_keyword_suggestions(
    profile: ResumeProfile,
    top_matches: List[JobMatch],
    claude_client: ClaudeClient,
) -> str:
    """
    Generate keyword suggestions based on top job matches.

    Args:
        profile: Candidate's ResumeProfile
        top_matches: Top 5-10 job matches
        claude_client: Claude API client

    Returns:
        Formatted keyword suggestions
    """
    from .prompts import RESUME_KEYWORDS_PROMPT

    profile_summary = format_profile_summary(profile.model_dump())

    # Summarize job matches
    job_summaries = []
    for match in top_matches[:10]:
        job_summaries.append(
            f"- {match.title} at {match.company} (Score: {match.total_score})\n"
            f"  Matched Skills: {', '.join(match.matched_skills[:5])}\n"
            f"  Missing: {', '.join(match.missing_keywords[:3])}"
        )

    job_matches_summary = "\n".join(job_summaries)

    prompt = RESUME_KEYWORDS_PROMPT.format(
        profile_summary=profile_summary,
        job_matches_summary=job_matches_summary,
    )

    response = claude_client.generate(
        prompt=prompt,
        system_prompt="You are a resume optimization expert. Provide actionable advice.",
        max_tokens=1024,
    )

    return response


def explain_match(
    profile: ResumeProfile,
    job_match: JobMatch,
    claude_client: ClaudeClient,
) -> str:
    """
    Generate detailed explanation for a specific job match.

    Args:
        profile: Candidate's ResumeProfile
        job_match: JobMatch to explain
        claude_client: Claude API client

    Returns:
        Detailed explanation text
    """
    from .prompts import EXPLAIN_MATCH_PROMPT

    profile_summary = format_profile_summary(profile.model_dump())

    job_details = f"""Title: {job_match.title}
Company: {job_match.company}
Location: {job_match.location}
Workplace: {", ".join(job_match.workplace_types)}
Salary: {job_match.salary or "Not specified"}
Posted: {job_match.posted_date}
"""

    score_breakdown = "\n".join(
        [f"{key}: {value}" for key, value in job_match.score_breakdown.items()]
    )

    prompt = EXPLAIN_MATCH_PROMPT.format(
        profile_summary=profile_summary,
        job_details=job_details,
        score_breakdown=score_breakdown,
    )

    response = claude_client.generate(
        prompt=prompt,
        system_prompt="You are a career mentor providing detailed job match analysis.",
        max_tokens=1536,
    )

    return response
