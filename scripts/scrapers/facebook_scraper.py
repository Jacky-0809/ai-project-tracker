"""Facebook AI project / Skill public page scraper.

Scrapes mbasic.facebook.com public pages for AI-related posts.
Falls back to built-in example data on any failure (login wall, network, etc.).
"""
import re
import json
import urllib.request
import urllib.parse

from utils.helpers import http_get_text, DEFAULT_UA


MBASIC_BASE = "https://mbasic.facebook.com"


def _fetch_page_html(page_name):
    """Fetch the mbasic Facebook public page HTML."""
    url = f"{MBASIC_BASE}/{urllib.parse.quote(page_name, safe='')}"
    html = http_get_text(url, timeout=20, headers={"Accept-Language": "en-US,en;q=0.9"})
    if not html:
        return ""
    return html


def _parse_posts_from_html(html, page_name):
    """Extract post data from mbasic Facebook page HTML using regex."""
    posts = []
    # mbasic.facebook.com wraps each story in a <div> with data-ft or similar
    # Look for story blocks — they follow patterns in the HTML
    # Each post typically has: text content, reaction counts, a permalink

    # Split on story divs — mbasic uses <div> with role="article" or story containers
    story_pattern = re.compile(
        r'<div[^>]*data-ft=\'\{[^}]*"story_type"[^}]*\}\'[^>]*>(.*?)</div>\s*</div>\s*</div>',
        re.DOTALL,
    )
    stories = story_pattern.findall(html)

    if not stories:
        # Fallback: look for any content blocks with reaction counts
        stories = re.split(r'<div[^>]*id="see_more_pager"', html)

    for story_html in stories[:30]:
        post = _extract_single_post(story_html, page_name)
        if post and post.get("text"):
            posts.append(post)
    return posts


def _extract_single_post(story_html, page_name):
    """Extract a single post's data from its HTML fragment."""
    post = {
        "page": page_name,
        "text": "",
        "likes": 0,
        "comments": 0,
        "shares": 0,
        "url": "",
    }

    # Extract post text: look for content within story body divs
    # mbasic wraps text in <div> with role="article" or in <span> tags
    text_match = re.search(
        r'<div[^>]*class="[^"]*"[^>]*>\s*(?:<[^>]+>)*([^<]{10,})',
        story_html,
    )
    if text_match:
        raw = text_match.group(1)
        # Strip any trailing HTML tags
        raw = re.sub(r'<[^>]+>', '', raw).strip()
        post["text"] = raw[:500]

    # Extract likes/reaction count — mbasic uses patterns like "1.2K" or "123"
    likes_match = re.search(
        r'(\d[\d,.]*[KkMm]?)\s*(?:people reacted|likes|reactions?)',
        story_html,
        re.IGNORECASE,
    )
    if likes_match:
        post["likes"] = _parse_count(likes_match.group(1))

    # Also try the aria-label pattern: aria-label="X reactions"
    if post["likes"] == 0:
        likes_match2 = re.search(
            r'aria-label="(\d[\d,.]*[KkMm]?)\s*(?:reaction|like)',
            story_html,
            re.IGNORECASE,
        )
        if likes_match2:
            post["likes"] = _parse_count(likes_match2.group(1))

    # Extract comment count
    comment_match = re.search(
        r'(\d[\d,.]*[KkMm]?)\s*(?:comments?|Comment)',
        story_html,
        re.IGNORECASE,
    )
    if comment_match:
        post["comments"] = _parse_count(comment_match.group(1))

    # Extract share count
    share_match = re.search(
        r'(\d[\d,.]*[KkMm]?)\s*(?:shares?|Share)',
        story_html,
        re.IGNORECASE,
    )
    if share_match:
        post["shares"] = _parse_count(share_match.group(1))

    # Extract permalink — mbasic uses /story.php?... or /permalink.php?...
    url_match = re.search(
        r'href="(/(?:story\.php|permalink\.php)[^"]*)"',
        story_html,
    )
    if url_match:
        post["url"] = f"{MBASIC_BASE}{url_match.group(1).replace('&amp;', '&')}"
    else:
        post["url"] = f"{MBASIC_BASE}/{page_name}"

    return post


def _parse_count(raw):
    """Parse a count string like '1.2K' or '1,234' into an integer."""
    raw = raw.replace(",", "").strip()
    multiplier = 1
    if raw.upper().endswith("K"):
        multiplier = 1000
        raw = raw[:-1]
    elif raw.upper().endswith("M"):
        multiplier = 1000000
        raw = raw[:-1]
    try:
        return int(float(raw) * multiplier)
    except (ValueError, TypeError):
        return 0


def _scrape_all_pages(config):
    """Scrape posts from all configured Facebook pages."""
    pages = config.get("facebook", {}).get("pages", [])
    all_posts = []
    for page_name in pages:
        try:
            html = _fetch_page_html(page_name)
            if not html:
                continue
            # Detect login wall — mbasic redirects to login when access denied
            if "login" in html.lower() and len(html) < 2000:
                continue
            posts = _parse_posts_from_html(html, page_name)
            all_posts.extend(posts)
        except Exception:
            continue
    return all_posts


def scrape_facebook_top(config, top_n=20):
    """Scrape top N AI project posts from Facebook public pages.

    Returns a sorted list of post dicts by engagement (likes + comments).
    Falls back to built-in example data on any failure.
    """
    try:
        posts = _scrape_all_pages(config)
        if not posts:
            return _fallback_data(top_n)

        # Deduplicate by text similarity (simple prefix match)
        seen_prefixes = set()
        unique = []
        for p in posts:
            prefix = p["text"][:80]
            if prefix in seen_prefixes:
                continue
            seen_prefixes.add(prefix)
            unique.append(p)

        # Sort by engagement (likes + comments + shares)
        unique.sort(key=lambda x: x.get("likes", 0) + x.get("comments", 0) + x.get("shares", 0), reverse=True)

        # Add rank and standardize output fields
        results = []
        for idx, post in enumerate(unique[:top_n]):
            results.append({
                "rank": idx + 1,
                "author": post.get("page", ""),
                "text": post.get("text", "")[:500],
                "likes": post.get("likes", 0),
                "comments": post.get("comments", 0),
                "shares": post.get("shares", 0),
                "url": post.get("url", ""),
                "platform": "facebook",
                "source": "live",
            })

        # If live scraping yielded fewer than top_n, fill the remainder with
        # clearly-marked example data so the section stays complete.
        if len(results) < top_n:
            for it in _fallback_data(top_n):
                if len(results) >= top_n:
                    break
                it["rank"] = len(results) + 1
                results.append(it)

        return results

    except Exception:
        return _fallback_data(top_n)


def _fallback_data(top_n):
    """Fallback: built-in AI project example posts from major AI orgs."""
    seeds = [
        {
            "page": "OpenAI",
            "text": "Introducing GPT-5: our most capable model yet. GPT-5 brings native multimodal reasoning, "
                    "128K context, and a new coding agent that can build entire projects from a single prompt. "
                    "Available today for ChatGPT Plus and API users.",
            "likes": 48200,
            "comments": 3150,
            "shares": 8700,
            "url": "https://mbasic.facebook.com/OpenAI",
        },
        {
            "page": "DeepMind",
            "text": "Our latest research: Gemini 2.5 Pro achieves state-of-the-art on 30+ benchmarks. "
                    "New advances in long-context reasoning, scientific discovery, and multimodal understanding. "
                    "Read the full paper on arXiv.",
            "likes": 31500,
            "comments": 2100,
            "shares": 6400,
            "url": "https://mbasic.facebook.com/DeepMind",
        },
        {
            "page": "AnthropicAI",
            "text": "Claude 4 Opus is here — our most intelligent model, now with extended thinking, "
                    "computer use, and tool use capabilities. Claude can now manage multi-step workflows, "
                    "run code, and reason through complex tasks autonomously.",
            "likes": 27800,
            "comments": 2800,
            "shares": 5900,
            "url": "https://mbasic.facebook.com/AnthropicAI",
        },
        {
            "page": "MetaAILabs",
            "text": "Llama 4 is now open-source and available for download. With 405B parameters, "
                    "vision capabilities, and 256K context window — the most powerful open model ever released. "
                    "Fine-tune it, deploy it, build with it.",
            "likes": 35100,
            "comments": 3400,
            "shares": 12200,
            "url": "https://mbasic.facebook.com/MetaAILabs",
        },
        {
            "page": "GoogleAI",
            "text": "Project Astra: your AI assistant that can see, hear, and help in real-time. "
                    "Today we're opening the API to all developers. Build multimodal AI agents "
                    "that understand the world through your camera.",
            "likes": 19600,
            "comments": 1800,
            "shares": 4300,
            "url": "https://mbasic.facebook.com/GoogleAI",
        },
        {
            "page": "AIatMicrosoft",
            "text": "Microsoft Copilot Studio: create custom AI agents for your enterprise — "
                    "no code required. Connect to your data, define workflows, and deploy "
                    "intelligent agents that handle customer support, HR, and IT tasks.",
            "likes": 15300,
            "comments": 1200,
            "shares": 3800,
            "url": "https://mbasic.facebook.com/AIatMicrosoft",
        },
        {
            "page": "OpenAI",
            "text": "DevDay 2026 Recap: Realtime API, new fine-tuning tiers, Structured Outputs GA, "
                    "and the Agents SDK. Building AI agents just got 10x easier. "
                    "Watch the full keynote replay on our YouTube channel.",
            "likes": 22400,
            "comments": 1950,
            "shares": 5100,
            "url": "https://mbasic.facebook.com/OpenAI",
        },
        {
            "page": "DeepMind",
            "text": "AlphaFold 4 predicts protein interactions with near-experimental accuracy. "
                    "We've open-sourced the model weights and the full training dataset. "
                    "Drug discovery will never be the same.",
            "likes": 26700,
            "comments": 2200,
            "shares": 7800,
            "url": "https://mbasic.facebook.com/DeepMind",
        },
        {
            "page": "MetaAILabs",
            "text": "PyTorch 3.0 is here with native distributed training, 4-bit quantization, "
                    "and the new torch.compile v2 — 3x faster training out of the box. "
                    "The future of open-source ML infrastructure.",
            "likes": 18900,
            "comments": 1600,
            "shares": 4500,
            "url": "https://mbasic.facebook.com/MetaAILabs",
        },
        {
            "page": "AnthropicAI",
            "text": "Responsible Scaling Policy update: we've audited Claude 4's capabilities against "
                    "our ASL-4 threat model. New evaluations show significant improvements in "
                    "safety without compromising capability. Full report on our website.",
            "likes": 11200,
            "comments": 980,
            "shares": 2600,
            "url": "https://mbasic.facebook.com/AnthropicAI",
        },
        {
            "page": "GoogleAI",
            "text": "Gemma 3: our most efficient open model family. From 2B to 70B parameters, "
                    "optimized for on-device, edge, and cloud deployment. Includes new "
                    "safety classifiers and instruction-tuned variants.",
            "likes": 16400,
            "comments": 1350,
            "shares": 4100,
            "url": "https://mbasic.facebook.com/GoogleAI",
        },
        {
            "page": "AIatMicrosoft",
            "text": "GitHub Copilot now supports multi-file editing, autonomous code review, "
                    "and our new Copilot Workspace for planning complex tasks. "
                    "Shipping faster with AI that understands your entire codebase.",
            "likes": 14700,
            "comments": 1100,
            "shares": 3500,
            "url": "https://mbasic.facebook.com/AIatMicrosoft",
        },
        {
            "page": "OpenAI",
            "text": "Sora is now available to all users — generate cinematic-quality videos from text. "
                    "New features include scene editing, audio generation, and 1080p output. "
                    "Create AI-powered stories like never before.",
            "likes": 38500,
            "comments": 4200,
            "shares": 9100,
            "url": "https://mbasic.facebook.com/OpenAI",
        },
        {
            "page": "DeepMind",
            "text": "Gemini Nano is now running on over 200 million Android devices. "
                    "On-device AI for smart replies, summarization, and real-time translation — "
                    "all without sending data to the cloud.",
            "likes": 13800,
            "comments": 950,
            "shares": 2800,
            "url": "https://mbasic.facebook.com/DeepMind",
        },
        {
            "page": "MetaAILabs",
            "text": "Segment Anything 2 (SAM 2) is out — real-time object segmentation in video. "
                    "Track any object across frames with zero-shot泛化能力. "
                    "Open weights, open dataset, open research.",
            "likes": 21300,
            "comments": 1700,
            "shares": 5600,
            "url": "https://mbasic.facebook.com/MetaAILabs",
        },
        {
            "page": "AnthropicAI",
            "text": "Claude Skills: composable, reusable capabilities you can share across teams. "
                    "Define a skill once — coding, research, data analysis — and plug it into "
                    "any Claude workflow. Community skill library launching next month.",
            "likes": 9800,
            "comments": 850,
            "shares": 2100,
            "url": "https://mbasic.facebook.com/AnthropicAI",
        },
        {
            "page": "GoogleAI",
            "text": "Veo 2 video generation is available in public preview. Create 4K, 60fps "
                    "video clips with physics-aware rendering and consistent character identity. "
                    "API access opens to all developers this quarter.",
            "likes": 17500,
            "comments": 1400,
            "shares": 3900,
            "url": "https://mbasic.facebook.com/GoogleAI",
        },
        {
            "page": "AIatMicrosoft",
            "text": "Azure AI Foundry: your one-stop platform for building, evaluating, and deploying "
                    "enterprise AI applications. Now supports 1,800+ models, built-in RAG, "
                    "and end-to-end monitoring.",
            "likes": 12100,
            "comments": 920,
            "shares": 2900,
            "url": "https://mbasic.facebook.com/AIatMicrosoft",
        },
        {
            "page": "OpenAI",
            "text": "Operator is now generally available — your AI agent that browses the web, "
                    "fills forms, books flights, and manages tasks autonomously. "
                    "Built-in guardrails let you review before any action is taken.",
            "likes": 29300,
            "comments": 3600,
            "shares": 7200,
            "url": "https://mbasic.facebook.com/OpenAI",
        },
        {
            "page": "MetaAILabs",
            "text": "NoVA (No Video Artifacts): our new image generation model that creates "
                    "photorealistic images with zero visual artifacts. Better than DALL-E 3 "
                    "on human preference evaluations. Weights on Hugging Face.",
            "likes": 14200,
            "comments": 1100,
            "shares": 3400,
            "url": "https://mbasic.facebook.com/MetaAILabs",
        },
    ]

    results = []
    for idx, seed in enumerate(seeds[:top_n]):
        results.append({
            "rank": idx + 1,
            "author": seed["page"],
            "text": seed["text"],
            "likes": seed["likes"],
            "comments": seed["comments"],
            "shares": seed["shares"],
            "url": seed["url"],
            "platform": "facebook",
            "source": "示例",
        })
    return results


if __name__ == "__main__":
    from utils.helpers import load_config
    cfg = load_config()
    for item in scrape_facebook_top(cfg):
        print(
            f"#{item['rank']} [{item['author']}] "
            f"({item['likes']}👍 {item['comments']}💬 {item['shares']}🔄) - "
            f"{item['text'][:60]}"
        )
