"""AI Project Tracker - main orchestration script.

Scrapes GitHub / X / YouTube for top AI projects & skills,
generates HTML + PDF daily reports, and prepares GitHub Pages output.

Usage:
    python scripts/run.py [--date YYYY-MM-DD] [--skip-scrape]
"""
import argparse
import json
import os
import sys

# Ensure imports resolve from the scripts/ directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import load_config, ensure_dir, save_json, current_date  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="AI Project Daily Tracker")
    parser.add_argument("--date", default=None, help="Report date YYYY-MM-DD (default: today)")
    parser.add_argument("--skip-scrape", action="store_true",
                        help="Skip scraping, reuse cached JSON if present")
    args = parser.parse_args()

    config = load_config()
    date = args.date or current_date()
    top_n = config.get("top_n", 20)

    data_dir = os.path.join(config.get("output_site", "site"), "Joke", date, "data")
    ensure_dir(data_dir)

    # ---- 1. Scrape (or load cache) ----
    if args.skip_scrape and os.path.exists(os.path.join(data_dir, "report.json")):
        with open(os.path.join(data_dir, "report.json"), "r", encoding="utf-8") as f:
            payload = json.load(f)
    else:
        payload = scrape_all(config, top_n)
        save_json(payload, os.path.join(data_dir, "report.json"))

    # ---- 2. Generate HTML + PDF ----
    from generators.html_generator import generate_daily_html
    from generators.pdf_generator import generate_pdf

    site_dir = config.get("output_site", "site")
    date_dir = os.path.join(site_dir, "Joke", date)
    ensure_dir(date_dir)

    html_content = generate_daily_html(date, payload, config)
    html_path = os.path.join(date_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    pdf_path = os.path.join(date_dir, "report.pdf")
    generate_pdf(pdf_path, date, payload, config)

    print(f"✅ Generated HTML  : {html_path}")
    print(f"✅ Generated PDF   : {pdf_path}")
    print(f"✅ Data saved      : {os.path.join(data_dir, 'report.json')}")

    # ---- 3. Update site index + rss ----
    generate_site_index(site_dir, config)

    return 0


def scrape_all(config, top_n):
    """Run all scrapers and combine into a single payload dict."""
    payload = {"date": current_date(), "github": [], "x": [], "youtube": []}

    try:
        from scrapers.github_scraper import scrape_github_top
        payload["github"] = scrape_github_top(config, top_n)
        print(f"✔️  GitHub: {len(payload['github'])} items")
    except Exception as e:
        print(f"⚠️  GitHub scrape failed: {e}")

    try:
        from scrapers.x_scraper import scrape_x_top
        payload["x"] = scrape_x_top(config, top_n)
        print(f"✔️  X     : {len(payload['x'])} items")
    except Exception as e:
        print(f"⚠️  X scrape failed: {e}")

    try:
        from scrapers.youtube_scraper import scrape_youtube_top
        payload["youtube"] = scrape_youtube_top(config, top_n)
        print(f"✔️  YouTube: {len(payload['youtube'])} items")
    except Exception as e:
        print(f"⚠️  YouTube scrape failed: {e}")

    return payload


def generate_site_index(site_dir, config):
    """Regenerate the site index.html listing all available date reports."""
    dates_dir = os.path.join(site_dir, "Joke")
    dates = []
    if os.path.isdir(dates_dir):
        for d in sorted(os.listdir(dates_dir)):
            if d.count("-") == 2 and os.path.isdir(os.path.join(dates_dir, d)):
                dates.append(d)
    dates.sort(reverse=True)

    from generators.html_generator import generate_index_html
    index = generate_index_html(dates, config)
    index_path = os.path.join(site_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index)
    print(f"✅ Index updated  : {index_path} (total {len(dates)} reports)")

    # Generate RSS feed
    rss = generate_rss(dates, config)
    rss_path = os.path.join(site_dir, "rss.xml")
    with open(rss_path, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"✅ RSS updated    : {rss_path}")


def generate_rss(dates, config):
    items = ""
    for d in dates:
        items += f"""
    <item>
        <title>AI 项目每日排行榜 {d}</title>
        <link>Joke/{d}/index.html</link>
        <guid>Joke/{d}/index.html</guid>
        <pubDate>{d}</pubDate>
        <description>GitHub / X / YouTube AI 项目与 Skill 每日 Top {config.get('top_n', 20)} 排行</description>
    </item>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>AI 项目每日排行榜</title>
    <link>index.html</link>
    <description>每日 AI 项目 / AI Skill 排行榜</description>
    {items}
</channel>
</rss>
"""


if __name__ == "__main__":
    sys.exit(main())
