"""HTML report generator for the daily AI project report."""
import html as html_mod
from utils.helpers import ensure_dir


def _esc(text):
    """Escape HTML special characters."""
    if text is None:
        return ""
    return html_mod.escape(str(text))


def _render_github_section(items):
    if not items:
        return '<p class="empty">暂无 GitHub 数据（可检查 GITHUB_TOKEN 配额后重试）</p>'
    rows = []
    for it in items:
        lang = _esc(it.get("language") or "N/A")
        topics = "".join(
            f'<span class="tag">{_esc(t)}</span>' for t in it.get("topics", [])[:4]
        )
        rows.append(f"""
        <div class="rank-item">
            <div class="rank">{it['rank']}</div>
            <div class="content">
                <div class="title"><a href="{_esc(it['url'])}" target="_blank">{_esc(it['name'])}</a></div>
                <div class="desc">{_esc(it.get('description') or '')}</div>
                <div class="meta">
                    <span class="metric stars">★ {it.get('stars', 0)}</span>
                    <span class="metric">🍴 {it.get('forks', 0)}</span>
                    <span class="metric">Lang: {lang}</span>
                    {topics}
                </div>
            </div>
        </div>""")
    return "\n".join(rows)


def _render_x_section(items):
    if not items:
        return '<p class="empty">暂无 X 数据（需配置 X_BEARER_TOKEN）</p>'
    rows = []
    for it in items:
        rows.append(f"""
        <div class="rank-item">
            <div class="rank">{it['rank']}</div>
            <div class="content">
                <div class="title"><a href="{_esc(it.get('url',''))}" target="_blank">{_esc(it.get('author',''))}</a></div>
                <div class="desc">{_esc(it.get('text') or '')}</div>
                <div class="meta">
                    <span class="metric">❤️ {it.get('likes', 0)}</span>
                    <span class="metric">🔁 {it.get('retweets', 0)}</span>
                    <span class="metric">💬 {it.get('replies', 0)}</span>
                </div>
            </div>
        </div>""")
    return "\n".join(rows)


def _render_youtube_section(items):
    if not items:
        return '<p class="empty">暂无 YouTube 数据（需配置 YOUTUBE_API_KEY）</p>'
    rows = []
    for it in items:
        views = it.get("views", 0)
        views_str = f"{views:,}" if views else "N/A"
        rows.append(f"""
        <div class="rank-item">
            <div class="rank">{it['rank']}</div>
            <div class="content">
                <div class="title"><a href="{_esc(it.get('url',''))}" target="_blank">{_esc(it.get('title') or '')}</a></div>
                <div class="desc">{_esc(it.get('channel') or '')}</div>
                <div class="desc">{_esc(it.get('description') or '')[:150]}</div>
                <div class="meta">
                    <span class="metric">▶️ {views_str} views</span>
                </div>
            </div>
        </div>""")
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


def generate_daily_html(date, data, config):
    """Generate a single self-contained daily HTML report."""
    from utils.helpers import report_dir_name
    top_n = config.get("top_n", 20)
    report_name = report_dir_name(date)
    github_html = _render_github_section(data.get("github", []))
    x_html = _render_x_section(data.get("x", []))
    youtube_html = _render_youtube_section(data.get("youtube", []))

    summary = _build_summary(data)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 项目每日排行榜 · {date}</title>
<link rel="stylesheet" href="../../../css/style.css">
</head>
<body>
<header>
    <div class="container">
        <h1>🤖 AI 项目 / AI Skill 每日排行榜</h1>
        <div class="date">{date} · 数据来源：GitHub / X / YouTube</div>
    </div>
</header>
<nav>
    <div class="container">
        <a href="../../../index.html">🏠 首页</a>
        <a href="report.pdf">⬇ 下载 PDF</a>
        <a href="index.html">📄 本页</a>
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

    <div class="card">
        <h2><span class="platform-badge badge-github">GitHub</span> AI 项目 Top {top_n}</h2>
        {github_html}
    </div>

    <div class="card">
        <h2><span class="platform-badge badge-x">X</span> AI 讨论 Top {top_n}</h2>
        {x_html}
    </div>

    <div class="card">
        <h2><span class="platform-badge badge-youtube">YouTube</span> AI 视频 Top {top_n}</h2>
        {youtube_html}
    </div>
</main>
<footer>
    <div class="container">由 GitHub Actions 自动生成 · {date} · Powered by ai-project-tracker skill</div>
</footer>
</body>
</html>
"""


def _build_summary(data):
    github, x, youtube = data.get("github", []), data.get("x", []), data.get("youtube", [])
    gh_str = f"<b>{len(github)}</b> 个仓库" if github else "无"
    x_str = f"<b>{len(x)}</b> 条讨论" if x else "无"
    yt_str = f"<b>{len(youtube)}</b> 个视频" if youtube else "无"
    total = len(github) + len(x) + len(youtube)
    return f"""
    <p>本次共收录 <b>{total}</b> 条 AI 动态：</p>
    <ul>
        <li>🏆 GitHub：收录 {gh_str}</li>
        <li>🐦 X：收录 {x_str}</li>
        <li>▶️ YouTube：收录 {yt_str}</li>
    </ul>
    <p>如需更多数据，请为 X 和 YouTube 配置对应的 API 密钥。</p>
    """
