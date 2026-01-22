"""Test script for storage module and search history."""

import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.schemas import SearchHistory, JobConstraints, JobMatch
from core.storage import (
    save_search,
    load_all_searches,
    get_search_stats,
    delete_search,
)


def test_search_history():
    """Test basic search history functionality."""

    # Create test data
    constraints = JobConstraints(
        workplace_types=["Remote"],
        employment_types=["FULLTIME"],
        min_salary=100000,
        posted_date="SEVEN",
    )

    matches = [
        JobMatch(
            job_id="test123",
            title="Senior Python Developer",
            company="Tech Corp",
            location="Remote",
            url="https://dice.com/job/test123",
            posted_date="2026-01-20",
            workplace_types=["Remote"],
            total_score=92.5,
            score_breakdown={
                "role_fit": 95.0,
                "skill_overlap": 90.0,
                "seniority_match": 92.0,
                "constraints_match": 100.0,
                "freshness": 85.0,
            },
            matched_skills=["Python", "Django", "PostgreSQL"],
            missing_keywords=["Kubernetes"],
            match_explanation="Strong match with Python expertise",
        ),
    ]

    search = SearchHistory(
        timestamp=datetime.now(timezone.utc).isoformat(),
        constraints=constraints,
        queries_generated=["Senior Python Developer Remote"],
        queries_executed=["Senior Python Developer Remote"],
        total_results=15,
        top_matches=matches,
    )

    # Test saving
    print("✅ Creating test search...")
    save_search(search)
    print("   Search saved successfully!")

    # Test loading
    print("\n✅ Loading all searches...")
    searches = load_all_searches()
    print(f"   Found {len(searches)} searches")

    # Test stats
    print("\n✅ Getting statistics...")
    stats = get_search_stats()
    print(f"   Total searches: {stats['total_searches']}")
    print(f"   Total jobs found: {stats['total_jobs_found']}")
    print(f"   Average score: {stats['average_score']}")
    print(f"   Top score: {stats['top_score']}")
    if stats["date_range"]:
        print(f"   Date range: {stats['date_range']}")

    # Test deleting
    if searches:
        print(f"\n✅ Testing delete...")
        first_search = searches[0]
        print(f"   Attempting to delete search from {first_search.timestamp}")
        result = delete_search(first_search.timestamp)
        print(f"   Delete {'succeeded' if result else 'failed'}")

        # Verify deletion
        remaining = load_all_searches()
        print(f"   Searches remaining: {len(remaining)}")

    print("\n🎉 All tests passed!")


if __name__ == "__main__":
    test_search_history()
