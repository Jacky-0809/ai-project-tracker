"""HTML report generator for the daily AI project report."""
import html as html_mod

# The daily report is a fully self-contained page: we inline the stylesheet so it
# renders correctly regardless of where it is opened (GitHub Pages, file://, etc.)
REPORT_CSS = """* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif; background: #f4f6f9; color: #2d3340; line-height: 1.55; }
.container { max-width: 1180px; margin: 0 auto; padding: 0 20px; }
header { background: linear-gradient(135deg, #1e90ff, #6a5ae0); color: #fff; padding: 30px 0; margin-bottom: 24px; }
header h1 { font-size: 25px; margin-bottom: 6px; letter-spacing: .5px; }
header .date { opacity: .92; font-size: 14px; }
nav { background: #fff; padding: 10px 0; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(0,0,0,.06); position: sticky; top: 0; z-index: 10; }
nav a { color: #1e90ff; text-decoration: none; margin-right: 18px; font-weight: 500; }
nav a:hover { text-decoration: underline; }
.card { background: #fff; border-radius: 12px; padding: 20px 22px; margin-bottom: 18px; box-shadow: 0 1px 4px rgba(0,0,0,.07); border-top: 4px solid #e3e8f0; }
.card h2 { font-size: 19px; color: #1b2430; margin-bottom: 14px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.card h2 .src-hint { margin-left: auto; font-size: 12px; font-weight: 400; color: #8a94a6; }

/* ---- platform accents ---- */
.card.github  { border-top-color: #24292e; }
.card.x       { border-top-color: #1da1f2; }
.card.youtube { border-top-color: #ff0000; }
.card.facebook{ border-top-color: #1877f2; }

.platform-badge { display: inline-block; padding: 3px 11px; border-radius: 16px; font-size: 12px; font-weight: 600; color: #fff; }
.badge-github { background: #24292e; }
.badge-x { background: #1da1f2; }
.badge-youtube { background: #ff0000; }
.badge-facebook { background: #1877f2; }

/* ---- summary stat cards ---- */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }
.stat { display: flex; align-items: center; gap: 12px; background: #f8fafc; border: 1px solid #edf1f7; border-radius: 10px; padding: 14px 16px; }
.stat .ic { font-size: 26px; }
.stat b { display: block; font-size: 22px; color: #1e90ff; line-height: 1.1; }
.stat span { font-size: 12px; color: #6b7686; }
.stat.note { grid-column: 1 / -1; background: #fffbe9; border-color: #f5e9b8; }
.stat.note span { color: #8a6d1a; }

/* ---- data table (4 columns) ---- */
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13.5px; table-layout: fixed; }
.data-table th { text-align: left; padding: 10px 12px; font-size: 12px; font-weight: 600; color: #fff; letter-spacing: .3px; border: none; }
.data-table thead.github th { background: #24292e; }
.data-table thead.x th { background: #1da1f2; }
.data-table thead.youtube th { background: #ff0000; }
.data-table thead.facebook th { background: #1877f2; }
.data-table td { padding: 11px 12px; border-bottom: 1px solid #eef1f6; vertical-align: top; word-break: break-word; overflow-wrap: anywhere; }
.data-table tbody tr:nth-child(even) { background: #fafbfe; }
.data-table tbody tr:hover { background: #eef4ff; }

/* column widths (sum to 100%) */
.col-rank { width: 5%; text-align: center; font-weight: 700; color: #1e90ff; }
.col-title { width: 25%; font-weight: 600; }
.col-desc  { width: 45%; color: #4a5465; }
.col-author{ width: 12%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #5a6475; }
.col-heat  { width: 13%; white-space: nowrap; color: #444c59; font-variant-numeric: tabular-nums; }

.data-table .col-title a { color: #1a73e8; text-decoration: none; word-break: break-word; }
.data-table .col-title a:hover { text-decoration: underline; }

/* example vs live */
.row-example { opacity: .62; }
.row-example td { background-image: linear-gradient(90deg, rgba(0,0,0,0) 0, rgba(0,0,0,.05) 900px); }
.tag-example { display: inline-block; background: #f0f2f7; color: #8a94a6; border: 1px solid #e2e6ee; border-radius: 4px; font-size: 11px; padding: 1px 6px; margin-left: 6px; vertical-align: 1px; font-weight: 400; }

.heat-stars { color: #eab308; font-weight: 700; }
.heat-likes { color: #e0245e; font-weight: 700; }
.heat-views { color: #ff0000; font-weight: 700; }
.heat-heat  { color: #1e90ff; font-weight: 700; }

.empty { color: #8a94a6; font-size: 13px; padding: 12px 0; }

footer { text-align: center; padding: 26px 0; color: #9aa3b2; font-size: 13px; }
.report-links { margin-bottom: 16px; }
.btn { display: inline-block; padding: 9px 18px; background: #1e90ff; color: #fff; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 13px; }
.btn:hover { background: #0073d6; }
.btn-secondary { background: #6a5ae0; }
.btn-secondary:hover { background: #5a49cf; }

@media (max-width: 720px) {
  .col-title { width: 32%; }
  .col-desc  { width: 40%; }
  .col-author{ display: none; }
}
@media print { nav, footer, .report-links { display: none; } body { background: #fff; } .card { box-shadow: none; border: 1px solid #eee; } }
.badge-new{background:#facc15;color:#1a1a1a;font-size:.72em;padding:2px 7px;border-radius:10px;font-weight:700;margin-left:6px;vertical-align:middle}
.badge-rising{background:#34d399;color:#064e3b;font-size:.72em;padding:2px 7px;border-radius:10px;font-weight:700;margin-left:6px;vertical-align:middle}
.trending-desc{font-size:.82em;color:#64748b;margin:4px 0 12px}
.card.trending{background:linear-gradient(135deg,#fef9ee 0%,#fff 50%);border:1px solid #f59e0b20}
.card.bookmarks{background:linear-gradient(135deg,#f0f9ff 0%,#fff 50%);border:1px solid #3b82f620}
"""

def _esc(text):
    """Escape HTML special characters."""
    if text is None:
        return ""
    return html_mod.escape(str(text))


def _fmt_num(n):
    """Format a number with thousands separators."""
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return "N/A"


def _truncate(text, limit=140):
    if not text:
        return ""
    text = " ".join(str(text).split())
    return text[:limit] + ("…" if len(text) > limit else "")


def _table_header(platform):
    return f"""<table class="data-table">
    <thead class="{platform}">
        <tr>
            <th class="col-rank">#</th>
            <th class="col-title">Title</th>
            <th class="col-desc">Description</th>
            <th class="col-author">Author</th>
            <th class="col-heat">热度</th>
        </tr>
    </thead>
    <tbody>"""


def _table_footer():
    return "</tbody></table>"


def _render_github_section(items):
    if not items:
        return '<p class="empty">暂无 GitHub 数据（可检查 GITHUB_TOKEN 配额后重试）</p>'
    rows = [_table_header("github")]
    for it in items:
        heat = f"<span class='heat-stars'>★</span> {_fmt_num(it.get('stars', 0))}"
        rows.append(f"""
        <tr>
            <td class="col-rank">{it['rank']}</td>
            <td class="col-title"><a href="{_esc(it['url'])}" target="_blank">{_esc(it['name'])}</a></td>
            <td class="col-desc">{_esc(_truncate(it.get('description') or ''))}</td>
            <td class="col-author">{_esc(it.get('owner') or '')}</td>
            <td class="col-heat">{heat}</td>
        </tr>""")
    rows.append(_table_footer())
    return "\n".join(rows)


def _render_x_section(items):
    if not items:
        return '<p class="empty">暂无 X 数据（需配置 X_BEARER_TOKEN）</p>'
    rows = [_table_header("x")]
    seen_titles = set()
    for it in items:
        text = (it.get("text") or "").replace("\n", " ")
        heat = (
            f"<span class='heat-likes'>❤️</span> {_fmt_num(it.get('likes', 0))}"
            f"&nbsp;🔁 {_fmt_num(it.get('retweets', 0))}"
        )
        title = it.get("author") or ""
        desc = _truncate(text, 200)
        src = it.get("source", "")
        row_cls = ' class="row-example"' if src == "示例" else ""
        tag = '<span class="tag-example">示例</span>' if src == "示例" else ""
        rows.append(f"""
        <tr{row_cls}>
            <td class="col-rank">{it['rank']}</td>
            <td class="col-title"><a href="{_esc(it.get('url',''))}" target="_blank">{_esc(title)}</a>{tag}</td>
            <td class="col-desc">{_esc(desc)}</td>
            <td class="col-author">{_esc(title)}</td>
            <td class="col-heat">{heat}</td>
        </tr>""")
    rows.append(_table_footer())
    return "\n".join(rows)


def _render_youtube_section(items):
    if not items:
        return '<p class="empty">暂无 YouTube 数据（需配置 YOUTUBE_API_KEY）</p>'
    rows = [_table_header("youtube")]
    for it in items:
        views = it.get("views", 0)
        views_str = _fmt_num(views) if views else "N/A"
        desc = it.get("description") or it.get("channel") or ""
        src = it.get("source", "")
        row_cls = ' class="row-example"' if src == "示例" else ""
        tag = '<span class="tag-example">示例</span>' if src == "示例" else ""
        rows.append(f"""
        <tr{row_cls}>
            <td class="col-rank">{it['rank']}</td>
            <td class="col-title"><a href="{_esc(it.get('url',''))}" target="_blank">{_esc(it.get('title') or '')}</a>{tag}</td>
            <td class="col-desc">{_esc(_truncate(desc))}</td>
            <td class="col-author">{_esc(it.get('channel') or '')}</td>
            <td class="col-heat"><span class='heat-views'>▶️</span> {views_str}</td>
        </tr>""")
    rows.append(_table_footer())
    return "\n".join(rows)


def _render_facebook_section(items):
    if not items:
        return '<p class="empty">暂无 Facebook 数据（公开页面抓取受限）</p>'
    rows = [_table_header("facebook")]
    for it in items:
        author = it.get("page_name") or it.get("author", "")
        src = it.get("source", "")
        row_cls = ' class="row-example"' if src == "示例" else ""
        tag = '<span class="tag-example">示例</span>' if src == "示例" else ""
        heat = f"<span class='heat-likes'>👍</span> {_fmt_num(it.get('likes', 0))}"
        rows.append(f"""
        <tr{row_cls}>
            <td class="col-rank">{it['rank']}</td>
            <td class="col-title"><a href="{_esc(it.get('url',''))}" target="_blank">{_esc(author)}</a>{tag}</td>
            <td class="col-desc">{_esc(_truncate(it.get('text') or ''))}</td>
            <td class="col-author">{_esc(author)}</td>
            <td class="col-heat">{heat}</td>
        </tr>""")
    rows.append(_table_footer())
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# "本周收藏" sections — X bookmarks & YouTube liked videos
# ---------------------------------------------------------------------------

def _render_x_bookmarks_section(items):
    """Render user's X bookmarks/favorites this week."""
    if not items:
        return '<p class="empty">暂无 X 收藏数据（需配置 X_ACCESS_TOKEN + X_USER_ID）</p>'
    rows = [_table_header("x_bookmarks")]
    for it in items:
        text = (it.get("text") or "").replace("\n", " ")
        heat = (
            f"<span class='heat-likes'>❤️</span> {_fmt_num(it.get('likes', 0))}"
            f"&nbsp;🔁 {_fmt_num(it.get('retweets', 0))}"
        )
        title = it.get("author") or ""
        desc = _truncate(text, 200)
        src = it.get("source", "")
        row_cls = ' class="row-example"' if src == "示例" else ""
        tag = '<span class="tag-example">示例</span>' if src == "示例" else ""
        rows.append(f"""
        <tr{row_cls}>
            <td class="col-rank">{it['rank']}</td>
            <td class="col-title"><a href="{_esc(it.get('url',''))}" target="_blank">{_esc(title)}</a>{tag}</td>
            <td class="col-desc">{_esc(desc)}</td>
            <td class="col-author">{_esc(title)}</td>
            <td class="col-heat">{heat}</td>
        </tr>""")
    rows.append(_table_footer())
    return "\n".join(rows)


def _render_youtube_liked_section(items):
    """Render user's YouTube liked videos this week."""
    if not items:
        return '<p class="empty">暂无 YouTube 收藏数据（需配置 YOUTUBE_CLIENT_ID + YOUTUBE_CLIENT_SECRET + YOUTUBE_REFRESH_TOKEN）</p>'
    rows = [_table_header("youtube_liked")]
    for it in items:
        views = it.get("views", 0)
        views_str = _fmt_num(views) if views else "N/A"
        desc = it.get("description") or it.get("channel") or ""
        src = it.get("source", "")
        row_cls = ' class="row-example"' if src == "示例" else ""
        tag = '<span class="tag-example">示例</span>' if src == "示例" else ""
        rows.append(f"""
        <tr{row_cls}>
            <td class="col-rank">{it['rank']}</td>
            <td class="col-title"><a href="{_esc(it.get('url',''))}" target="_blank">{_esc(it.get('title') or '')}</a>{tag}</td>
            <td class="col-desc">{_esc(_truncate(desc))}</td>
            <td class="col-author">{_esc(it.get('channel') or '')}</td>
            <td class="col-heat"><span class='heat-views'>▶️</span> {views_str}</td>
        </tr>""")
    rows.append(_table_footer())
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Unified "新上榜单 / 上升最快 Top 20" trending section
# ---------------------------------------------------------------------------

_PLATFORM_BADGE = {
    "github":   '<span class="platform-badge badge-github" style="font-size:.7em;margin-right:4px">GitHub</span>',
    "x":        '<span class="platform-badge badge-x" style="font-size:.7em;margin-right:4px">X</span>',
    "youtube":  '<span class="platform-badge badge-youtube" style="font-size:.7em;margin-right:4px">YouTube</span>',
    "facebook": '<span class="platform-badge badge-facebook" style="font-size:.7em;margin-right:4px">Facebook</span>',
}


def _render_trending_section(items):
    """Render the unified cross-platform '新上榜单 / 上升最快 Top 20' table."""
    if not items:
        return '<p class="empty">暂无数据</p>'
    rows = ["""<table>
    <thead>
        <tr>
            <th class="col-rank">#</th>
            <th class="col-title">Title</th>
            <th class="col-desc">Description</th>
            <th class="col-heat">Momentum</th>
        </tr>
    </thead>
    <tbody>"""]

    for it in items:
        platform = it.get("platform", "")
        badge_cls = "badge-new" if it.get("badge") == "新" else ("badge-rising" if it.get("badge") == "上升" else "")
        badge_label = it.get("badge", "")
        badge_html = f'<span class="{badge_cls}">{badge_label}</span>' if badge_label else ""

        # Build title with platform badge
        title_raw = it.get("name") or it.get("title") or it.get("author") or it.get("page_name") or ""
        link = it.get("url", "")
        title_cell = _PLATFORM_BADGE.get(platform, "")
        if link:
            title_cell += f'<a href="{_esc(link)}" target="_blank">{_esc(title_raw)}</a>'
        else:
            title_cell += _esc(title_raw)
        title_cell += badge_html

        # Description
        desc = it.get("description") or it.get("text") or ""
        desc = _truncate(desc, 160)

        # Momentum: show score + velocity
        momentum = it.get("momentum_score", 0)
        velocity = it.get("velocity", "")
        if platform == "github" and velocity:
            heat = f"<b>{momentum:.2f}</b> <span style='color:#64748b;font-size:.75em'>({velocity:.0f} ⭐/day)</span>"
        else:
            heat = f"<b>{momentum:.2f}</b>"

        src = it.get("source", "")
        row_cls = ' class="row-example"' if src == "示例" else ""

        rows.append(f"""
        <tr{row_cls}>
            <td class="col-rank">{it.get('trending_rank', it.get('rank', ''))}</td>
            <td class="col-title">{title_cell}</td>
            <td class="col-desc">{_esc(_truncate(desc))}</td>
            <td class="col-heat">{heat}</td>
        </tr>""")

    rows.append(_table_footer())
    return "\n".join(rows)


def generate_index_html(dates, config):
    """Generate the site index page listing all available reports."""
    from utils.helpers import report_dir_name
    nav_links = ""
    for d in dates:
        report_name = report_dir_name(d)
        nav_links += (
            f'<div class="card"><a href="output/{report_name}/index.html">📅 {d}</a>'
            f' <a href="output/{report_name}/report.pdf" class="pdf-link">⬇ PDF</a></div>\n'
        )
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 项目每日排行榜</title>
<link rel="stylesheet" href="css/style.css">
</head>
<body>
<header>
    <div class="container">
        <h1>🤖 AI 项目 / AI Skill 每日排行榜</h1>
        <div class="date">GitHub · X · YouTube — Top {config.get('top_n', 20)}</div>
    </div>
</header>
<nav>
    <div class="container">
        <a href="index.html">🏠 首页</a>
        <a href="rss.xml">📡 RSS</a>
    </div>
</nav>
<main class="container">
    <div class="card">
        <h2>📅 历史报告</h2>
        {nav_links}
    </div>
</main>
<footer>
    <div class="container">由 GitHub Actions 自动生成 · Powered by ai-project-tracker skill</div>
</footer>
</body>
</html>
"""
    return html_content


def _build_summary(data):
    counts = {
        "github": len(data.get("github", [])),
        "x": len(data.get("x", [])),
        "youtube": len(data.get("youtube", [])),
        "facebook": len(data.get("facebook", [])),
    }
    total = sum(counts.values())

    def stat(ic, label, n):
        return f"""<div class="stat">
        <div class="ic">{ic}</div>
        <div><b>{n}</b><span>{label}</span></div>
    </div>"""

    cards = "".join([
        stat("🏆", "GitHub 仓库", counts["github"]),
        stat("🐦", "X 讨论", counts["x"]),
        stat("▶️", "YouTube 视频", counts["youtube"]),
        stat("📘", "Facebook 帖子", counts["facebook"]),
    ])
    return f"""
    <div class="stats">
        {cards}
        <div class="stat note"><div class="ic">ℹ️</div><div><span>共收录 <b>{total}</b> 条动态；GitHub 为实时数据，X/YouTube/Facebook 无密钥时展示示例数据（已淡化并标注）。</span></div></div>
    </div>"""


def generate_daily_html(date, data, config):
    """Generate a single self-contained daily HTML report (inline CSS)."""
    from utils.helpers import report_dir_name
    top_n = config.get("top_n", 20)

    trending_items = data.get("trending", [])
    trending_html = _render_trending_section(trending_items)
    github_html = _render_github_section(data.get("github", []))
    x_html = _render_x_section(data.get("x", []))
    youtube_html = _render_youtube_section(data.get("youtube", []))
    facebook_html = _render_facebook_section(data.get("facebook", []))
    x_bookmarks_html = _render_x_bookmarks_section(data.get("x_bookmarks", []))
    youtube_liked_html = _render_youtube_liked_section(data.get("youtube_liked", []))

    summary = _build_summary(data)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 项目每日排行榜 · {date}</title>
<style>
{REPORT_CSS}
</style>
</head>
<body>
<header>
    <div class="container">
        <h1>🤖 AI 项目 / AI Skill 每日排行榜</h1>
        <div class="date">{date} · 数据来源：GitHub / X / YouTube / Facebook</div>
    </div>
</header>
<nav>
    <div class="container">
        <a href="index.html">📄 本页</a>
        <a href="report.pdf">⬇ 下载 PDF</a>
    </div>
</nav>
<main class="container">
    <div class="report-links">
        <a class="btn btn-secondary" href="report.pdf">⬇ 下载 PDF 版本</a>
    </div>

    <div class="card">
        <h2>📊 今日概览</h2>
        {summary}
    </div>

    <div class="card trending">
        <h2>🚀 新上榜单 / 上升最快 Top {top_n}<span class="src-hint">跨平台 Momentum</span></h2>
        <p class="trending-desc">按「新鲜度 × 热度」综合评分，<span class="badge-new">新</span> = 最近 30 天发布，<span class="badge-rising">上升</span> = 高速度增长</p>
        <div class="table-wrap">
        {trending_html}
        </div>
    </div>

    <div class="card bookmarks">
        <h2>📚 本周收藏 · X<span class="src-hint">用户收藏</span></h2>
        <p class="trending-desc">本周收藏的 X/Twitter 帖子（需配置 OAuth token）</p>
        <div class="table-wrap">
        {x_bookmarks_html}
        </div>
    </div>

    <div class="card bookmarks">
        <h2>📚 本周收藏 · YouTube<span class="src-hint">用户收藏</span></h2>
        <p class="trending-desc">本周收藏的 YouTube 视频（需配置 OAuth token）</p>
        <div class="table-wrap">
        {youtube_liked_html}
        </div>
    </div>

    <div class="card github">
        <h2><span class="platform-badge badge-github">GitHub</span> AI 项目 Top {top_n}<span class="src-hint">实时</span></h2>
        <div class="table-wrap">
        {github_html}
        </div>
    </div>

    <div class="card x">
        <h2><span class="platform-badge badge-x">X</span> AI 讨论 Top {top_n}<span class="src-hint">无密钥时为例外数据</span></h2>
        <div class="table-wrap">
        {x_html}
        </div>
    </div>

    <div class="card youtube">
        <h2><span class="platform-badge badge-youtube">YouTube</span> AI 视频 Top {top_n}<span class="src-hint">无密钥时为例外数据</span></h2>
        <div class="table-wrap">
        {youtube_html}
        </div>
    </div>

    <div class="card facebook">
        <h2><span class="platform-badge badge-facebook">Facebook</span> AI 动态 Top {top_n}<span class="src-hint">公开页面抓取</span></h2>
        <div class="table-wrap">
        {facebook_html}
        </div>
    </div>
</main>
<footer>
    <div class="container">由 GitHub Actions 自动生成 · {date} · Powered by ai-project-tracker</div>
</footer>
</body>
</html>
"""
