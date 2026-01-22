"""Pydantic schemas for resume profiles, LinkedIn profiles, and job data."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ResumeProfile(BaseModel):
    """Unified resume profile extracted from resume and/or LinkedIn PDF."""

    target_titles: List[str] = Field(
        default_factory=list, description="Target job titles the candidate is seeking"
    )
    core_skills: List[str] = Field(default_factory=list, description="Top 20 core technical skills")
    secondary_skills: List[str] = Field(
        default_factory=list, description="Additional skills beyond core competencies"
    )
    cloud_stack: List[str] = Field(
        default_factory=list, description="Cloud platforms (aws, azure, gcp, etc.)"
    )
    years_experience_estimate: int = Field(
        default=0, description="Estimated total years of professional experience"
    )
    recent_roles: List[Dict[str, str]] = Field(
        default_factory=list, description="Recent work history with title, company, years"
    )
    keywords_to_emphasize: List[str] = Field(
        default_factory=list, description="Important keywords for job search optimization"
    )
    extracted_name: Optional[str] = Field(
        default=None, description="Candidate name extracted from documents"
    )
    sources: Dict[str, bool] = Field(
        default_factory=dict,
        description="Which sources were used: {'resume': True, 'linkedin': False}",
    )
    last_updated: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp of last profile update",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "target_titles": ["Platform Engineer", "Cloud Engineer", "DevOps Engineer"],
                "core_skills": ["Kubernetes", "Terraform", "AWS", "Python", "CI/CD"],
                "secondary_skills": ["Docker", "Ansible", "GitLab", "Prometheus"],
                "cloud_stack": ["aws", "azure"],
                "years_experience_estimate": 5,
                "recent_roles": [
                    {"title": "Senior DevOps Engineer", "company": "TechCorp", "years": "2"},
                    {"title": "Cloud Engineer", "company": "StartupXYZ", "years": "3"},
                ],
                "keywords_to_emphasize": [
                    "infrastructure as code",
                    "containerization",
                    "observability",
                ],
                "extracted_name": "John Doe",
                "sources": {"resume": True, "linkedin": True},
                "last_updated": "2026-01-22T10:30:00",
            }
        }


class LinkedInProfile(BaseModel):
    """LinkedIn profile data extracted from LinkedIn PDF export."""

    skills: List[str] = Field(
        default_factory=list, description="All skills listed on LinkedIn profile"
    )
    endorsements: Dict[str, int] = Field(
        default_factory=dict,
        description="Skills with endorsement counts: {'Python': 45, 'AWS': 32}",
    )
    experience: List[Dict[str, str]] = Field(
        default_factory=list, description="Detailed work history from LinkedIn"
    )
    projects: List[Dict[str, str]] = Field(
        default_factory=list, description="Projects and accomplishments"
    )
    certifications: List[str] = Field(
        default_factory=list, description="Professional certifications"
    )
    extracted_name: Optional[str] = Field(default=None, description="Name from LinkedIn profile")
    last_updated: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp of last update",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "skills": ["Python", "AWS", "Kubernetes", "Terraform", "Docker"],
                "endorsements": {"Python": 45, "AWS": 32, "Kubernetes": 28},
                "experience": [
                    {
                        "title": "Senior DevOps Engineer",
                        "company": "TechCorp",
                        "duration": "2 yrs 3 mos",
                        "description": "Led infrastructure automation initiatives",
                    }
                ],
                "projects": [
                    {
                        "name": "Cloud Migration",
                        "description": "Migrated 50+ services to Kubernetes",
                    }
                ],
                "certifications": ["AWS Solutions Architect", "CKA"],
                "extracted_name": "John Doe",
                "last_updated": "2026-01-22T10:30:00",
            }
        }


class JobConstraints(BaseModel):
    """User constraints for job search."""

    workplace_types: List[str] = Field(
        default_factory=lambda: ["Remote"],
        description="Workplace preferences: Remote, On-Site, Hybrid",
    )
    employment_types: List[str] = Field(
        default_factory=lambda: ["FULLTIME"],
        description="Employment types: FULLTIME, CONTRACTS, PARTTIME, THIRD_PARTY",
    )
    min_salary: Optional[int] = Field(default=None, description="Minimum acceptable salary")
    location: Optional[str] = Field(
        default=None, description="Geographic location (e.g., 'San Francisco, CA')"
    )
    radius: Optional[int] = Field(default=None, description="Search radius from location in miles")
    posted_date: Optional[str] = Field(
        default="SEVEN", description="Job posting recency: ONE, THREE, SEVEN (days)"
    )
    willing_to_sponsor: bool = Field(default=False, description="Require visa sponsorship")
    easy_apply: bool = Field(default=False, description="Filter for easy apply jobs")


class ScoringWeights(BaseModel):
    """User-adjustable weights for job scoring."""

    role_fit: int = Field(
        default=25, ge=0, le=100, description="Weight for role/title match (0-100)"
    )
    skill_overlap: int = Field(
        default=30, ge=0, le=100, description="Weight for skill match (0-100)"
    )
    seniority_match: int = Field(
        default=15, ge=0, le=100, description="Weight for experience level match (0-100)"
    )
    constraints_match: int = Field(
        default=20, ge=0, le=100, description="Weight for constraint satisfaction (0-100)"
    )
    freshness: int = Field(
        default=10, ge=0, le=100, description="Weight for posting recency (0-100)"
    )

    def normalize(self) -> Dict[str, float]:
        """Normalize weights to sum to 1.0."""
        total = (
            self.role_fit
            + self.skill_overlap
            + self.seniority_match
            + self.constraints_match
            + self.freshness
        )
        if total == 0:
            return {
                "role_fit": 0.25,
                "skill_overlap": 0.30,
                "seniority_match": 0.15,
                "constraints_match": 0.20,
                "freshness": 0.10,
            }
        return {
            "role_fit": self.role_fit / total,
            "skill_overlap": self.skill_overlap / total,
            "seniority_match": self.seniority_match / total,
            "constraints_match": self.constraints_match / total,
            "freshness": self.freshness / total,
        }


class JobMatch(BaseModel):
    """Scored job match with breakdown."""

    job_id: str = Field(description="Unique job identifier from Dice")
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: str = Field(description="Job location")
    url: str = Field(description="Link to job posting")
    salary: Optional[str] = Field(default=None, description="Salary information if available")
    posted_date: str = Field(description="When job was posted")
    workplace_types: List[str] = Field(default_factory=list, description="Remote/Hybrid/On-Site")

    # Scoring
    total_score: float = Field(description="Total score (0-100)")
    score_breakdown: Dict[str, float] = Field(description="Breakdown of score components")

    # Analysis
    matched_skills: List[str] = Field(
        default_factory=list, description="Skills from profile found in job description"
    )
    missing_keywords: List[str] = Field(
        default_factory=list, description="Important keywords in job not in profile"
    )
    match_explanation: str = Field(description="Human-readable explanation of why this job matched")


class SearchHistory(BaseModel):
    """Record of a search session."""

    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="When search was executed",
    )
    constraints: JobConstraints = Field(description="Constraints used for this search")
    queries_generated: List[str] = Field(description="Dice queries that were generated")
    queries_executed: List[str] = Field(
        description="Queries that were actually executed (after user editing)"
    )
    total_results: int = Field(description="Total number of jobs found")
    top_matches: List[JobMatch] = Field(
        default_factory=list, description="Top 10 job matches from this search"
    )
