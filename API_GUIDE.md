# API 获取与配置指南（X / YouTube）

本项目已在 `.github/workflows/daily.yml` 中通过 `env` 接收两个 secret（缺省时自动降级到示例数据）：

```yaml
env:
  X_BEARER_TOKEN: ${{ secrets.X_BEARER_TOKEN }}
  YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
```

Python 侧读取方式（`scripts/scrapers/x_scraper.py` / `youtube_scraper.py`）：

```python
import os
token = os.environ.get("X_BEARER_TOKEN")   # X API v2
key   = os.environ.get("YOUTUBE_API_KEY")  # YouTube Data API v3
```

在 GitHub 仓库 → **Settings → Secrets and variables → Actions → New repository secret** 填写保密名与值即可。推送即自动生效。

---

## 1. X (Twitter) — `X_BEARER_TOKEN`

### 官方 API（付费，2026 现状）

- 入口：`console.x.com`（原 developer.twitter.com）
- 新开发者**没有免费层**；采用预付费点数（pay-per-use）。读帖子约 $0.005/条，搜索约 $0.005/结果，趋势约 $0.010/次。
- 评价：对"每日爬取趋势/时间线"用途**性价比低**，建议不采用官方 API。

### 推荐：免费无鉴权方案（无需 key）

| 方案 | 拿到的数据 | 说明 |
|------|-----------|------|
| **trends24.in HTML 抓取** | 各区域上挑 50 趋势词 | `trend-tap`/`trend-pulse`/`trending-scraper` 均用此法，零 key 零限流 |
| **X syndication 接口** | 用户时间线 ~20 条 | `syndication.twitter.com/srv/timeline-profile/screen-name/{user}`，无鉴权（本项目当前已采用该降级路径） |
| **Guest-token GraphQL（scweet/twifork）** | 时间线/趋势/资料 | 与 X 网页嵌入同源，无付费 key |

> 建议：X 保持现有 syndication 无鉴权方案即可；如需要趋势词再叠加 `trends24.in` 抓取。

---

## 2. YouTube — `YOUTUBE_API_KEY`

### 官方 API（免费，推荐）

1. 打开 <https://console.cloud.google.com>，新建（或选择）一个项目。
2. **APIs & Services → Library** → 搜索 "YouTube Data API v3" → **Enable**。
3. **APIs & Services → Credentials → Create credentials → API key**，复制。
4. 建议点击该 key → **API restrictions** → 仅勾选 "YouTube Data API v3"，降低被滥用风险。

### 配额（2026，免费）

- 默认每日 **10,000 单位**（太平洋时间午夜重置）。
- `search.list` 100 单位/次（每日约 100 次）；`videos.list` / `channels.list` 1 单位/次。
- 对本项目每日一次、单频道抓取绰绰有余。

### 备选：无 key 免费方案

- **YouTube RSS**：`https://www.youtube.com/feeds/videos.xml?channel_id=UC...`（每频道最新 15 条，已有代码后盾）
- **yt-dlp / Invidious**：无需 key。

> 建议：**配置 YouTube API key**（真免费、够用），配合 RSS 兜底，即可拿到 YouTube 实时数据。

---

## 3. 相似开源实现参考（研究结论）

| 仓库 | 做法 | 是否付费 key |
|------|------|------------|
| `kastrah/trending-scraper` | multi-platform 趋势→SQLite→预警，X 用 syndication+trends24、YT 用 API+yt-dlp | 无需 |
| `XiaoYiWeio/trend-tap` | 7 平台聚合，X 直接爬 trends24.in 纯标准库 | 零 key |
| `claude-world/trend-pulse` | 37 源聚合插件化，X/YT 均免费抓取，bearer 仅提升限流 | 无需 |
| `hchen13/github-daily` | 每日 GitHub+AI agent 仓库 → HTML/PDF/JPEG → Pages | GitHub token |
| `linny006/trending-claude-skills` | GitHub 搜索自动榜单 → Pages | GitHub token |

**结论**：所有抓 X/YT 的开源项目都用免费方法（syndication/trends24/RSS/yt-dlp），官方付费 X API 在该场景不划算；YouTube 官方 key 免费且最可靠。

---

## 4. 本周收藏功能 — X Bookmarks & YouTube Liked Videos

报告新增「📚 本周收藏」章节，聚合用户在 X 和 YouTube 上本周收藏/点赞的内容。需要 **OAuth 2.0 用户级 Token**（不同于前面的 App-level Bearer Token）。

### 4.1 X Bookmarks — `X_USER_ID` + `X_ACCESS_TOKEN`

X 的收藏（Bookmarks）是**私有数据**，必须使用 OAuth 2.0 User Context 访问。

#### 获取步骤

1. 登录 <https://console.x.com> → 你的 Developer Portal 项目
2. **Keys and tokens** → 确保你的 App 的 **User authentication settings** 已开启 OAuth 2.0，权限范围包含 `bookmark.read`
3. 用 OAuth 2.0 Authorization Code Flow 获取 User Access Token：
   - 构造授权 URL：`https://twitter.com/i/oauth2/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT&response_type=code&scope=bookmark.read+tweet.read+users.read&state=xyz`
   - 用户授权后拿到 `code`
   - 用 `code` 换取 `access_token`（POST `https://api.twitter.com/2/oauth2/token`）
4. 获取你的 numeric User ID（GET `https://api.twitter.com/2/users/me`）

#### GitHub Actions Secrets 配置

```
X_USER_ID        = 你的数字用户 ID（如 1234567890）
X_ACCESS_TOKEN   = OAuth 2.0 User Access Token（有 bookmark.read 权限）
```

#### 本地测试

```bash
export X_USER_ID="1234567890"
export X_ACCESS_TOKEN="eyJhbGciOi..."
python scripts/scrapers/x_bookmarks_scraper.py
```

### 4.2 YouTube Liked Videos — OAuth 2.0

YouTube 的「喜欢的视频」也是**私有数据**，需要 OAuth 2.0 授权。

#### 获取步骤

1. <https://console.cloud.google.com> → 你的项目 → **APIs & Services → Credentials**
2. **Create Credentials → OAuth client ID** → 选择 "Web application"
3. 添加 Authorized redirect URI：`https://localhost`（本地测试用）
4. 记录 `client_id` 和 `client_secret`
5. 构造授权 URL：`https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_ID&redirect_uri=https://localhost&response_type=code&scope=https://www.googleapis.com/auth/youtube.readonly&access_type=offline`
6. 浏览器打开该 URL → 授权 → 拿到 `code`
7. 用 `code` 换取 `refresh_token`（POST `https://oauth2.googleapis.com/token`）

#### GitHub Actions Secrets 配置

```
YOUTUBE_CLIENT_ID      = OAuth 2.0 Client ID
YOUTUBE_CLIENT_SECRET  = OAuth 2.0 Client Secret
YOUTUBE_REFRESH_TOKEN  = 授权后获得的 Refresh Token
```

> Refresh Token 有效期很长（通常不 expires），每次运行时自动换取 Access Token。

#### 本地测试

```bash
export YOUTUBE_CLIENT_ID="xxxxx.apps.googleusercontent.com"
export YOUTUBE_CLIENT_SECRET="GOCSPX-xxxxx"
export YOUTUBE_REFRESH_TOKEN="1//0xxxxx"
python scripts/scrapers/youtube_liked_scraper.py
```

### 4.3 无 Token 时的行为

未配置 OAuth Token 时，收藏章节自动降级到**内置示例数据**（20 条 AI skill 相关内容），条目标注「示例」且样式淡化，与现有 X/YouTube 降级逻辑一致。