"""X (Twitter) AI project discussion scraper.

Strategy:
  1. Use X API v2 with Bearer Token if available
  2. Try public Syndication Embed (no auth) for known AI accounts
  3. Fall back to curated example data (clearly marked)
"""
import os
import json
import re
import urllib.request
import urllib.parse

from utils.helpers import http_get_text, load_config

X_API = "https://api.twitter.com/2"
# Accounts to try via syndication embed when no API key is available
_AI_X_ACCOUNTS = [
    "OpenAI", "AnthropicAI", "GoogleDeepMind", "MetaAILabs",
    "KaboranovAI", "LangChainAI", "Weights_Biases",
]


def _twitter_request(path, query_params):
    """Make a Twitter API v2 request."""
    token = os.environ.get("X_BEARER_TOKEN", "")
    if not token:
        return None
    url = f"{X_API}{path}?{urllib.parse.urlencode(query_params)}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "ai-project-tracker")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _try_syndication_embed(top_n):
    """Try to fetch recent tweets from AI accounts via Twitter syndication (no auth).

    Uses the embed/timeline endpoint which is public but limited.
    Returns a list of tweet dicts or [] if all fail.
    """
    results = []
    per_account = max(1, top_n // len(_AI_X_ACCOUNTS) + 1)

    for account in _AI_X_ACCOUNTS:
        if len(results) >= top_n:
            break
        url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{account}"
        html = http_get_text(url, timeout=10,
                             headers={"Accept": "text/html"})
        if not html or len(html) < 100:
            continue
        # Parse tweets from embedded HTML
        texts = re.findall(r'tweet-text[^>]*>(.*?)</p', html, re.DOTALL)
        for text in texts[:per_account]:
            clean = re.sub(r'<[^>]+>', '', text).strip()
            if not clean or len(clean) < 20:
                continue
            results.append({
                "author": f"@{account}",
                "text": clean[:300],
                "likes": 0,
                "retweets": 0,
                "replies": 0,
                "created_at": "",
                "url": f"https://x.com/{account}",
            })
        import time
        time.sleep(0.3)  # polite delay between requests

    return results[:top_n]


def _example_data(top_n):
    """Curated example data (shown when all live sources fail).

    Clearly marked as example data in the output.
    """
    seeds = [
        {"text": "GPT-5 匹配基准发布：推理能力跨跃式提升，tool-use reliability 大幅改善。",
         "author": "@OpenAI", "likes": 12800, "retweets": 4120, "source": "示例"},
        {"text": "Claude Skills 生态系统日活开发者超 50万，新增 200+ 社区 skill。",
         "author": "@AnthropicAI", "likes": 9400, "retweets": 3000, "source": "示例"},
        {"text": "DeepMind 发布 Gemini Nano 2：端侧多模态，支持实时视觉推理。",
         "author": "@GoogleDeepMind", "likes": 7600, "retweets": 2010, "source": "示例"},
        {"text": "Llama 4 Scout 开源，128k context + 多语言，训练数据超 30T tokens。",
         "author": "@MetaAILabs", "likes": 6110, "retweets": 1500, "source": "示例"},
        {"text": "openclaw skill 生态突破 100万次下载，agent skill 标准基本定型。",
         "author": "@opencode_ai", "likes": 5400, "retweets": 1320, "source": "示例"},
        {"text": "MCP 3.0 规范草案：统一 agent ↔ tool ↔ skill 的交互协议。",
         "author": "@AnthropicAI", "likes": 4300, "retweets": 980, "source": "示例"},
        {"text": "微软 Copilot Studio 新增 AI skill marketplace，企业可内部发布 skill。",
         "author": "@microsoft", "likes": 3880, "retweets": 770, "source": "示例"},
        {"text": "NousResearch Hermes 3 发布：首个支持通用 skill 执行的本地 agent 模型。",
         "author": "@NousResearch", "likes": 3010, "retweets": 640, "source": "示例"},
        {"text": "vLLM v0.7 支持 speculative decoding + skill-aware routing，推理成本降 40%。",
         "author": "@vaboratory", "likes": 2750, "retweets": 510, "source": "示例"},
        {"text": "AI safety eval harness 1.0：针对 agent skill 的标准化安全评测框架。",
         "author": "@AIethicsboard", "likes": 2400, "retweets": 430, "source": "示例"},
        {"text": "社区 awesome-agent-skills 精选列表突破 1000 条，覆盖 30+ 平台。",
         "author": "@coolabaans", "likes": 2100, "retweets": 380, "source": "示例"},
        {"text": "Groq 推出 on-device LLM runtime：本地执行 skill 的实时推理引擎。",
         "author": "@GroqInc", "likes": 1800, "retweets": 320, "source": "示例"},
        {"text": "RAG 2.0：混合检索 + skill 工具链，Agent 端到端准确率提升至 92%。",
         "author": "@llamaindex", "likes": 1600, "retweets": 280, "source": "示例"},
        {"text": "LangGraph 2.0：原生 skill 支持 + 可视化调试，agent 编排进入新阶段。",
         "author": "@LangChainAI", "likes": 1400, "retweets": 240, "source": "示例"},
        {"text": "HuggingFace Open LLM Leaderboard 新增 skill 执行能力评分维度。",
         "author": "@huggingface", "likes": 1200, "retweets": 200, "source": "示例"},
        {"text": "AI agent observability 标准化：Skills 可追踪、可审计、可回滚。",
         "author": "@Weights_Biases", "likes": 1100, "retweets": 180, "source": "示例"},
        {"text": "多模态 skill 框架成熟：视觉/音频/代码 skill 可自由组合编排。",
         "author": "@Cohere_Labs", "likes": 950, "retweets": 150, "source": "示例"},
        {"text": "Edge AI 兴起：skill 在手机/IoT 设备上直接执行，延迟降至毫秒级。",
         "author": "@EdgeImpulse", "likes": 820, "retweets": 120, "source": "示例"},
        {"text": "AI coding agent 技能竞赛：首周 500+ 开发者提交自定义 skill。",
         "author": "@devpost", "likes": 700, "retweets": 90, "source": "示例"},
        {"text": "OpenAI Codex 开源终局：skill 标准完全开放，生态进入 fast-follow 阶段。",
         "author": "@OpenAI", "likes": 600, "retweets": 75, "source": "示例"},
    ]
    return [
        {
            "rank": i + 1,
            "id": "",
            "text": s["text"],
            "author": s["author"],
            "likes": s["likes"],
            "retweets": s["retweets"],
            "replies": max(3, s["retweets"] // 4),
            "created_at": "",
            "url": f"https://x.com/{s['author'].lstrip('@')}",
            "source": s.get("source", ""),
        }
        for i, s in enumerate(seeds[:top_n])
    ]


def scrape_x_top(config, top_n=20):
    """Scrape top N AI project discussions from X.

    Priority: API v2 (with token) > Syndication embed (no auth) > Example data.
    All live data is marked source='live', example data is source='示例'.
    """
    # 1. Try API v2 with Bearer Token
    token = os.environ.get("X_BEARER_TOKEN", "")
    if token:
        query = "(".join(["ai project", "ai skill", "ai agent", "open source ai"]) + \
                ") -is:retweet lang:en"
        params = {
            "query": query,
            "max_results": min(100, top_n * 3),
            "tweet.fields": "public_metrics,created_at,author_id",
            "expansions": "author_id",
            "user.fields": "username,name",
            "sort_order": "relevancy",
        }
        try:
            data = _twitter_request("/tweets/search/recent", params)
            if data and "data" in data:
                users = {}
                for u in data.get("includes", {}).get("users", []):
                    users[u["id"]] = f"@{u.get('username', '')}"
                results = []
                for idx, tweet in enumerate(data["data"][:top_n]):
                    metrics = tweet.get("public_metrics", {})
                    author_id = tweet.get("author_id", "")
                    results.append({
                        "rank": idx + 1,
                        "id": tweet.get("id", ""),
                        "text": tweet.get("text", "").replace("\n", " ")[:300],
                        "author": users.get(author_id, ""),
                        "likes": metrics.get("like_count", 0),
                        "retweets": metrics.get("retweet_count", 0),
                        "replies": metrics.get("reply_count", 0),
                        "created_at": tweet.get("created_at", ""),
                        "url": f"https://x.com/{users.get(author_id, '').lstrip('@')}/status/{tweet.get('id', '')}",
                        "source": "live",
                    })
                return results
        except Exception as e:
            print(f"⚠️  X API failed: {e}, trying syndication embed...")

    # 2. Try syndication embed (no auth)
    try:
        live = _try_syndication_embed(top_n)
        if live:
            for idx, item in enumerate(live):
                item["rank"] = idx + 1
                item["source"] = "live"
            return live
    except Exception as e:
        print(f"⚠️  X syndication failed: {e}, using example data...")

    # 3. Example data fallback
    return _example_data(top_n)


if __name__ == "__main__":
    cfg = load_config()
    for item in scrape_x_top(cfg):
        src = item.get("source", "")
        tag = " [示例]" if src == "示例" else ""
        print(f"#{item['rank']} {item['author']} ({item['likes']}❤️) - {item['text'][:60]}{tag}")
