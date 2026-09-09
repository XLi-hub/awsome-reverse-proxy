# 贡献指南

感谢帮助维护 Awesome Reverse Proxy。本目录优先保证可验证性，不以收集最多链接为目标。

## 推荐项目

提交前请确认：

- 项目以反向代理、入口网关、负载均衡或反向隧道为核心能力；
- GitHub 仓库是规范上游，不是未修改 Fork 或镜像；
- 仓库未归档，README 未声明弃用；
- 项目不是代理 IP 池、订阅转换、破解或账号中转工具；
- 推荐描述能够由 README、官方文档或许可证直接验证。

优先使用“推荐项目”Issue 模板。维护者确认分类后，再将项目加入对应的 `data/inbox/*.yaml`。

## 修改候选数据

候选条目必须符合 [数据规范](docs/DATA_SCHEMA.md)。不要手工编辑生成文件 `data/candidates.yaml`、动态 GitHub 字段或 `docs/CATALOG.md`。

修改后运行：

```bash
python3 scripts/catalog.py validate
python3 scripts/catalog.py merge
python3 scripts/enrich_github.py
python3 scripts/apply_reviews.py
python3 scripts/score_projects.py
python3 scripts/generate_readme.py
python3 -m unittest discover -s tests
```

## 审核要求

- 中文简介应描述实际能力，不复制宣传口号；
- “生产可用”“高性能”“安全”等结论必须附直接证据；
- 复杂、混合或附加条款许可证保持 `needs-review`；
- 托管控制面、商业版本和开源核心必须分别说明；
- 实验项目、维护模式和迁移项目不得按普通活跃项目展示；
- 每条审核至少包含 GitHub 仓库、README/官方文档和许可证证据。

## Pull Request

一个 PR 尽量只处理一个类别或一种机械更新。说明新增、删除或状态变化的理由，并确认所有 `--check` 命令通过。自动刷新 PR 只更新元数据，不应改变人工审核结论。

