---
name: ai-project-tracker
description: 每日抓取GitHub、X(Twitter)、YouTube上排名前20的AI Skill和AI项目，生成HTML和PDF每日报告并发布到GitHub Pages。当用户需要追踪AI项目动态、AI skill趋势、GitHub热门AI仓库、或生成AI项目日报时使用。
---

# AI项目追踪 Daily Report

每日自动抓取 **GitHub**、**X (Twitter)**、**YouTube**、**Facebook** 上排名前20的 **AI Skill** 和 **AI项目**，生成图文混合的HTML报告和PDF文件，发布到 GitHub Pages。

## 核心功能

- 抓取GitHub上star增长最快的AI项目/AI Skill仓库
- 抓取X上关于AI项目/Skill的热门讨论和推文
- 抓取YouTube上关于AI项目/Skill的热门视频
- 抓取Facebook公开页面的AI项目动态
- 生成当日排名前20的AI项目报告
- 输出HTML和PDF两种格式
- 自动发布到GitHub Pages

## 项目结构

```
ai-project-tracker/
├── .github/workflows/daily.yml    # GitHub Actions定时任务
├── scripts/
│   ├── scrapers/
│   │   ├── github_scraper.py     # GitHub AI项目爬虫
│   │   ├── x_scraper.py          # X AI讨论爬虫
│   │   ├── youtube_scraper.py    # YouTube AI视频爬虫
│   │   └── facebook_scraper.py   # Facebook AI动态爬虫
│   ├── generators/
│   │   ├── html_generator.py     # HTML报告生成器
│   │   └── pdf_generator.py      # PDF报告生成器
│   ├── utils/
│   │   └── helpers.py            # 共用工具
│   └── run.py                    # 主控脚本
├── data/                         # 原始JSON数据（运行期生成）
├── site/                         # 生成的静态站点（发布到 Pages）
│   ├── index.html               # 首页
│   ├── output/                  # 按日期组织的报告输出目录
│   │   └── Ai_skill_YYYY_MM_DD/ # 例：Ai_skill_2026_09_04
│   │       ├── index.html      # 当日HTML报告
│   │       ├── report.pdf      # 当日PDF报告
│   │       └── data/report.json # 原始数据
│   ├── css/style.css
│   └── rss.xml
├── config.json                   # 运行配置
├── requirements.txt
└── README.md
```

## 配置

### GitHub Secrets 配置

在仓库 Settings → Secrets and variables → Actions 中添加：

| 密钥名 | 必填 | 说明 |
|--------|------|------|
| `GITHUB_TOKEN` | 否 | 自动提供，用于GitHub API（提高速率限制） |
| `X_BEARER_TOKEN` | 否 | X API Bearer Token（有则提高抓取质量） |
| `YOUTUBE_API_KEY` | 否 | YouTube Data API Key |

### config.json 配置

项目根目录下 `config.json`：

```json
{
  "top_n": 20,
  "languages": ["Python", "TypeScript"],
  "keywords": ["ai", "agent", "skill", "llm", "gpt", "ai-agent", "ai-skill"],
  "output_site": "site",
  "timezone": "Asia/Shanghai"
}
```

## 使用方式

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行（当前日期）
python scripts/run.py

# 指定日期（用于测试）
python scripts/run.py --date 2026-09-04
```

### GitHub Actions 自动运行

默认每天 UTC 00:30（北京时间 08:30）自动运行，也可手动触发：

1. 进入仓库 Actions 标签页
2. 选择 "Daily AI Project Report"
3. 点击 "Run workflow"

## 部署到 GitHub Pages

1. 将本skill目录内容放入你的仓库（如 `~/.opencode/skills/ai-project-tracker/`）
2. 仓库 Settings → Pages → Source 选择 **GitHub Actions**
3. 仓库 Settings → Actions → General → Workflow permissions 选择 **Read and write permissions**
4. 首次手动触发 workflow 生成报告

## 页面访问

生成后可通过 GitHub Pages 访问：

```
https://<username>.github.io/<repo>/output/Ai_skill_2026_09_04/
```

或访问首页 `index.html` 查看最新报告列表。

## 注释与合规

- 遵守 GitHub / X / YouTube / Facebook 的 API 使用条款和 robots.txt
- 设置合理的抓取频率，避免触发限流
- 内容仅为 AI 项目信息聚合，不涉及隐私
- 若 API 不可用或网络不可达，脚本会自动降级：GitHub 用匿名公开 Search API，X/YouTube/Facebook 用无鉴权公开源，最终回退到内置示例数据（条目标注「示例」）
- 网络不可达时自动启用快速降级模式，避免逐个请求超时拖慢流水线

## 扩展功能

- RSS 订阅推送
- 邮件/微信推送每日报告
- 项目趋势数据分析

## 许可

MIT License
