# Awesome Reverse Proxy

一个面向中文读者的开源反向代理项目精选目录。当前首版目录已生成，项目依据可复核的收录标准整理，而不是简单按 GitHub Star 排名。

查看：[正式项目目录](docs/CATALOG.md) · [优先审核队列](docs/REVIEW_QUEUE.md) · [收录方法](docs/PLAN.md) · [评分说明](docs/SCORING.md)

## 我们收录什么

- 通用反向代理与负载均衡器
- 云原生代理、Ingress Controller 与 Gateway API 实现
- API 网关与服务网格入口
- 反向隧道、内网穿透与零信任访问入口
- 反向代理管理面板
- 具备独立使用价值的轻量代理和代理库

纯正向代理、代理 IP 池、未修改 Fork、教学 Demo，以及以账号中转或规避平台限制为主要目的的项目不在默认收录范围内。

## 当前工作流

```text
GitHub 搜索与种子项目
        ↓
data/discovered.yaml（自动发现暂存，不自动收录）
        ↓
data/inbox/*.yaml（分组候选）
        ↓
字段校验与跨文件去重
        ↓
data/candidates.yaml（统一候选池）
        ↓
GitHub API 元数据补全
        ↓
data/reviews/*.yaml（分组审核）
        ↓
data/projects.yaml（审核状态与元数据）
        ↓
docs/CATALOG.md（正式收录）
```

收录方法、评分原则和多 Agent 协作约定见 [项目计划](docs/PLAN.md)，字段定义见 [数据规范](docs/DATA_SCHEMA.md)。

## 本地检查

需要 Python 3.10+ 和 PyYAML：

```bash
python3 scripts/catalog.py validate
python3 scripts/discover.py
python3 scripts/catalog.py merge
python3 scripts/enrich_github.py
python3 scripts/enrich_releases.py
python3 scripts/apply_reviews.py
python3 scripts/score_projects.py
python3 scripts/generate_readme.py

# CI 一致性检查
python3 scripts/catalog.py merge --check
python3 scripts/discover.py --check
python3 scripts/apply_reviews.py --check
python3 scripts/score_projects.py --check
python3 scripts/generate_readme.py --check
```

- `validate` 检查字段、分类、仓库名称和重复项。
- `discover.py` 搜索潜在新项目，以可解释的范围相关性规则降噪后只写人工分流暂存区，不会自动进入候选或正式目录；`--refilter-only` 可离线重筛已有结果。
- `merge` 将所有分组候选确定性地合并到 `data/candidates.yaml`。
- `enrich_github.py` 批量获取 GitHub 元数据并缓存；可选使用 `GITHUB_TOKEN` 或 `GH_TOKEN` 提高配额。
- `enrich_releases.py` 为正式项目补充最新 GitHub Release，并支持缓存和断点续跑。
- `apply_reviews.py` 验证审核覆盖率和安全门槛，再应用审核结论。
- `score_projects.py` 生成带版本和维度明细的可解释信号分。
- `generate_readme.py` 只将 `accepted` 项目写入正式目录。
- 各 `--check` 命令适合 CI，用于确认生成文件和发现暂存区没有过期或重复。

## 项目状态

当前共有 [74 个唯一候选](data/candidates.yaml)，其中 52 个已进入[正式目录](docs/CATALOG.md)，22 个保留在优先复核状态，另有 2 个已归档项目进入[排除记录](data/rejected.yaml)。

| 类别 | 候选 | 已收录 |
|---|---:|---:|
| API 网关 | 14 | 12 |
| 反向隧道 | 11 | 9 |
| 通用反向代理 | 7 | 6 |
| Kubernetes Ingress Controller | 7 | 6 |
| 负载均衡器 | 7 | 4 |
| 零信任访问入口 | 7 | 2 |
| 反代管理面板 | 6 | 4 |
| 代理库 | 5 | 4 |
| 轻量代理 | 4 | 3 |
| 云原生代理数据平面 | 3 | 2 |
| 服务网格网关 | 3 | 0 |

`needs-review` 不代表项目质量差，而是存在许可证、迁移关系、托管依赖、实验状态或目录边界需要进一步说明。正式目录中的 Star 是元数据抓取时的快照，不是实时值。
