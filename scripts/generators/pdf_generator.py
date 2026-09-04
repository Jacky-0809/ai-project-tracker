"""PDF report generator for the daily AI project report.

Uses reportlab (pure Python, no heavy system deps like weasyprint).
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT

from utils.helpers import ensure_dir


def _style_sheet():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="SectionTitle", parent=styles["Heading2"],
        textColor=colors.HexColor("#1e90ff"), spaceBefore=14, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Small", parent=styles["BodyText"], fontSize=9, textColor=colors.grey,
    ))
    styles.add(ParagraphStyle(
        name="Meta", parent=styles["BodyText"], fontSize=8.5, textColor=colors.grey,
    ))
    return styles


def _build_gh_table(items, styles):
    data = [["#", "Repo", "★", "Language"]]
    for it in items:
        data.append([
            str(it.get("rank", "")),
            it.get("name", ""),
            f"{it.get('stars', 0):,}",
            it.get("language") or "N/A",
        ])
    table = Table(data, colWidths=[10 * mm, 110 * mm, 22 * mm, 28 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e90ff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e0e6ee")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafd")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _build_x_table(items, styles):
    data = [["#", "Author", "Content", "Likes"]]
    for it in items:
        text = it.get("text", "").replace("\n", " ")
        if len(text) > 80:
            text = text[:80] + "…"
        data.append([
            str(it.get("rank", "")),
            it.get("author", ""),
            text,
            f"{it.get('likes', 0):,}",
        ])
    table = Table(data, colWidths=[8 * mm, 30 * mm, 105 * mm, 27 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1da1f2")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e0e6ee")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafd")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def _build_youtube_table(items, styles):
    data = [["#", "Title", "Channel", "Views"]]
    for it in items:
        title = it.get("title", "")
        if len(title) > 40:
            title = title[:40] + "…"
        views = it.get("views", 0)
        views_str = f"{views:,}" if views else "N/A"
        data.append([
            str(it.get("rank", "")),
            title,
            it.get("channel", ""),
            views_str,
        ])
    table = Table(data, colWidths=[8 * mm, 95 * mm, 40 * mm, 27 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ff0000")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e0e6ee")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafd")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def generate_pdf(path, date, data, config):
    """Generate a PDF report at the given path."""
    ensure_dir(path.rsplit("/", 1)[0])
    styles = _style_sheet()
    top_n = config.get("top_n", 20)

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"AI 项目每日排行榜 {date}",
    )
    story = []

    story.append(Paragraph(f"🤖 AI 项目 / AI Skill 每日排行榜", styles["Title"]))
    story.append(Paragraph(
        f"日期：{date}　·　数据来源：GitHub / X / YouTube　·　Top {top_n}",
        styles["Small"],
    ))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#1e90ff")))
    story.append(Spacer(1, 12))

    # GitHub
    gh = data.get("github", [])
    story.append(Paragraph(f"GitHub · AI 项目 Top {top_n}", styles["SectionTitle"]))
    if gh:
        story.append(_build_gh_table(gh, styles))
    else:
        story.append(Paragraph("暂无数据（可检查 GITHUB_TOKEN 配额后重试）", styles["BodyText"]))
    story.append(Spacer(1, 6))

    # X
    x = data.get("x", [])
    story.append(Paragraph(f"X (Twitter) · AI 讨论 Top {top_n}", styles["SectionTitle"]))
    if x:
        story.append(_build_x_table(x, styles))
    else:
        story.append(Paragraph("暂无数据（需配置 X_BEARER_TOKEN）", styles["BodyText"]))
    story.append(Spacer(1, 6))

    # YouTube
    yt = data.get("youtube", [])
    story.append(Paragraph(f"YouTube · AI 视频 Top {top_n}", styles["SectionTitle"]))
    if yt:
        story.append(_build_youtube_table(yt, styles))
    else:
        story.append(Paragraph("暂无数据（需配置 YOUTUBE_API_KEY）", styles["BodyText"]))

    doc.build(story)
    return path


if __name__ == "__main__":
    import os
    from utils.helpers import load_config
    from generators.html_generator import generate_daily_html
    cfg = load_config()
    test_data = {
        "github": [{"rank": 1, "name": "example/ai-agent", "url": "https://github.com/example/ai-agent",
                    "description": "Test AI agent", "stars": 12345, "forks": 999, "language": "Python",
                    "topics": ["ai", "agent"]}],
        "x": [{"rank": 1, "author": "@test", "text": "Testing AI project", "likes": 500, "retweets": 100,
               "replies": 20, "url": "https://x.com/test"}],
        "youtube": [{"rank": 1, "title": "Test AI Video", "channel": "Test Channel",
                     "description": "desc", "views": 100000, "url": "https://youtube.com"}],
    }
    generate_pdf("/tmp/test_report.pdf", "2026-09-04", test_data, cfg)
    print("PDF written: /tmp/test_report.pdf")
    print(os.path.getsize("/tmp/test_report.pdf"), "bytes")
