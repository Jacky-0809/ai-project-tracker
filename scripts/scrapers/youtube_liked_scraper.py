"""YouTube liked videos scraper — fetches user's liked/favorited videos.

Requires OAuth 2.0 credentials with `youtube.readonly` scope.
Environment variables:
  YOUTUBE_CLIENT_ID      — OAuth 2.0 client ID
  YOUTUBE_CLIENT_SECRET  — OAuth 2.0 client secret
  YOUTUBE_REFRESH_TOKEN  — OAuth 2.0 refresh token (obtained via consent flow)

Strategy:
  1. YouTube Data API v3 videos?myRating=like (requires OAuth user token)
  2. Fall back to curated example data if no token provided
"""
import os
import json
import urllib.request
import urllib.parse
import datetime

from utils.helpers import http_get_text, load_config

YT_API = "https://www.googleapis.com/youtube/v3"


def _get_access_token():
    """Get a fresh OAuth 2.0 access token using refresh token."""
    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
    if not all([client_id, client_secret, refresh_token]):
        return None

    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST",
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as resp:
        token_data = json.loads(resp.read().decode("utf-8"))
    return token_data.get("access_token")


def _yt_request(endpoint, params):
    """Make a YouTube Data API v3 request with OAuth access token."""
    token = _get_access_token()
    if not token:
        return None
    params["access_token"] = token
    url = f"{YT_API}{endpoint}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "ai-project-tracker")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def scrape_youtube_liked(config=None, max_items=50):
    """Fetch user's liked YouTube videos from the past 7 days.

    Args:
        config: project config dict
        max_items: max videos to return

    Returns:
        list of video dicts: [{rank, id, title, description, channel, published_at,
                               views, likes, url, source, platform}]
    """
    cfg = config or load_config()
    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")

    if not client_id or not refresh_token:
        print("  ℹ️  YouTube liked: 无 OAuth credentials，使用内置示例数据")
        return _example_liked(max_items)

    try:
        results = _fetch_liked_videos(max_items)
        if results:
            return results
        print("  ℹ️  YouTube liked API 返回空，使用内置示例数据")
        return _example_liked(max_items)
    except Exception as e:
        print(f"  ⚠️  YouTube liked API 失败: {e}，使用内置示例数据")
        return _example_liked(max_items)


def _fetch_liked_videos(max_items):
    """Fetch liked videos via YouTube Data API v3."""
    # Step 1: Get list of liked video IDs
    data = _yt_request("/videos", {
        "myRating": "like",
        "part": "snippet,statistics,contentDetails",
        "maxResults": min(max_items, 50),
    })
    if not data:
        return []

    # Filter to last 7 days
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    results = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        published = snippet.get("publishedAt", "")

        if published:
            try:
                dt = datetime.datetime.fromisoformat(published.replace("Z", "+00:00"))
                if dt < cutoff:
                    continue
            except ValueError:
                pass

        video_id = item.get("id", "")
        results.append({
            "rank": len(results) + 1,
            "id": video_id,
            "title": snippet.get("title", ""),
            "description": (snippet.get("description") or "")[:200],
            "channel": snippet.get("channelTitle", ""),
            "published_at": published,
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "source": "live",
            "platform": "youtube_liked",
        })
        if len(results) >= max_items:
            break

    return results


def _example_liked(max_items=20):
    """Built-in example liked videos — shown when no OAuth token is configured."""
    now = datetime.datetime.now(datetime.timezone.utc)
    items = [
        {
            "title": "Claude Code Skills 完整教程：从零到生产环境的 Agent Skill 开发指南",
            "channel": "AI Explained",
            "views": 2850000,
            "likes": 142000,
            "description": "完整介绍如何使用 Claude Code Skills 构建生产级 AI agent，包含 MCP 工具集成、工作流编排、测试与部署的最佳实践。",
        },
        {
            "title": "我用 OpenAI Codex CLI 写了一个自动部署 Skill 的 Pipeline",
            "channel": "Matthew Berman",
            "views": 1620000,
            "likes": 98000,
            "description": "实战演示如何用 Codex CLI 从零构建一个完整的 skill 自动部署 pipeline，从代码编写到 GitHub Actions 到生产上线只用 5 分钟。",
        },
        {
            "title": "50 个最佳 Claude Skills 清单：2026 年 AI Agent 技能生态全景",
            "channel": "Two Minute Papers",
            "views": 1450000,
            "likes": 89000,
            "description": "盘点 2026 年最值得关注的 50 个 Claude Skills，涵盖编码、写作、数据分析、自动化、多模态等场景。",
        },
        {
            "title": "MCP 3.0 深度解析：统一 Agent ↔ Tool ↔ Skill 交互协议",
            "channel": "Andrej Karpathy",
            "views": 1380000,
            "likes": 85000,
            "description": "MCP 3.0 规范草案解读，详解如何统一 agent 与 tool 和 skill 之间的交互协议，开发者只需写一个适配器。",
        },
        {
            "title": "Gemini Skill Framework：构建实时多模态翻译 Agent 实战",
            "channel": "Anthropic",
            "views": 1120000,
            "likes": 72000,
            "description": "使用 Google Gemini Skill Framework 构建一个支持视觉+语音的实时多模态翻译 agent，含完整代码与部署指南。",
        },
        {
            "title": "vLLM v0.7 Skill-Aware Routing：不同 Skill 自动选择最优推理后端",
            "channel": "Weights & Biases",
            "views": 980000,
            "likes": 61000,
            "description": "vLLM v0.7 新特性详解：skill-aware routing 让系统根据 skill 类型自动选择最优推理后端，推理成本降低 40%。",
        },
        {
            "title": "OpenClaw 生态突破 100 万次下载：社区 Top Skill 盘点",
            "channel": "Fireship",
            "views": 2100000,
            "likes": 128000,
            "description": "OpenClaw skill 生态里程碑：社区贡献的 top skill 已覆盖 30+ 平台，下载量突破 100 万次。",
        },
        {
            "title": "Copilot Studio Skill Marketplace 深度评测",
            "channel": "Microsoft Developer",
            "views": 750000,
            "likes": 45000,
            "description": "微软 Copilot Studio 新增 skill marketplace 的完整评测：企业可内部发布、版本管理、权限控制自定义 skill。",
        },
        {
            "title": "Hermes 3：首个支持通用 Skill 执行的本地 Agent 模型",
            "channel": "The AI Epiphany",
            "views": 1050000,
            "likes": 67000,
            "description": "NousResearch Hermes 3 深度评测：首个支持通用 skill 执行的本地 agent 模型，量化后可在笔记本上运行。",
        },
        {
            "title": "HuggingFace Leaderboard 新增 Skill 执行评分：模型排名大洗牌",
            "channel": "Yannic Kilcher",
            "views": 890000,
            "likes": 54000,
            "description": "HuggingFace Open LLM Leaderboard 新增 skill 执行能力评分维度，模型排名发生重大变化。",
        },
        {
            "title": "AI Safety Eval Harness 1.0：Agent Skill 安全评测框架",
            "channel": "AI Safety Fundamentals",
            "views": 420000,
            "likes": 28000,
            "description": "AI safety eval harness 1.0 发布：针对 agent skill 的标准化安全评测框架，含红队测试与对抗样本。",
        },
        {
            "title": "RAG 2.0 实战：混合检索 + Skill 工具链准确率 92%",
            "channel": "Paddy G",
            "views": 680000,
            "likes": 41000,
            "description": "RAG 2.0 实战指南：混合检索 + skill 工具链让 Agent 端到端准确率从 72% 提升到 92%。",
        },
        {
            "title": "Edge AI 技能革命：Skill 在手机/IoT 上直接执行",
            "channel": "Qualcomm Developer",
            "views": 530000,
            "likes": 32000,
            "description": "Edge AI 技能革命：skill 在手机和 IoT 设备上直接执行，端到端延迟降至毫秒级。",
        },
        {
            "title": "OpenAI Codex 开源终局：Skill 标准完全开放",
            "channel": "Sam Altman",
            "views": 3200000,
            "likes": 198000,
            "description": "OpenAI Codex 正式开源，skill 标准完全开放，第三方生态进入 fast-follow 阶段。",
        },
        {
            "title": "多模态 Skill 框架实战：视觉+音频+代码 Skill 自由组合",
            "channel": "Google DeepMind",
            "views": 920000,
            "likes": 58000,
            "description": "多模态 skill 框架实战：视觉/音频/代码 skill 可自由组合编排，不再受限单一模态。",
        },
        {
            "title": "AI Agent Observability：Skills 可追踪、可审计、可回滚",
            "channel": "Langfuse",
            "views": 380000,
            "likes": 24000,
            "description": "AI agent observability 标准化：skills 现在可追踪、可审计、可回滚，生产部署不再黑箱。",
        },
        {
            "title": "awesome-agent-skills 突破 1000 条：最全 AI Skill 发现平台",
            "channel": "VoltAgent",
            "views": 290000,
            "likes": 18000,
            "description": "awesome-agent-skills 精选列表突破 1000 条，社区维护的最全 AI skill 发现与推荐平台。",
        },
        {
            "title": "AI Coding Agent 技能竞赛 Top 10 获奖作品解析",
            "channel": "GitHub",
            "views": 1800000,
            "likes": 112000,
            "description": "首周 500+ 开发者参与 AI coding agent 技能竞赛，Top 10 获奖作品深度解析。",
        },
        {
            "title": "LangGraph 2.0：原生 Skill + 可视化调试实战",
            "channel": "LangChain",
            "views": 710000,
            "likes": 43000,
            "description": "LangGraph 2.0 实战：原生 skill 支持 + 可视化调试，agent 编排进入新阶段。",
        },
        {
            "title": "Groq On-Device LLM Runtime：本地 Skill 执行延迟 <50ms",
            "channel": "Groq",
            "views": 850000,
            "likes": 52000,
            "description": "Groq 推出 on-device LLM runtime：本地执行 skill 的实时推理引擎，端到端延迟低于 50ms。",
        },
    ]

    results = []
    for i, s in enumerate(items[:max_items]):
        created = (now - datetime.timedelta(hours=i * 3 + 2)).isoformat().replace("+00:00", "Z")
        results.append({
            "rank": i + 1,
            "id": f"example_{i}",
            "title": s["title"],
            "description": s["description"],
            "channel": s["channel"],
            "published_at": created,
            "views": s["views"],
            "likes": s["likes"],
            "url": f"https://www.youtube.com/watch?v=example_{i}",
            "source": "示例",
            "platform": "youtube_liked",
        })
    return results
