"""Resume and LinkedIn profile parsing with auto-load functionality."""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone

from PyPDF2 import PdfReader

from core.schemas import ResumeProfile, LinkedInProfile
from integrations.llm import ClaudeClient
from core.prompts import (
    RESUME_NORMALIZATION_PROMPT,
    LINKEDIN_NORMALIZATION_PROMPT,
)


# Local storage directory
JOB_SCOUT_DIR = Path.home() / ".job-scout"
PROFILE_PATH = JOB_SCOUT_DIR / "profile.json"
LINKEDIN_PATH = JOB_SCOUT_DIR / "linkedin.json"


def ensure_job_scout_dir():
    """Ensure .job-scout directory exists."""
    JOB_SCOUT_DIR.mkdir(exist_ok=True)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text content

    Raises:
        Exception: If PDF cannot be read
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def parse_resume_with_claude(resume_text: str, claude_client: ClaudeClient) -> Dict:
    """
    Parse resume text using Claude.

    Args:
        resume_text: Raw text extracted from resume
        claude_client: Claude API client

    Returns:
        Dictionary with normalized resume data
    """
    prompt = RESUME_NORMALIZATION_PROMPT.format(resume_text=resume_text)

    response = claude_client.generate_json(
        prompt=prompt,
        system_prompt="You are a resume parsing expert. Extract structured data accurately.",
        max_tokens=2048,
    )

    # Parse JSON response
    try:
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        return json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Claude response as JSON: {str(e)}\nResponse: {response}")


def parse_linkedin_with_claude(linkedin_text: str, claude_client: ClaudeClient) -> Dict:
    """
    Parse LinkedIn profile text using Claude.

    Args:
        linkedin_text: Raw text extracted from LinkedIn PDF
        claude_client: Claude API client

    Returns:
        Dictionary with normalized LinkedIn data
    """
    prompt = LINKEDIN_NORMALIZATION_PROMPT.format(linkedin_text=linkedin_text)

    response = claude_client.generate_json(
        prompt=prompt,
        system_prompt="You are a LinkedIn profile parsing expert. Extract all relevant data.",
        max_tokens=2048,
    )

    # Parse JSON response
    try:
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        return json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Claude response as JSON: {str(e)}\nResponse: {response}")


def merge_profiles(resume_data: Optional[Dict], linkedin_data: Optional[Dict]) -> ResumeProfile:
    """
    Merge resume and LinkedIn data into unified ResumeProfile.

    Args:
        resume_data: Parsed resume data (or None)
        linkedin_data: Parsed LinkedIn data (or None)

    Returns:
        Unified ResumeProfile
    """
    # Start with resume data or empty dict
    merged = resume_data.copy() if resume_data else {}

    # Track sources
    sources = {
        "resume": resume_data is not None,
        "linkedin": linkedin_data is not None,
    }

    if linkedin_data:
        # Merge skills: prioritize LinkedIn endorsements for core_skills
        if "endorsements" in linkedin_data and linkedin_data["endorsements"]:
            # Sort skills by endorsement count
            endorsed_skills = sorted(
                linkedin_data["endorsements"].items(), key=lambda x: x[1], reverse=True
            )
            top_endorsed = [skill for skill, _ in endorsed_skills[:20]]

            # Merge with resume core_skills
            existing_core = merged.get("core_skills", [])
            merged["core_skills"] = top_endorsed + [
                s for s in existing_core if s not in top_endorsed
            ]

        # Add LinkedIn skills to secondary_skills
        li_skills = linkedin_data.get("skills", [])
        existing_secondary = merged.get("secondary_skills", [])
        existing_core = merged.get("core_skills", [])
        new_secondary = [
            s for s in li_skills if s not in existing_core and s not in existing_secondary
        ]
        merged["secondary_skills"] = existing_secondary + new_secondary

        # Merge certifications into keywords_to_emphasize
        certs = linkedin_data.get("certifications", [])
        if certs:
            existing_keywords = merged.get("keywords_to_emphasize", [])
            merged["keywords_to_emphasize"] = existing_keywords + certs

        # Use LinkedIn name if resume didn't have one
        if not merged.get("extracted_name") and linkedin_data.get("extracted_name"):
            merged["extracted_name"] = linkedin_data["extracted_name"]

    # Add sources and timestamp
    merged["sources"] = sources
    merged["last_updated"] = datetime.now(timezone.utc).isoformat()

    # Create ResumeProfile with validation
    return ResumeProfile(**merged)


def load_existing_profile() -> Optional[ResumeProfile]:
    """
    Load existing profile from .job-scout/profile.json.

    Returns:
        ResumeProfile if exists, None otherwise
    """
    if not PROFILE_PATH.exists():
        return None

    try:
        with open(PROFILE_PATH, "r") as f:
            data = json.load(f)
        return ResumeProfile(**data)
    except Exception as e:
        print(f"Warning: Could not load existing profile: {e}")
        return None


def load_existing_linkedin() -> Optional[LinkedInProfile]:
    """
    Load existing LinkedIn profile from .job-scout/linkedin.json.

    Returns:
        LinkedInProfile if exists, None otherwise
    """
    if not LINKEDIN_PATH.exists():
        return None

    try:
        with open(LINKEDIN_PATH, "r") as f:
            data = json.load(f)
        return LinkedInProfile(**data)
    except Exception as e:
        print(f"Warning: Could not load existing LinkedIn profile: {e}")
        return None


def save_profile(profile: ResumeProfile):
    """Save ResumeProfile to .job-scout/profile.json."""
    ensure_job_scout_dir()
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile.model_dump(), f, indent=2)


def save_linkedin(linkedin: LinkedInProfile):
    """Save LinkedInProfile to .job-scout/linkedin.json."""
    ensure_job_scout_dir()
    with open(LINKEDIN_PATH, "w") as f:
        json.dump(linkedin.model_dump(), f, indent=2)


def process_resume(
    resume_pdf_path: Optional[str],
    linkedin_pdf_path: Optional[str],
    claude_client: ClaudeClient,
) -> ResumeProfile:
    """
    Process resume and/or LinkedIn PDF, merge, and save.

    Args:
        resume_pdf_path: Path to resume PDF (or None)
        linkedin_pdf_path: Path to LinkedIn PDF (or None)
        claude_client: Claude API client

    Returns:
        Unified ResumeProfile

    Raises:
        ValueError: If neither PDF is provided
    """
    if not resume_pdf_path and not linkedin_pdf_path:
        raise ValueError("Must provide at least one PDF (resume or LinkedIn)")

    resume_data = None
    linkedin_data = None

    # Process resume
    if resume_pdf_path:
        resume_text = extract_text_from_pdf(resume_pdf_path)
        resume_data = parse_resume_with_claude(resume_text, claude_client)

    # Process LinkedIn
    if linkedin_pdf_path:
        linkedin_text = extract_text_from_pdf(linkedin_pdf_path)
        linkedin_data = parse_linkedin_with_claude(linkedin_text, claude_client)

        # Save LinkedIn profile separately
        linkedin_profile = LinkedInProfile(**linkedin_data)
        save_linkedin(linkedin_profile)

    # Merge and create unified profile
    profile = merge_profiles(resume_data, linkedin_data)

    # Save unified profile
    save_profile(profile)

    return profile


def get_profile_status() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get status of existing profiles.

    Returns:
        Tuple of (name, resume_date, linkedin_date)
        Dates are None if files don't exist
    """
    profile = load_existing_profile()
    linkedin = load_existing_linkedin()

    name = None
    if profile and profile.extracted_name:
        name = profile.extracted_name
    elif linkedin and linkedin.extracted_name:
        name = linkedin.extracted_name

    resume_date = None
    if profile and profile.sources.get("resume"):
        # Parse ISO timestamp to readable format
        try:
            dt = datetime.fromisoformat(profile.last_updated)
            resume_date = dt.strftime("%Y-%m-%d %H:%M")
        except:
            resume_date = profile.last_updated

    linkedin_date = None
    if linkedin:
        try:
            dt = datetime.fromisoformat(linkedin.last_updated)
            linkedin_date = dt.strftime("%Y-%m-%d %H:%M")
        except:
            linkedin_date = linkedin.last_updated

    return name, resume_date, linkedin_date
