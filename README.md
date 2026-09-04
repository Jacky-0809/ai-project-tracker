# AI 项目每日排行榜 (ai-project-tracker)

每日自动抓取 **GitHub**、**X (Twitter)**、**YouTube** 上排名前 20 的 **AI Skill** 和 **AI 项目**，生成 HTML + PDF 报告，发布到 GitHub Pages。

## 数据来源

| 平台 | 数据 | 所需密钥 | 无密钥后备 |
|------|------|---------|-----------|
| GitHub | AI 项目 / Skill 仓库（按 star 排序，Search API） | 可选（`GITHUB_TOKEN` 提高配额） | 匿名搜索 API（实测可用） |
| X | AI 讨论（Twitter API v2） | `X_BEARER_TOKEN` | 静态示例数据 |
| YouTube | AI 视频（Data API v3） | `YOUTUBE_API_KEY` | 空（预警提示） |

## 快速开始

```bash
pip install -r requirements.txt

# 生成今日报告（默认抓取真实数据）
python scripts/run.py

# 指定日期 / 跳过抓取复用缓存
python scripts/run.py --date 2026-09-04
python scripts/run.py --skip-scrape
```

## 产物结构

```
site/
├── index.html              # 首页：历史报告列表
├── rss.xml                 # RSS 订阅
├── css/style.css
└── output/
    └── Ai_skill_2026_09_04/   # 例：AI 项目当日报告
        ├── index.html      # 当日 HTML 报告（图文混排）
        ├── report.pdf      # 当日 PDF 报告（A4）
        └── data/report.json # 原始数据
```

## GitHub Actions 自动部署

`.github/workflows/daily.yml` 每天 UTC 00:30（北京时间 08:30）自动运行：

1. 运行 `scripts/run.py` 抓取数据、生成 HTML + PDF
2. 提交 `site/` 到仓库（历史归档）
3. 通过 `actions/upload-pages-artifact` + `actions/deploy-pages` 部署到 GitHub Pages

### 首次配置

1. 仓库 **Settings → Pages** → Source 选 **GitHub Actions**
2. 仓库 **Settings → Actions → General** → Workflow permissions 选 **Read and write permissions**
3. （可选）在 **Secrets** 添加 `X_BEARER_TOKEN`、`YOUTUBE_API_KEY`
4. 手动触发一次 workflow：Actions → **Daily AI Project Report** → Run workflow

### 访问

```
https://<user>.github.io/<repo>/output/Ai_skill_2026_09_04/
```

## 配置 (config.json)

```json
{
  "top_n": 20,
  "languages": ["Python", "TypeScript", "JavaScript"],
  "keywords": ["ai", "agent", "skill", "llm", "gpt", "ai-agent", "ai-skill", "opencode"],
  "output_site": "site",
  "github": { "min_stars": 50, "pushed_days": 14 },
  "facebook": {
    "pages": ["OpenAI", "DeepMind", "AnthropicAI", "MetaAILabs", "GoogleAI", "AIatMicrosoft"],
    "show_example_flag": true
  }
}
```

`facebook.pages` 配置用于（无鉴权）抓取公开页面动态；未配置密钥或抓取失败时自动降级到内置示例数据。

## 合规说明

- 爬取遵守各平台服务条款与 API 使用限制
- GitHub 未配置令牌时使用匿名公开 Search API；X / YouTube / Facebook 未配置密钥或网络不可达时自动降级到内置示例数据并在条目上标注「示例」
- 当网络不可达（连续请求失败）时启用快速降级模式，避免逐个请求超时拖慢流水线
- 内容仅为公开 AI 项目信息聚合，不含隐私数据

## 许可

MIT License
