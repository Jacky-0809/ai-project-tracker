"""Shared utility helpers for AI project tracker."""
import json
import os
import tempfile
from datetime import datetime, timedelta


def load_config(config_path="config.json"):
    """Load config.json with defaults."""
    default_config = {
        "top_n": 20,
        "languages": ["Python", "TypeScript", "JavaScript"],
        "keywords": ["ai", "agent", "skill", "llm", "gpt", "ai-agent", "ai-skill"],
        "output_site": "site",
        "timezone": "Asia/Shanghai",
        "github": {"min_stars": 50},
    }
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        default_config.update(user_config)
    return default_config


def ensure_dir(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
    return path


def save_json(data, path):
    """Save data as pretty JSON."""
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def days_ago(days):
    """Return date string for N days ago (YYYY-MM-DD)."""
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def current_date():
    """Return today's date string (YYYY-MM-DD)."""
    return datetime.now().strftime("%Y-%m-%d")


def report_dir_name(date):
    """Convert a YYYY-MM-DD date string to the report directory name.

    e.g. '2026-09-04' -> 'Ai_skill_2026_09_04'
    """
    parts = date.split("-")
    if len(parts) == 3:
        return f"Ai_skill_{parts[0]}_{parts[1]}_{parts[2]}"
    return f"Ai_skill_{date.replace('-', '_')}"


def parse_report_dir(dir_name):
    """Parse a report directory name back to a YYYY-MM-DD date string.

    e.g. 'Ai_skill_2026_09_04' -> '2026-09-04'
    Returns None if the name is not a valid report directory.
    """
    if not dir_name.startswith("Ai_skill_"):
        return None
    rest = dir_name[len("Ai_skill_"):]
    parts = rest.split("_")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        return f"{parts[0]}-{parts[1]}-{parts[2]}"
    return None
