"""YouTube AI project video scraper.

Strategy:
  1. Use YouTube Data API v3 with YOUTUBE_API_KEY if available
  2. Try YouTube RSS feeds for known AI channels (no auth)
  3. Fall back to curated example data (clearly marked)
"""
import os
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

from utils.helpers import http_get_text, load_config

YOUTUBE_API = "https://www.googleapis.com/youtube/v3"

# Well-known AI channel IDs for RSS fallback (no API key needed)
_AI_CHANNEL_RSS = {
    "GoogleDeepMind": "UCP7jMXSY2xbc3KCAE0MHQ-A",  # Google DeepMind
    "OpenAI":         "UCXZCJLdBC09xxGZ6gcdrc6A",  # OpenAI
    "anthropic":      "UCrDwWp7EBBv4NwvScIpBDOA",  # Anthropic
}

_YT_NS = {"atom": "http://www.w3.org/2005/Atom", "media": "http://search.yahoo.com/mrss/"}


def _youtube_request(path, params):
    """Make a YouTube Data API request."""
    key = os.environ.get("YOUTUBE_API_KEY", "")
    if not key:
        return None
    from urllib.parse import urlencode
    params["key"] = key
    url = f"{YOUTUBE_API}{path}?{urlencode(params)}"
    import urllib.request
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "ai-project-tracker")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _search_videos_api(query, max_results=50):
    """Search YouTube via Data API v3, sorted by viewCount."""
    published_after = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "viewCount",
        "publishedAfter": published_after,
        "relevanceLanguage": "en",
    }
    data = _youtube_request("/search", params)
    if not data or "items" not in data:
        return []
    video_ids = [item["id"]["videoId"] for item in data["items"]
                 if item.get("id", {}).get("videoId")]
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
                   ["ai", "agent", "skill", "llm", "gpt", "model", "open source",
                    "open-source", "claude", "gemini", "deepseek"]):
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
            "source": "live",
        })
    results.sort(key=lambda v: v["views"], reverse=True)
    return results


def _try_rss_fallback(top_n):
    """Try to fetch AI videos from YouTube RSS feeds (no API key).

    RSS feeds are publicly accessible without authentication.
    Returns a list of video dicts or [] if all fail.
    """
    results = []
    seen_ids = set()
    for channel_name, channel_id in _AI_CHANNEL_RSS.items():
        if len(results) >= top_n:
            break
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        xml_text = http_get_text(url, timeout=10)
        if not xml_text or "<feed" not in xml_text:
            continue
        try:
            root = ET.fromstring(xml_text)
            for entry in root.findall("atom:entry", _YT_NS)[:5]:
                vid_id_el = entry.find("yt:videoId", {"yt": "http://www.youtube.com/xml/schemas/2015"})
                vid_id = vid_id_el.text if vid_id_el is not None else None
                if not vid_id or vid_id in seen_ids:
                    continue
                seen_ids.add(vid_id)
                title = entry.findtext("atom:title", "", _YT_NS)
                desc = entry.findtext("media:group/media:description", "", _YT_NS)[:200]
                views_text = entry.findtext("media:group/yt:statistics", "0",
                                            {"media": "http://search.yahoo.com/mrss/",
                                             "yt": "http://www.youtube.com/xml/schemas/2015"})
                try:
                    views = int(views_text)
                except (ValueError, TypeError):
                    views = 0
                pub = entry.findtext("atom:published", "", _YT_NS)
                results.append({
                    "id": vid_id,
                    "title": title,
                    "description": desc,
                    "channel": channel_name,
                    "published_at": pub,
                    "views": views,
                    "likes": 0,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "source": "live",
                })
                if len(results) >= top_n:
                    break
        except Exception:
            continue
        import time
        time.sleep(0.3)
    results.sort(key=lambda v: v["views"], reverse=True)
    return results[:top_n]


def _example_data(top_n):
    """Curated example data (shown when all live sources fail)."""
    seeds = [
        {"title": "OpenAI GPT-5 完整技术分析：推理、工具使用、多模态能力全面评测",
         "channel": "AI Explained", "views": 2850000, "likes": 142000,
         "description": "深入分析 GPT-5 的推理能力提升、原生工具调用、多模态融合..."},
        {"title": "Claude 4 Skills 生态全景：如何用 skill 扩展 Claude 的能力边界",
         "channel": "Matthew Berman", "views": 1620000, "likes": 98000,
         "description": "全面介绍 Claude Skills 框架、社区 skill 市场、企业部署最佳实践..."},
        {"title": "Llama 4 开源震撼发布：128k context + 端侧推理实战",
         "channel": "Two Minute Papers", "views": 1450000, "likes": 89000,
         "description": "Meta Llama 4 Scout/B开源模型对比、性能基准、本地部署指南..."},
        {"title": "AI Agent 工具链 2026：从 skill 到编排到生产的完整流程",
         "channel": "Andrej Karpathy", "views": 1380000, "likes": 85000,
         "description": "深入讲解现代 AI agent 的 skill 架构、MCP 协议、生产部署经验..."},
        {"title": "MCP 3.0 协议详解：统一 agent ↔ tool ↔ skill 交互标准",
         "channel": "Anthropic", "views": 1120000, "likes": 72000,
         "description": "Anthropic 官方讲解 Model Context Protocol 3.0 的设计哲学和实现细节..."},
        {"title": "openclaw + opencode skill 开发实战：从零构建生产级 AI 工具",
         "channel": "The AI Epiphany", "views": 980000, "likes": 64000,
         "description": "手把手教学如何为 Claude Code / OpenCode 编写高质量 skill..."},
        {"title": "DeepMind Gemini Nano 2：端侧多模态 AI 的突破与局限",
         "channel": "Fireship", "views": 890000, "likes": 56000,
         "description": "Google DeepMind 最新端侧模型 Gemini Nano 2 技术解读..."},
        {"title": "RAG 2.0 全栈实战：向量检索 + Agent Skill + 生产部署",
         "channel": "Data Independent", "views": 760000, "likes": 48000,
         "description": "新一代 RAG 架构详解，混合检索、skill 工具链、准确率优化..."},
        {"title": "Hermes 3：首个支持通用 Skill 执行的本地 Agent 模型",
         "channel": "NousResearch", "views": 650000, "likes": 42000,
         "description": "NousResearch 最新模型支持原生 skill 调用，完整本地运行..."},
        {"title": "vLLM 0.7 Speculative Decoding 实测：推理成本直降 40%",
         "channel": "Weights & Biases", "views": 540000, "likes": 35000,
         "description": "vLLM 新版本的推测解码优化实测，包含 skill-aware 路由..."},
        {"title": "AI Safety Eval 1.0：针对 Agent Skill 的安全评测标准",
         "channel": "Yannic Kilcher", "views": 420000, "likes": 28000,
         "description": "介绍新的 agent skill 安全评测框架和已知漏洞类型..."},
        {"title": "LangGraph 2.0 发布：原生 Skill 支持 + 可视化调试",
         "channel": "LangChain", "views": 380000, "likes": 24000,
         "description": "LangGraph 2.0 的新特性演示，skill 编排、实时监控、测试工具..."},
        {"title": "Edge AI 兴起：Skill 在手机/IoT 设备上执行的完整方案",
         "channel": "Edge Impulse", "views": 320000, "likes": 20000,
         "description": "端侧 AI skill 执行的技术方案，含案例和性能基准..."},
        {"title": "AI Coding Agent 技能大赛回顾：500+ 开发者的 Skill 作品集",
         "channel": "DevPost", "views": 280000, "likes": 18000,
         "description": "盘点近期 AI coding agent skill 大赛的最佳作品..."},
        {"title": "多模态 Skill 框架：视觉/音频/代码 Skill 自由组合编排",
         "channel": "Cohere", "views": 240000, "likes": 15000,
         "description": "Cohere 讲解多模态 skill 框架的设计和实现..."},
        {"title": "Groq On-Device LLM Runtime：本地执行 Skill 的毫秒级推理",
         "channel": "Groq", "views": 210000, "likes": 13000,
         "description": "Groq 最新端侧推理引擎的性能实测和 skill 执行演示..."},
        {"title": "HuggingFace Open LLM Leaderboard 新增 Skill 执行评分",
         "channel": "Hugging Face", "views": 180000, "likes": 12000,
         "description": "Open LLM Leaderboard 新增的 agent skill 执行能力维度解读..."},
        {"title": "Copilot Studio Skill Marketplace 企业级部署指南",
         "channel": "Microsoft Developer", "views": 160000, "likes": 10000,
         "description": "微软 Copilot Studio 新 skill marketplace 的完整使用教程..."},
        {"title": "AI Agent Observability 标准：Skill 追踪、审计、回滚实战",
         "channel": "Weights & Biases", "views": 140000, "likes": 9000,
         "description": "生产环境中 AI agent skill 的可观测性最佳实践..."},
        {"title": "DeepSeek V3 开源：高性能推理 + Skill 执行实测",
         "channel": "AI Explained", "views": 120000, "likes": 8000,
         "description": "DeepSeek 最新版本的技术评测和 skill 执行实测..."},
    ]
    return [
        {
            "rank": i + 1,
            "id": "",
            "title": s["title"],
            "description": s["description"],
            "channel": s["channel"],
            "published_at": "",
            "views": s["views"],
            "likes": s["likes"],
            "url": f"https://www.youtube.com/results?search_query={s['title'][:30].replace(' ', '+')}",
            "source": "示例",
        }
        for i, s in enumerate(seeds[:top_n])
    ]


def scrape_youtube_top(config, top_n=20):
    """Scrape top N AI project videos from YouTube.

    Priority: Data API (with key) > RSS feeds (no auth) > Example data.
    """
    # 1. Try YouTube Data API v3 with API key
    results = []
    if os.environ.get("YOUTUBE_API_KEY"):
        try:
            results = _search_videos_api("AI project OR AI agent OR AI skill", top_n)
            if results:
                return results
        except Exception as e:
            print(f"⚠️  YouTube API failed: {e}, trying RSS...")

    # 2. Try RSS feeds (no auth)
    try:
        results = _try_rss_fallback(top_n)
        if results:
            print(f"✔️  YouTube RSS: {len(results)} items")
            return results
    except Exception as e:
        print(f"⚠️  YouTube RSS failed: {e}, using example data...")

    # 3. Example data fallback
    return _example_data(top_n)


if __name__ == "__main__":
    cfg = load_config()
    for item in scrape_youtube_top(cfg):
        src = item.get("source", "")
        tag = " [示例]" if src == "示例" else ""
        print(f"#{item['rank']} {item['title'][:55]} ({item['views']:,} views){tag}")
