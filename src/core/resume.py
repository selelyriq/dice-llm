"""Resume and LinkedIn profile parsing with auto-load functionality."""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timezone

from PyPDF2 import PdfReader

from core.schemas import ResumeProfile, LinkedInProfile, ProfileVersion
from integrations.llm import ClaudeClient
from core.prompts import (
    RESUME_NORMALIZATION_PROMPT,
    LINKEDIN_NORMALIZATION_PROMPT,
)


# Local storage directory
JOB_SCOUT_DIR = Path.home() / ".job-scout"
PROFILE_PATH = JOB_SCOUT_DIR / "profile.json"
LINKEDIN_PATH = JOB_SCOUT_DIR / "linkedin.json"
PROFILE_HISTORY_DIR = JOB_SCOUT_DIR / "profile" / "history"


def ensure_job_scout_dir():
    """Ensure .job-scout directory and subdirectories exist."""
    JOB_SCOUT_DIR.mkdir(exist_ok=True)
    PROFILE_HISTORY_DIR.mkdir(parents=True, exist_ok=True)


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
        except Exception:
            resume_date = profile.last_updated

    linkedin_date = None
    if linkedin:
        try:
            dt = datetime.fromisoformat(linkedin.last_updated)
            linkedin_date = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            linkedin_date = linkedin.last_updated

    return name, resume_date, linkedin_date


def archive_current_profile() -> Optional[ProfileVersion]:
    """
    Archive the current profile to history directory with timestamp-based filename.
    Manages rotation to keep only the most recent 10 versions.

    Returns:
        ProfileVersion if profile was archived, None if no current profile exists
    """
    current_profile = load_existing_profile()
    if not current_profile:
        return None

    ensure_job_scout_dir()

    # Create version ID from timestamp
    timestamp = datetime.now(timezone.utc)
    version_id = timestamp.strftime("%Y%m%d_%H%M%S")

    # Create ProfileVersion
    profile_version = ProfileVersion(
        version_id=version_id,
        profile=current_profile,
        archived_at=timestamp.isoformat(),
        change_summary=None,  # Could be enhanced to detect changes
    )

    # Save to history directory
    history_file = PROFILE_HISTORY_DIR / f"profile_{version_id}.json"
    with open(history_file, "w") as f:
        json.dump(profile_version.model_dump(), f, indent=2)

    # Manage rotation: keep only 10 most recent versions
    _rotate_profile_history(max_versions=10)

    return profile_version


def _rotate_profile_history(max_versions: int = 10):
    """
    Delete oldest profile versions to maintain max_versions limit.

    Args:
        max_versions: Maximum number of profile versions to keep
    """
    if not PROFILE_HISTORY_DIR.exists():
        return

    # Get all profile history files sorted by modification time (newest first)
    history_files = sorted(
        PROFILE_HISTORY_DIR.glob("profile_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    # Delete files beyond max_versions
    for old_file in history_files[max_versions:]:
        try:
            old_file.unlink()
        except Exception as e:
            print(f"Warning: Could not delete old profile version {old_file}: {e}")


def load_profile_history() -> List[ProfileVersion]:
    """
    Load all archived profile versions from history directory.

    Returns:
        List of ProfileVersion objects, sorted by archived_at (newest first)
    """
    if not PROFILE_HISTORY_DIR.exists():
        return []

    versions = []
    for history_file in PROFILE_HISTORY_DIR.glob("profile_*.json"):
        try:
            with open(history_file, "r") as f:
                data = json.load(f)
            version = ProfileVersion(**data)
            versions.append(version)
        except Exception as e:
            print(f"Warning: Could not load profile version from {history_file}: {e}")
            continue

    # Sort by archived_at timestamp (newest first)
    versions.sort(key=lambda v: v.archived_at, reverse=True)
    return versions


def compare_profiles(current: ProfileVersion, previous: ProfileVersion) -> Dict[str, any]:
    """
    Compare two profile versions and return detailed comparison.

    Args:
        current: Newer profile version
        previous: Older profile version

    Returns:
        Dictionary with comparison details
    """
    # Combine all skills from both profiles
    current_skills = set(current.profile.core_skills + current.profile.secondary_skills)
    previous_skills = set(previous.profile.core_skills + previous.profile.secondary_skills)

    # Calculate skill changes
    skills_added = sorted(list(current_skills - previous_skills))
    skills_removed = sorted(list(previous_skills - current_skills))
    skills_unchanged = sorted(list(current_skills & previous_skills))

    # Title changes
    title_changes = []
    current_titles = set(current.profile.target_titles)
    previous_titles = set(previous.profile.target_titles)

    for title in current_titles - previous_titles:
        title_changes.append({"type": "added", "title": title})
    for title in previous_titles - current_titles:
        title_changes.append({"type": "removed", "title": title})

    # Experience change
    experience_change = (
        current.profile.years_experience_estimate - previous.profile.years_experience_estimate
    )

    # Keyword density
    keyword_density_current = len(current.profile.keywords_to_emphasize)
    keyword_density_previous = len(previous.profile.keywords_to_emphasize)

    return {
        "skills_added": skills_added,
        "skills_removed": skills_removed,
        "skills_unchanged": skills_unchanged,
        "title_changes": title_changes,
        "experience_change": experience_change,
        "keyword_density_current": keyword_density_current,
        "keyword_density_previous": keyword_density_previous,
        "total_skills_current": len(current_skills),
        "total_skills_previous": len(previous_skills),
    }
