"""YouTube AI project video scraper.

Requires YOUTUBE_API_KEY env var for the YouTube Data API v3.
If unavailable, gracefully returns empty data.
"""
import os
import json
import urllib.request
import urllib.parse


YOUTUBE_API = "https://www.googleapis.com/youtube/v3"


def _youtube_request(path, params):
    """Make a YouTube Data API request."""
    key = os.environ.get("YOUTUBE_API_KEY", "")
    if not key:
        return None
    params["key"] = key
    url = f"{YOUTUBE_API}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "ai-project-tracker")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _search_videos(query, max_results=50):
    """Search YouTube videos for a query, sorted by view count."""
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "viewCount",
        "publishedAfter": _past_week_iso(),
        "relevanceLanguage": "en",
    }
    data = _youtube_request("/search", params)
    if not data or "items" not in data:
        return []

    # Fetch stats for returned videos in a second call
    video_ids = [item["id"]["videoId"] for item in data["items"] if item.get("id", {}).get("videoId")]
    stats_map = {}
    if video_ids:
        stats_data = _youtube_request("/videos", {
            "part": "statistics",
            "id": ",".join(video_ids[:50]),
        })
        for item in (stats_data or {}).get("items", []):
            stats_map[item["id"]] = item.get("statistics", {})

    results = []
    for item in data["items"]:
        vid = item.get("id", {}).get("videoId")
        if not vid:
            continue
        sn = item.get("snippet", {})
        stats = stats_map.get(vid, {})
        title, desc = sn.get("title", ""), (sn.get("description") or "")[:200]
        if not any(kw in (title + " " + desc).lower() for kw in
                   ["ai", "agent", "skill", "llm", "gpt", "model", "open source", "open-source"]):
            continue
        results.append({
            "id": vid,
            "title": title,
            "description": desc,
            "channel": sn.get("channelTitle", ""),
            "published_at": sn.get("publishedAt", ""),
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "url": f"https://www.youtube.com/watch?v={vid}",
        })
    results.sort(key=lambda v: v["views"], reverse=True)
    return results


def _past_week_iso():
    """Return ISO 8601 timestamp for 7 days ago (for publishedAfter filter)."""
    from datetime import datetime, timedelta
    return (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")


def scrape_youtube_top(config, top_n=20):
    """Scrape top N AI project videos from YouTube."""
    results = _search_videos("AI project OR AI agent OR AI skill", max_results=50)
    # Keep only top_n
    for idx, item in enumerate(results[:top_n]):
        item["rank"] = idx + 1
    return results[:top_n]


if __name__ == "__main__":
    from utils.helpers import load_config
    cfg = load_config()
    for item in scrape_youtube_top(cfg):
        print(f"#{item['rank']} {item['title']} ({item['views']} views)")
