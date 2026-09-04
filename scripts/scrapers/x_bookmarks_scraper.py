"""X (Twitter) bookmarks scraper — fetches user's saved/bookmarked posts.

Requires OAuth 2.0 User Context token with `bookmark.read` scope.
Environment variables:
  X_USER_ID         — numeric Twitter user ID
  X_ACCESS_TOKEN    — OAuth 2.0 User access token (with bookmark.read)

Strategy:
  1. API v2 /2/users/:id/bookmarks (requires user token)
  2. Fall back to curated example data if no token provided
"""
import os
import json
import urllib.request
import urllib.parse
import datetime

from utils.helpers import http_get_text, load_config

X_API = "https://api.twitter.com/2"


def _user_request(path, query_params=None):
    """Make a Twitter API v2 request with user-context OAuth token."""
    user_id = os.environ.get("X_USER_ID", "")
    token = os.environ.get("X_ACCESS_TOKEN", "")
    if not user_id or not token:
        return None
    params = query_params or {}
    url = f"{X_API}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "ai-project-tracker")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def scrape_x_bookmarks(config=None, max_items=50):
    """Fetch user's X bookmarks from the past 7 days.

    Args:
        config: project config dict
        max_items: max bookmarks to return

    Returns:
        list of bookmark dicts: [{rank, id, author, text, likes, created_at, url, source, platform}]
    """
    cfg = config or load_config()
    fb_cfg = cfg.get("x_bookmarks", cfg.get("facebook", {}))
    user_id = os.environ.get("X_USER_ID", "")
    token = os.environ.get("X_ACCESS_TOKEN", "")

    if not user_id or not token:
        print("  ℹ️  X bookmarks: 无 OAuth token，使用内置示例数据")
        return _example_bookmarks(max_items)

    try:
        results = _fetch_bookmarks(user_id, token, max_items)
        if results:
            return results
        print("  ℹ️  X bookmarks API 返回空，使用内置示例数据")
        return _example_bookmarks(max_items)
    except Exception as e:
        print(f"  ⚠️  X bookmarks API 失败: {e}，使用内置示例数据")
        return _example_bookmarks(max_items)


def _fetch_bookmarks(user_id, token, max_items):
    """Fetch bookmarks via API v2 /2/users/:id/bookmarks."""
    # Fields to request
    params = {
        "max_results": min(max_items, 100),
        "tweet.fields": "created_at,public_metrics,author_id,text",
        "user.fields": "name,username",
        "expansions": "author_id",
    }
    data = _user_request(f"/2/users/{user_id}/bookmarks", params)
    if not data:
        return []

    tweets = data.get("data", [])
    users_map = {}
    for u in data.get("includes", {}).get("users", []):
        users_map[u["id"]] = f"@{u.get('username', '')}"

    # Filter to last 7 days
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    results = []
    for tweet in tweets:
        created = tweet.get("created_at", "")
        if created:
            try:
                dt = datetime.datetime.fromisoformat(created.replace("Z", "+00:00"))
                if dt < cutoff:
                    continue
            except ValueError:
                pass

        metrics = tweet.get("public_metrics", {})
        author = users_map.get(tweet.get("author_id", ""), "")
        url = f"https://x.com/i/status/{tweet['id']}"
        text = (tweet.get("text") or "").replace("\n", " ")[:300]

        results.append({
            "rank": len(results) + 1,
            "id": tweet["id"],
            "text": text,
            "author": author,
            "likes": metrics.get("like_count", 0),
            "retweets": metrics.get("retweet_count", 0),
            "replies": metrics.get("reply_count", 0),
            "created_at": created,
            "url": url,
            "source": "live",
            "platform": "x_bookmarks",
        })
        if len(results) >= max_items:
            break

    return results


def _example_bookmarks(max_items=20):
    """Built-in example bookmarks — shown when no OAuth token is configured."""
    now = datetime.datetime.now(datetime.timezone.utc)
    items = [
        {
            "text": "Claude Code Skills 完全指南：从零开始构建你的第一个 AI agent skill，含 MCP 工具集成与工作流编排",
            "author": "@anthropics",
            "likes": 2340,
            "retweets": 180,
        },
        {
            "text": "刚用 OpenAI Codex CLI 写了一个自动部署 skill 的 pipeline，5分钟搞定从代码到上线",
            "author": "@OpenAI",
            "likes": 5600,
            "retweets": 420,
        },
        {
            "text": "分享我整理的 50 个最佳 Claude Skills 清单：涵盖编码、写作、数据分析、自动化",
            "author": "@LangChainAI",
            "likes": 8900,
            "retweets": 1200,
        },
        {
            "text": "MCP 3.0 发布：统一 agent ↔ tool ↔ skill 交互协议，开发者只需写一个适配器",
            "author": "@modelcontextprotocol",
            "likes": 12300,
            "retweets": 2100,
        },
        {
            "text": "用 Gemini Skill Framework 构建了一个实时多模态翻译 agent，支持视觉+语音",
            "author": "@GoogleDeepMind",
            "likes": 6700,
            "retweets": 890,
        },
        {
            "text": "vLLM v0.7 现在支持 skill-aware routing：不同 skill 自动选择最优推理后端",
            "author": "@vaborabore",
            "likes": 4100,
            "retweets": 520,
        },
        {
            "text": "OpenClaw skill 生态突破 100万次下载！社区贡献的 top skill 覆盖 30+ 平台",
            "author": "@OpenClaw",
            "likes": 9800,
            "retweets": 1500,
        },
        {
            "text": "Copilot Studio 新增 skill marketplace：企业可内部发布、版本管理、权限控制自定义 skill",
            "author": "@Microsoft",
            "likes": 3200,
            "retweets": 340,
        },
        {
            "text": "NousResearch Hermes 3：首个支持通用 skill 执行的本地 agent 模型，量化后可跑在笔记本上",
            "author": "@NousResearch",
            "likes": 7600,
            "retweets": 980,
        },
        {
            "text": "HuggingFace Open LLM Leaderboard 新增 skill 执行能力评分维度，模型排名大洗牌",
            "author": "@huggingface",
            "likes": 5400,
            "retweets": 670,
        },
        {
            "text": "AI safety eval harness 1.0 发布：针对 agent skill 的标准化安全评测框架",
            "author": "@AnthropicAI",
            "likes": 4300,
            "retweets": 560,
        },
        {
            "text": "RAG 2.0 实战：混合检索 + skill 工具链让 Agent 端到端准确率从 72% 提升到 92%",
            "author": "@LangChainAI",
            "likes": 6100,
            "retweets": 830,
        },
        {
            "text": "Edge AI 技能革命：skill 在手机/IoT 设备上直接执行，端到端延迟降至毫秒级",
            "author": "@Qualcomm",
            "likes": 2800,
            "retweets": 310,
        },
        {
            "text": "OpenAI Codex 开源终局：skill 标准完全开放，第三方生态进入 fast-follow 阶段",
            "author": "@OpenAI",
            "likes": 15200,
            "retweets": 3200,
        },
        {
            "text": "多模态 skill 框架成熟：视觉/音频/代码 skill 可自由组合编排，不再受限单一模态",
            "author": "@GoogleDeepMind",
            "likes": 4900,
            "retweets": 620,
        },
        {
            "text": "AI agent observability 标准化：Skills 现在可追踪、可审计、可回滚，生产部署不再黑箱",
            "author": "@Langfuse",
            "likes": 3600,
            "retweets": 410,
        },
        {
            "text": "awesome-agent-skills 精选列表突破 1000 条！社区维护的最全 AI skill 发现平台",
            "author": "@VoltAgent",
            "likes": 2100,
            "retweets": 280,
        },
        {
            "text": "首周 500+ 开发者参与 AI coding agent 技能竞赛，最惊艳的 skill 是一个自动 code review agent",
            "author": "@GitHub",
            "likes": 7800,
            "retweets": 1100,
        },
        {
            "text": "LangGraph 2.0：原生 skill 支持 + 可视化调试，agent 编排进入新阶段",
            "author": "@LangChainAI",
            "likes": 5200,
            "retweets": 710,
        },
        {
            "text": "Groq 推出 on-device LLM runtime：本地执行 skill 的实时推理引擎，延迟 <50ms",
            "author": "@GroqInc",
            "likes": 6400,
            "retweets": 850,
        },
    ]

    results = []
    for i, s in enumerate(items[:max_items]):
        created = (now - datetime.timedelta(hours=i * 3 + 1)).isoformat().replace("+00:00", "Z")
        results.append({
            "rank": i + 1,
            "id": f"example_{i}",
            "text": s["text"],
            "author": s["author"],
            "likes": s["likes"],
            "retweets": s["retweets"],
            "replies": s.get("replies", s["likes"] // 20),
            "created_at": created,
            "url": f"https://x.com/i/status/example_{i}",
            "source": "示例",
            "platform": "x_bookmarks",
        })
    return results
