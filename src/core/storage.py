"""Storage utilities for managing search history and data retention."""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import shutil

from core.schemas import SearchHistory, StorageSettings
from core.resume import JOB_SCOUT_DIR


# Storage paths
SEARCHES_DIR = JOB_SCOUT_DIR / "searches"
MARKET_DIR = JOB_SCOUT_DIR / "market"
PROFILE_DIR = JOB_SCOUT_DIR / "profile"
SETTINGS_DIR = JOB_SCOUT_DIR / "settings"


def get_searches_directory() -> Path:
    """Get or create the searches directory."""
    SEARCHES_DIR.mkdir(parents=True, exist_ok=True)
    return SEARCHES_DIR


def get_month_file(timestamp: Optional[datetime] = None) -> Path:
    """Get the JSONL file for a specific month (YYYY-MM.jsonl)."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    month_str = timestamp.strftime("%Y-%m")
    return get_searches_directory() / f"{month_str}.jsonl"


def save_search(search_history: SearchHistory, timestamp: Optional[datetime] = None) -> None:
    """Save a search to the appropriate month file."""
    month_file = get_month_file(timestamp)

    with open(month_file, "a") as f:
        f.write(search_history.model_dump_json() + "\n")


def load_all_searches() -> List[SearchHistory]:
    """Load all searches from all month files."""
    searches = []
    searches_dir = get_searches_directory()

    # Find all month files
    month_files = sorted(searches_dir.glob("*.jsonl"), reverse=True)

    for month_file in month_files:
        with open(month_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        search = SearchHistory.model_validate_json(line)
                        searches.append(search)
                    except Exception as e:
                        print(f"Error parsing search history: {e}")
                        continue

    return searches


def load_searches_in_range(
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> List[SearchHistory]:
    """Load searches within a date range."""
    all_searches = load_all_searches()

    if not start_date and not end_date:
        return all_searches

    filtered = []
    for search in all_searches:
        try:
            search_date = datetime.fromisoformat(search.timestamp.replace("Z", "+00:00"))

            # Ensure timezone-aware
            if search_date.tzinfo is None:
                search_date = search_date.replace(tzinfo=timezone.utc)

            if start_date and search_date < start_date:
                continue
            if end_date and search_date > end_date:
                continue

            filtered.append(search)
        except Exception:
            # If we can't parse the date, skip it
            continue

    return filtered


def delete_search(timestamp: str) -> bool:
    """Delete a specific search by timestamp."""
    searches_dir = get_searches_directory()

    # Parse timestamp to find the right month file
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        month_file = get_month_file(dt)

        if not month_file.exists():
            return False

        # Read all searches from the month file
        searches = []
        with open(month_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        search = SearchHistory.model_validate_json(line)
                        if search.timestamp != timestamp:
                            searches.append(search)
                    except Exception:
                        continue

        # Rewrite the file without the deleted search
        with open(month_file, "w") as f:
            for search in searches:
                f.write(search.model_dump_json() + "\n")

        return True

    except Exception as e:
        print(f"Error deleting search: {e}")
        return False


def get_search_stats() -> Dict[str, Any]:
    """Get statistics about search history."""
    searches = load_all_searches()

    if not searches:
        return {
            "total_searches": 0,
            "total_jobs_found": 0,
            "average_score": 0.0,
            "top_score": 0.0,
            "date_range": None,
        }

    total_jobs = sum(s.total_results for s in searches)

    # Get all scores from all matches
    all_scores = [match.total_score for search in searches for match in search.top_matches]

    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
    top_score = max(all_scores) if all_scores else 0.0

    # Get date range
    timestamps = []
    for search in searches:
        try:
            # Parse timestamp and ensure it's timezone-aware
            timestamp_str = search.timestamp.replace("Z", "+00:00")
            dt = datetime.fromisoformat(timestamp_str)

            # If naive, make it UTC-aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            timestamps.append(dt)
        except Exception:
            continue

    date_range = None
    if timestamps:
        earliest = min(timestamps)
        latest = max(timestamps)
        date_range = f"{earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}"

    return {
        "total_searches": len(searches),
        "total_jobs_found": total_jobs,
        "average_score": round(avg_score, 1),
        "top_score": round(top_score, 1),
        "date_range": date_range,
    }


def calculate_storage_usage() -> Dict[str, float]:
    """Calculate storage usage by category in MB."""

    def get_dir_size(path: Path) -> float:
        """Get total size of directory in MB."""
        if not path.exists():
            return 0.0

        total = 0
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size

        return total / (1024 * 1024)  # Convert to MB

    return {
        "profiles": get_dir_size(PROFILE_DIR),
        "searches": get_dir_size(SEARCHES_DIR),
        "market": get_dir_size(MARKET_DIR),
        "settings": get_dir_size(SETTINGS_DIR),
        "total": get_dir_size(JOB_SCOUT_DIR),
    }


def load_settings() -> StorageSettings:
    """Load storage settings or return defaults."""
    settings_file = SETTINGS_DIR / "config.json"

    if not settings_file.exists():
        return StorageSettings()

    try:
        with open(settings_file, "r") as f:
            data = json.load(f)
            return StorageSettings(**data)
    except Exception:
        return StorageSettings()


def save_settings(settings: StorageSettings) -> None:
    """Save storage settings."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    settings_file = SETTINGS_DIR / "config.json"

    with open(settings_file, "w") as f:
        json.dump(settings.model_dump(), f, indent=2)


def enforce_retention_policies(settings: Optional[StorageSettings] = None) -> Dict[str, int]:
    """Enforce retention policies and return count of deleted items."""
    if settings is None:
        settings = load_settings()

    deleted = {"searches": 0, "market": 0, "profiles": 0}

    if not settings.auto_cleanup:
        return deleted

    # Delete old searches
    if settings.privacy_mode or settings.search_history_retention_days > 0:
        cutoff_days = 1 if settings.privacy_mode else settings.search_history_retention_days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=cutoff_days)

        searches_dir = get_searches_directory()
        for month_file in searches_dir.glob("*.jsonl"):
            searches = []
            with open(month_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            search = SearchHistory.model_validate_json(line)
                            search_date = datetime.fromisoformat(
                                search.timestamp.replace("Z", "+00:00")
                            )

                            # Ensure timezone-aware
                            if search_date.tzinfo is None:
                                search_date = search_date.replace(tzinfo=timezone.utc)

                            if search_date >= cutoff_date:
                                searches.append(search)
                            else:
                                deleted["searches"] += 1
                        except Exception:
                            continue

            # Rewrite file with only recent searches
            if deleted["searches"] > 0:
                with open(month_file, "w") as f:
                    for search in searches:
                        f.write(search.model_dump_json() + "\n")

    return deleted


def auto_cleanup_if_needed(threshold_mb: Optional[int] = None) -> Dict[str, int]:
    """Auto-cleanup if storage exceeds threshold."""
    settings = load_settings()
    threshold = threshold_mb or settings.cleanup_threshold_mb

    usage = calculate_storage_usage()

    if usage["total"] < threshold:
        return {"searches": 0, "market": 0, "profiles": 0}

    # We exceeded threshold, delete oldest files
    deleted = {"searches": 0, "market": 0, "profiles": 0}

    # Delete oldest search month files
    searches_dir = get_searches_directory()
    month_files = sorted(searches_dir.glob("*.jsonl"))

    for month_file in month_files:
        if usage["total"] < threshold:
            break

        file_size = month_file.stat().st_size / (1024 * 1024)
        month_file.unlink()
        deleted["searches"] += 1
        usage["total"] -= file_size

    return deleted


def export_all_data(export_path: Optional[Path] = None) -> Path:
    """Export all data as a ZIP file."""
    if export_path is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        export_path = Path.home() / "Downloads" / f"job_scout_backup_{timestamp}.zip"

    # Create ZIP archive
    shutil.make_archive(str(export_path.with_suffix("")), "zip", JOB_SCOUT_DIR)

    return export_path.with_suffix(".zip")


def clear_category_data(category: str) -> bool:
    """Clear all data for a specific category."""
    category_dirs = {
        "searches": SEARCHES_DIR,
        "market": MARKET_DIR,
        "profiles": PROFILE_DIR,
    }

    if category not in category_dirs:
        return False

    dir_path = category_dirs[category]

    if dir_path.exists():
        shutil.rmtree(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)

    return True
