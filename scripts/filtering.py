"""Central content filtering & ranking for AI-skill posts.

Design goal: surface only (a) high-quality introductions/overviews of great
AI skills and (b) trending posts teaching good ways to USE AI skills, while
removing ads/spam/promotional noise.

Filters ALL scraped items at render-time (centralized, single source of truth
in config.json) so keyword/threshold updates don't require touching scrapers.

The keyword lists are loaded from config["filtering"] with sensible defaults here.
"""
import re

DEFAULT_INCLUDE_KEYWORDS_EN = [
    "skill tutorial", "skill guide", "skill overview", "skill list",
    "how to use", "how to install", "beginner guide", "getting started",
    "best skills", "top skills", "skill recommendation", "skill review",
    "workflow", "agent skill", "install skill", "setup guide",
    "prompt engineering", "prompt template", "system prompt",
    "claude skill", "claude code skill", "openai skill", "codex skill",
    "gemini skill", "cursor skill", "copilot skill",
    "mcp tool", "mcp server", "mcp integration",
    "create skill", "build skill", "write skill",
    "step by step", "walkthrough", "deep dive", "hands-on",
    "use case", "real world", "practical", "example",
    "reference", "architecture",
]

DEFAULT_INCLUDE_KEYWORDS_ZH = [
    "技能教程", "技能指南", "技能概览", "技能清单",
    "使用教程", "安装教程", "入门指南", "快速上手",
    "最佳技能", "推荐技能", "技能测评", "技能推荐",
    "工作流", "智能体技能", "安装技能",
    "提示词工程", "提示词模板", "系统提示词",
    "技能开发", "创建技能", "构建技能", "编写技能",
    "手把手", "详解", "深入分析", "实操",
    "使用场景", "真实案例", "实际应用",
    "文档", "参考", "架构",
    "claude技能", "openai技能", "codex技能",
]

DEFAULT_HARD_BLOCK_EN = [
    "limited time offer", "only today", "act now", "act fast", "hurry up",
    "buy now", "order now", "subscribe now", "free trial", "free gift",
    "discount", "50% off", "promo code", "sponsored", "advertisement",
    "sign up today", "join now", "register now", "earn money",
    "passive income", "get rich quick", "financial freedom", "side hustle",
    "crypto", "bitcoin", "investment opportunity", "weight loss",
    "check out my course", "click here", "click below", "download now",
    "winner", "congratulations", "you've been selected",
    "risk free", "money back guarantee", "mlm", "pyramid",
]

DEFAULT_HARD_BLOCK_ZH = [
    "限时", "限时优惠", "仅限今天", "仅限今日",
    "立即行动", "马上行动", "不要错过", "错过等一年",
    "立即购买", "立即下单", "抢购", "秒杀",
    "免费领取", "免费资料", "免费课程", "免费赠送",
    "折扣", "大促", "特价", "清仓",
    "优惠码", "优惠券", "团购",
    "扫码", "加微信", "加群", "私聊",
    "付费课程", "付费社群", "付费专栏",
    "赚快钱", "被动收入", "财富自由", "躺赚",
    "投资理财", "炒股", "加密货币", "区块链",
    "减肥", "瘦身", "点击领取", "下载链接",
    "中奖", "恭喜你", "已被选中",
    "传销", "割韭菜", "智商税",
]

# Soft-block patterns (regex). Presence adds a spam penalty but may be
# overridden if a strong include signal is present (graylist).
DEFAULT_SOFT_BLOCK_PATTERNS = [
    r"^(check out|visit|follow me|subscribe to) my",
    r"^(join|enter) my (group|community|telegram|discord)",
    r"^(dm me|message me|私我|私信)",
    r"^\d+%\s*(off|discount|折扣|优惠)",
    r"(click|戳) (the link|链接|below|评论区)",
    r"^(buy|get|order) (now|today|here|at)",
]


def _load_lists(config):
    f = (config or {}).get("filtering", {})
    return {
        "inc_en": f.get("include_keywords_en", DEFAULT_INCLUDE_KEYWORDS_EN),
        "inc_zh": f.get("include_keywords_zh", DEFAULT_INCLUDE_KEYWORDS_ZH),
        "block_en": f.get("hard_block_keywords_en", DEFAULT_HARD_BLOCK_EN),
        "block_zh": f.get("hard_block_keywords_zh", DEFAULT_HARD_BLOCK_ZH),
        "soft": f.get("soft_block_patterns", DEFAULT_SOFT_BLOCK_PATTERNS),
        "known_creators": set(f.get("known_creators", [])),
    }


def _item_text(item):
    """Concatenate the meaningful text fields of an item into one searchable string."""
    parts = [
        item.get("title", ""),
        item.get("text", ""),
        item.get("description", ""),
        item.get("name", ""),
        item.get("author", ""),
        item.get("page_name", ""),
    ]
    return " ".join(str(p) for p in parts if p).lower()


def _count_keywords(text_lower, keywords):
    """Return the number of distinct keywords found in the (already lowered) text."""
    return sum(1 for kw in keywords if kw.lower() in text_lower)


def _spam_analysis(text_lower, lists):
    hard_hits = _count_keywords(text_lower, lists["block_en"]) + _count_keywords(text_lower, lists["block_zh"])
    soft_hits = 0
    for pat in lists["soft"]:
        if re.search(pat, text_lower, re.IGNORECASE):
            soft_hits += 1
    return hard_hits, soft_hits


def _engagement(item):
    """Return the primary engagement metric for the item."""
    platform = item.get("platform", "")
    if platform == "github":
        return item.get("stars", 0)
    if platform == "youtube":
        return item.get("views", 0)
    # x and facebook use likes
    return item.get("likes", 0)


def _quality_floor(platform):
    floors = {
        "github": 5,
        "x": 3,
        "youtube": 100,
        "facebook": 5,
    }
    return floors.get(platform, 0)


def filter_and_rank_top(sections, top_n, config=None):
    """Filter, score, dedup, and rank each platform's items.

    Args:
        sections: dict of {platform: [item, ...]} — the raw scraped payload.
        top_n: how many to keep per platform.
        config: full config dict (looks at config["filtering"]).

    Returns:
        A new {platform: [ranked_item, ...]} dict. Items are mutated in place
        with a "score" field.
    """
    lists = _load_lists(config)
    out = {}
    for platform, items in sections.items():
        if not isinstance(items, list):
            continue
        filtered = []
        for it in items:
            if not isinstance(it, dict):
                continue
            res = score_item(it, platform, lists)
            if res is None:
                continue
            filtered.append(it)

        filtered = _dedup(filtered, platform)
        filtered.sort(key=lambda x: x["score"], reverse=True)
        for idx, it in enumerate(filtered[:top_n]):
            it["rank"] = idx + 1
        out[platform] = filtered[:top_n]
    return out


def score_item(item, platform, lists):
    """Return None if the item should be dropped, else populate "score". Also sets "score".

    Hard-block rules (drop regardless of include signal):
      * description/body too short (noise)
      * below platform engagement floor
      * >= 2 hard-block promo keywords
      * URL-only / no meaningful text
    """
    text = (" ".join(str(x) for x in [
        item.get("title", ""), item.get("text", ""), item.get("description", ""),
        item.get("name", ""),
    ] if x)).strip()
    # set platform if missing
    if not item.get("platform"):
        item["platform"] = platform

    # Quality floor: meaningful content length
    if len(text) < 30 and not item.get("description") and not item.get("text"):
        return None
    text_len = len(item.get("text") or item.get("description") or item.get("title") or "")

    # Engagement floor
    eng = _engagement(item)
    if eng < _quality_floor(platform):
        return None

    text_lower = text.lower()
    hard_hits, soft_hits = _spam_analysis(text_lower, lists)

    # Hard block: >=2 hard promos, or author not known + >=1 hard promo combined with weak include
    include_hits = (
        _count_keywords(text_lower, lists["inc_en"]) + _count_keywords(text_lower, lists["inc_zh"])
    )
    include_score = min(include_hits / 3.0, 1.0)

    known_author = item.get("author") in lists["known_creators"] or \
                   item.get("page_name") in lists["known_creators"]

    if hard_hits >= 2:
        return None
    if hard_hits == 1 and include_score < 0.6 and not known_author:
        return None

    # Scoring
    engagement_score = _engagement_norm(eng)
    desc_score = min(text_len / 200.0, 1.0)
    platform_score = {"github": 1.0, "youtube": 0.9, "x": 0.8, "facebook": 0.7}.get(platform, 0.8)

    score = (0.30 * include_score
             + 0.25 * engagement_score
             + 0.20 * desc_score
             + 0.15 * platform_score)

    # spam penalty (soft hits and graylisted single hard hit)
    penalty = soft_hits * 0.1
    if hard_hits >= 1:
        penalty += 0.2

    # known-creator allowance offset
    if known_author and include_score >= 0.5:
        penalty = max(0.0, penalty - 0.15)

    score -= min(penalty, 0.6)

    # Hard quality threshold
    if score < 0.12:
        return None

    item["score"] = round(score, 4)
    return item


def _engagement_norm(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return 0.0
    if value <= 0:
        return 0.0
    import math
    return min(math.log(value + 1) / math.log(10000), 1.0)


def _dedup(items, platform):
    """Remove near-duplicates within a platform (by normalized title / text prefix)."""
    seen = {}
    result = []
    for it in items:
        key_src = (it.get("title") or it.get("text") or it.get("name") or "").strip().lower()
        key = key_src[:80]
        if key in seen:
            # keep the higher-scoring one
            if it.get("score", 0) > seen[key].get("score", 0):
                result.remove(seen[key])
                seen[key] = it
                result.append(it)
            continue
        seen[key] = it
        result.append(it)
    return result