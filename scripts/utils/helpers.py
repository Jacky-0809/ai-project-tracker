"""Shared utility helpers for AI project tracker."""
import json
import os
import time
from datetime import datetime, timedelta

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    HAS_REQUESTS = False


DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Fail-fast degraded mode: when the network is unreachable (e.g. blocked/offline),
# repeated requests would each hang until timeout, making the pipeline very slow.
# We track consecutive empty/failed responses and switch to degraded mode so that
# subsequent http_get() calls return immediately (empty), letting scrapers fall
# back to their example data quickly instead of stalling.
NET_DEGRADED = {"flag": False}
_NET_FAIL_STREAK = {"n": 0}
_NET_FAIL_THRESHOLD = 3


def http_get(url, timeout=20, ua=DEFAULT_UA, headers=None):
    """Fetch a URL's text/bytes. Returns (status, content_bytes) or (None, b'') on failure.

    Zero-dependency: uses requests if available, else urllib.
    """
    if NET_DEGRADED["flag"]:
        return _record_failure(), b""
    merged = {"User-Agent": ua, "Accept": "*/*"}
    if headers:
        merged.update(headers)
    try:
        if HAS_REQUESTS:
            resp = requests.get(url, headers=merged, timeout=timeout, allow_redirects=True)
            if resp.content:
                _record_success()
            else:
                _record_failure()
            return resp.status_code, resp.content
        else:
            req = urllib.request.Request(url, headers=merged)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                if data:
                    _record_success()
                else:
                    _record_failure()
                return r.status, data
    except Exception:
        return _record_failure(), b""


def _record_success():
    _NET_FAIL_STREAK["n"] = 0


def reset_net_state():
    """Reset the degraded/fail-streak state (call at the start of a fresh scrape)."""
    _NET_FAIL_STREAK["n"] = 0
    NET_DEGRADED["flag"] = False


def _record_failure():
    _NET_FAIL_STREAK["n"] += 1
    if _NET_FAIL_STREAK["n"] >= _NET_FAIL_THRESHOLD:
        NET_DEGRADED["flag"] = True
    return None


def http_get_text(url, timeout=20, ua=DEFAULT_UA, headers=None, encoding="utf-8"):
    """Fetch a URL and decode as text. Returns '' on failure."""
    status, content = http_get(url, timeout=timeout, ua=ua, headers=headers)
    if not content:
        return ""
    try:
        return content.decode(encoding, errors="replace")
    except Exception:
        return content.decode("utf-8", errors="replace")


def load_config(config_path="config.json"):
    """Load config.json with defaults."""
    default_config = {
        "top_n": 20,
        "languages": ["Python", "TypeScript", "JavaScript"],
        "keywords": ["ai", "agent", "skill", "llm", "gpt", "ai-agent", "ai-skill"],
        "output_site": "site",
        "timezone": "Asia/Shanghai",
        "github": {"min_stars": 50},
        "facebook": {
            "pages": [
                "DeepMind",
                "OpenAI",
                "AnthropicAI",
                "AIatMicrosoft",
                "GoogleAI",
                "MetaAILabs",
            ],
            "show_example_flag": True,
        },
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
