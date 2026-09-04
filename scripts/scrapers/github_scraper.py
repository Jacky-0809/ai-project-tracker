"""GitHub AI project / AI skill scraper.

Fetches top trending AI projects and AI skill repositories from GitHub.
"""
import os
import time
import urllib.request
import urllib.parse
import json

from utils.helpers import days_ago


GITHUB_API = "https://api.github.com"


def _github_request(url):
    """Make a GitHub API request, returning parsed JSON."""
    req = urllib.request.Request(url)
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "ai-project-tracker")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _search_repos(keywords, per_page=20, min_stars=50, since=None):
    """Search GitHub repositories by keywords, sorted by stars."""
    since = since or days_ago(14)
    query_parts = []
    for kw in keywords:
        query_parts.append(f'({kw} in:name,description,topics)')
    query = " OR ".join(query_parts)
    query += f" stars:>{min_stars} pushed:>={since}"
    params = urllib.parse.urlencode({
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
    })
    url = f"{GITHUB_API}/search/repositories?{params}"
    data = _github_request(url)
    return data.get("items", [])


def scrape_github_top(config, top_n=20):
    """Scrape top N AI projects/skills from GitHub."""
    keywords = config.get("keywords", ["ai", "agent", "skill", "llm"])
    min_stars = config.get("github", {}).get("min_stars", 50)

    # Query 1: AI projects by stars
    try:
        items = _search_repos(["ai", "agent", "llm"], top_n, min_stars)
    except Exception:
        items = []

    # Query 2: AI skill repos (opencode/claude skills)
    skill_items = []
    try:
        skill_items = _search_repos(["ai-skill", "skill claude", "opencode skill"], top_n // 2, 10)
    except Exception:
        skill_items = []

    # Merge and dedupe by full_name
    seen = set()
    results = []
    for it in list(items) + list(skill_items):
        full_name = it.get("full_name")
        if full_name in seen:
            continue
        seen.add(full_name)
        results.append({
            "rank": len(results) + 1,
            "name": full_name,
            "full_name": full_name,
            "url": it.get("html_url", ""),
            "description": (it.get("description") or "").strip(),
            "stars": it.get("stargazers_count", 0),
            "forks": it.get("forks_count", 0),
            "language": it.get("language") or "N/A",
            "topics": it.get("topics", [])[:5],
            "updated_at": it.get("updated_at", ""),
            "owner": (it.get("owner") or {}).get("login", ""),
            "created_at": it.get("created_at", ""),
        })
        if len(results) >= top_n:
            break

    time.sleep(1)
    return results[:top_n]


if __name__ == "__main__":
    from utils.helpers import load_config
    cfg = load_config()
    for repo in scrape_github_top(cfg):
        print(f"#{repo['rank']} {repo['name']} ⭐{repo['stars']} - {repo['description'][:60]}")
