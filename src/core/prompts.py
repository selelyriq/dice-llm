"""Prompt templates for resume parsing, query generation, and ranking."""

from typing import Dict, List


# Resume normalization prompt
RESUME_NORMALIZATION_PROMPT = """You are analyzing a resume to extract structured information for job matching.

Resume text:
{resume_text}

Extract the following information in JSON format:
{{
  "extracted_name": "candidate name if present",
  "target_titles": ["list of 3-5 job titles this person would be good for"],
  "core_skills": ["top 20 technical skills, prioritized by proficiency/prominence"],
  "secondary_skills": ["additional skills beyond core"],
  "cloud_stack": ["cloud platforms mentioned: aws, azure, gcp, etc."],
  "years_experience_estimate": estimated total years of professional experience (integer),
  "recent_roles": [
    {{"title": "job title", "company": "company name", "years": "duration"}}
  ],
  "keywords_to_emphasize": ["important keywords for job search optimization"]
}}

Be specific and extract actual skills/technologies mentioned, not generic terms.
"""

# LinkedIn profile normalization prompt
LINKEDIN_NORMALIZATION_PROMPT = """You are analyzing a LinkedIn profile PDF to extract structured information.

LinkedIn profile text:
{linkedin_text}

Extract the following information in JSON format:
{{
  "extracted_name": "name from profile",
  "skills": ["all skills listed"],
  "endorsements": {{"skill_name": count, ...}},
  "experience": [
    {{"title": "role", "company": "company", "duration": "time period", "description": "summary"}}
  ],
  "projects": [
    {{"name": "project name", "description": "what they did"}}
  ],
  "certifications": ["list of certifications"]
}}

Pay special attention to skill endorsement counts as they indicate proficiency.
"""

# Query generation prompt
QUERY_GENERATION_PROMPT = """You are generating Dice.com job search queries for a candidate.

Candidate Profile:
{profile_summary}

User Constraints:
- Workplace Types: {workplace_types}
- Employment Types: {employment_types}
- Location: {location}
- Remote: {remote_preference}
- Minimum Salary: {min_salary}

Generate exactly 5 diverse Dice search queries as plain text strings (one per line).
Each query should:
1. Use natural language (Dice accepts conversational queries)
2. Include relevant keywords from the candidate's core skills
3. Prioritize skills with high LinkedIn endorsements (if available)
4. Consider the candidate's seniority level
5. Be diverse - cover different aspects of their experience

Example format:
Senior Platform Engineer with Kubernetes and Terraform experience
Cloud Infrastructure roles using AWS and Python
DevOps Engineer positions focused on CI/CD automation
Site Reliability Engineer with container orchestration expertise
Infrastructure as Code specialist with 5+ years experience

Generate 5 queries now (one per line, no numbering):
"""

# Job ranking prompt
JOB_RANKING_PROMPT = """You are scoring how well a job matches a candidate's profile.

Candidate Profile:
{profile_summary}

Job Details:
Title: {job_title}
Company: {job_company}
Description: {job_description}
Location: {job_location}
Workplace Type: {job_workplace_type}
Posted: {job_posted_date}

Scoring Criteria (return scores 0-100 for each):
1. role_fit: How well does the job title match their target titles?
2. skill_overlap: How many of their core skills are mentioned in the description?
3. seniority_match: Does the role match their experience level?
4. constraints_match: Does it meet location/remote/salary requirements?
5. freshness: How recently was it posted? (ONE day=100, THREE days=75, SEVEN days=50, older=25)

Also provide:
- matched_skills: List of candidate's skills found in job description
- missing_keywords: Important keywords in job they don't have
- match_explanation: 2-3 sentence explanation of why this is a good/bad match

Return as JSON:
{{
  "role_fit": score,
  "skill_overlap": score,
  "seniority_match": score,
  "constraints_match": score,
  "freshness": score,
  "matched_skills": ["skill1", "skill2"],
  "missing_keywords": ["keyword1", "keyword2"],
  "match_explanation": "explanation text"
}}
"""

# Resume keywords suggestion prompt
RESUME_KEYWORDS_PROMPT = """You are analyzing job matches to suggest resume keywords.

Candidate's Current Profile:
{profile_summary}

Top Job Matches:
{job_matches_summary}

Analyze the top matches and identify:
1. Keywords that appear frequently in high-scoring jobs
2. Skills/technologies mentioned that the candidate doesn't emphasize
3. Industry terms or buzzwords that would improve matching

Provide 10-15 keyword suggestions with brief explanations of why each matters.

Format as:
KEYWORD: Why this matters for the candidate
"""

# Broaden search prompt
BROADEN_SEARCH_PROMPT = """You are helping broaden a job search.

Current Constraints:
{current_constraints}

Current Target Titles:
{current_titles}

Suggest:
1. 3-5 adjacent/related job titles to add
2. Whether to increase location radius (current: {current_radius})
3. Whether to relax workplace type requirements
4. Whether to remove posted_date filter

Return as JSON:
{{
  "additional_titles": ["title1", "title2"],
  "suggested_radius": integer or null,
  "suggested_workplace_types": ["Remote", "Hybrid", "On-Site"],
  "remove_date_filter": boolean,
  "explanation": "brief explanation of changes"
}}
"""

# Explain match prompt
EXPLAIN_MATCH_PROMPT = """You are providing a detailed explanation of why a job matched.

Candidate Profile:
{profile_summary}

Job Details:
{job_details}

Score Breakdown:
{score_breakdown}

Provide a detailed, conversational explanation of:
1. Why this job is a good fit (or not)
2. Which skills align well
3. What gaps exist
4. Whether the candidate should apply
5. What to emphasize in their application

Write 3-4 paragraphs in a helpful, mentor-like tone.
"""


def format_profile_summary(profile_dict: Dict) -> str:
    """Format a ResumeProfile dict into human-readable summary."""
    summary = f"""Name: {profile_dict.get("extracted_name", "Unknown")}
Experience: {profile_dict.get("years_experience_estimate", 0)} years
Target Titles: {", ".join(profile_dict.get("target_titles", []))}
Core Skills: {", ".join(profile_dict.get("core_skills", [])[:10])}
Cloud Stack: {", ".join(profile_dict.get("cloud_stack", []))}
"""
    return summary


def format_job_summary(job_dict: Dict) -> str:
    """Format a job dict into human-readable summary."""
    summary = f"""Title: {job_dict.get("title", "Unknown")}
Company: {job_dict.get("companyName", "Unknown")}
Location: {job_dict.get("jobLocation", {}).get("displayName", "Unknown")}
Workplace: {", ".join(job_dict.get("workplaceTypes", []))}
Posted: {job_dict.get("postedDate", "Unknown")}
"""
    return summary
