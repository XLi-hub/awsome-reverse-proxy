# 数据规范

## 1. 自动发现暂存区

`data/discovered.yaml` 是自动搜索的待分流结果，不属于正式候选。每条记录包含：

```yaml
- repo: owner/repository
  name: Project Name
  description: GitHub repository description
  stars_at_discovery: 1234
  language: Go
  license_spdx: Apache-2.0
  topics: [reverse-proxy]
  found_by: [topic:reverse-proxy archived:false fork:false stars:>=100]
  relevance_score: 3
  matched_signals: [topic:reverse-proxy]
  discovered_at: 2026-09-09
  triage_status: unreviewed
```

`relevance_score` 只衡量与目录范围的相关性，不代表质量、安全性或推荐等级。自动任务只写该文件；维护者核实上游、用途和许可证后，才可将项目移入 `data/inbox/*.yaml`。运行 `python3 scripts/discover.py --check` 可检查去重、相关性规则和与已知项目的隔离。

## 2. 候选文件

`data/inbox/*.yaml` 是研究阶段的人工输入。顶层必须是 YAML 数组，每个仓库只出现一次：

```yaml
- repo: owner/repository
  name: Project Name
  category: general-reverse-proxy
  description_zh: 项目的客观中文定位。
  tags:
    - http
    - tls
  why_candidate: 说明它为何值得进入人工审核，而不是直接作推荐结论。
  source_queries:
    - topic:reverse-proxy
  status: candidate
```

### 必填字段

| 字段 | 类型 | 规则 |
|---|---|---|
| `repo` | string | GitHub 的 `owner/name`，不带 URL 和 `.git` |
| `name` | string | 项目公开名称 |
| `category` | enum | 必须是计划文档中定义的分类标识 |
| `description_zh` | string | 客观中文简介，不使用最高级宣传语 |
| `tags` | string[] | 小写短标签，至少一个 |
| `why_candidate` | string | 可审核的候选理由 |
| `source_queries` | string[] | 发现渠道或搜索式，至少一个 |
| `status` | enum | `candidate`、`needs-review` 或 `historical` |

候选文件不手工记录 Star、Fork 等易变化数据，这些字段由集中式抓取任务统一补全。

- `candidate`：等待常规审核；
- `needs-review`：已经发现维护状态、许可证或边界问题，需要优先裁决；
- `historical`：保留历史价值，但不应进入活跃项目排行。

## 3. 统一候选池

`data/candidates.yaml` 由脚本生成，结构与候选文件一致。该文件按 `repo` 的大小写无关顺序排列，不应手工编辑。

生成命令：

```bash
python3 scripts/catalog.py merge
```

## 4. 正式项目

`data/projects.yaml` 在候选字段基础上增加审核字段和自动元数据。目标结构如下：

```yaml
- repo: owner/repository
  name: Project Name
  category: general-reverse-proxy
  description_zh: 项目的客观中文定位。
  tags: [http, tls]
  suitable_for:
    - 需要 TLS 终止的自托管服务
  limitations:
    - 高级功能需要理解其配置模型
  status: accepted
  reviewed_at: 2026-01-31
  review_notes: 已核对官方 README、许可证和最新发布。
  github:
    url: https://github.com/owner/repository
    description: Upstream description
    stars: 1234
    forks: 123
    language: Go
    license_spdx: Apache-2.0
    archived: false
    is_fork: false
    pushed_at: 2026-01-30T12:00:00Z
    latest_release: v1.2.3
    latest_release_at: 2026-01-20T12:00:00Z
    release_fetched_at: 2026-01-31T12:00:00Z
    fetched_at: 2026-01-31T12:00:00Z
```

### 字段所有权

- 人工字段：`description_zh`、`category`、`tags`、`suitable_for`、`limitations`、审核字段；
- 自动字段：整个 `github` 对象；
- 抓取程序只能替换 `github`，不得覆盖人工字段；
- README 生成程序只读取数据，不反向修改数据文件。

在项目正式进入 `accepted` 或 `historical` 前，`data/inbox/*.yaml` 仍是人工字段的来源，重新补全会同步候选描述与状态、复用已有 `github` 缓存。正式审核后的项目以 `data/projects.yaml` 为准，候选刷新不得覆盖其审核结论。

### 审核记录

`data/reviews/*.yaml` 允许多个审核者按类别并行工作，统一由脚本应用到正式项目文件：

```yaml
- repo: owner/repository
  decision: accepted
  suitable_for:
    - 自托管 Web 服务入口
  limitations:
    - 只提供 HTTP 代理
  review_notes: 已核对官方 README、许可证和最小部署文档。
  evidence_urls:
    - https://github.com/owner/repository
  reviewed_at: 2026-09-08
```

运行 `python3 scripts/apply_reviews.py` 前，审核文件必须完整覆盖 `data/projects.yaml`，不能包含重复或未知仓库。`accepted` 项目还必须拥有明确的非归档、非 Fork 和单一 SPDX License 元数据；复杂或无法自动识别的许可证保持 `needs-review`。

## 5. 排除记录

`data/rejected.yaml` 保存稳定的排除结论：

```yaml
- repo: owner/repository
  reason_code: forward-proxy-only
  reason_zh: 项目只提供正向代理，不属于本目录范围。
  reviewed_at: 2026-01-31
  replacement: null
```

建议使用的 `reason_code`：

- `forward-proxy-only`
- `proxy-list-or-pool`
- `demo-only`
- `unmodified-fork`
- `archived-or-deprecated`
- `duplicate-or-mirror`
- `out-of-scope`
- `unsafe-primary-purpose`
- `unclear-license`

许可证不清晰的项目可以先进入 `needs-review`；只有明确决定不收录时才写入排除记录。

## 6. 规范化规则

- `repo` 是唯一键，比较时忽略大小写；
- `repo` 重命名后使用 GitHub 当前规范名称，旧名称记录在未来的 `aliases` 字段；
- 标签使用小写 ASCII 和连字符，例如 `gateway-api`；
- 中文描述句末使用中文标点，名称、协议和产品名保留官方写法；
- 数组去重并保持有意义的顺序；
- 日期使用 `YYYY-MM-DD`，时间使用带时区的 ISO 8601；
- 缺失信息使用 `null`，不要用空字符串、`unknown` 或猜测值代替。
