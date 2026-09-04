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
