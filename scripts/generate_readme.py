#!/usr/bin/env python3
"""Generate the reviewed project catalog from data/projects.yaml."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "data" / "projects.yaml"
OUTPUT = ROOT / "docs" / "CATALOG.md"

CATEGORIES = (
    ("general-reverse-proxy", "通用反向代理"),
    ("load-balancer", "负载均衡器"),
    ("lightweight-proxy", "轻量或嵌入式代理"),
    ("proxy-library", "代理开发库"),
    ("cloud-native-proxy", "云原生代理数据平面"),
    ("ingress-controller", "Kubernetes Ingress Controller"),
    ("api-gateway", "API 网关"),
    ("service-mesh-gateway", "服务网格网关"),
    ("reverse-tunnel", "反向隧道与内网穿透"),
    ("zero-trust-access", "零信任访问入口"),
    ("proxy-management-ui", "反代管理面板"),
)
CATEGORY_KEYS = {key for key, _ in CATEGORIES}


class CatalogGenerationError(Exception):
    """A human-readable catalog generation error."""


def load_projects(path: Path) -> list[dict[str, Any]]:
    """Load the project list and reject structures that cannot be rendered safely."""
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CatalogGenerationError(f"{path}: YAML 解析失败：{exc}") from exc

    if payload is None:
        return []
    if not isinstance(payload, list):
        raise CatalogGenerationError(f"{path}: 顶层必须是 YAML 数组")

    projects: list[dict[str, Any]] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise CatalogGenerationError(f"{path}:{index}: 每个项目必须是对象")
        if item.get("status") != "accepted":
            continue
        category = item.get("category")
        if category not in CATEGORY_KEYS:
            raise CatalogGenerationError(
                f"{path}:{index}: accepted 项目使用了未知分类 {category!r}"
            )
        projects.append(item)
    return projects


def markdown_escape(value: Any) -> str:
    """Escape arbitrary scalar text for use in a Markdown table cell."""
    if value is None or value == "":
        return "—"
    if isinstance(value, (dt.date, dt.datetime)):
        text = value.isoformat()
    else:
        text = str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\\", "\\\\")
    for character in ("`", "*", "_", "[", "]", "<", ">", "|"):
        text = text.replace(character, f"\\{character}")
    return text.replace("\n", "<br>")


def _project_url(project: dict[str, Any]) -> str:
    repo = project.get("repo")
    if not isinstance(repo, str) or "/" not in repo:
        raise CatalogGenerationError("accepted 项目的 repo 必须采用 owner/name 格式")
    owner, name = repo.split("/", 1)
    if not owner or not name:
        raise CatalogGenerationError("accepted 项目的 repo 必须采用 owner/name 格式")
    return f"https://github.com/{quote(owner, safe='')}/{quote(name, safe='')}"


def _stars(project: dict[str, Any]) -> int | None:
    github = project.get("github")
    if not isinstance(github, dict):
        return None
    stars = github.get("stars")
    if isinstance(stars, bool) or not isinstance(stars, int) or stars < 0:
        return None
    return stars


def _score(project: dict[str, Any]) -> float | None:
    score = project.get("score")
    total = score.get("total") if isinstance(score, dict) else None
    return float(total) if isinstance(total, (int, float)) and not isinstance(total, bool) else None


def _sort_key(project: dict[str, Any]) -> tuple[float, int, str, str]:
    stars = _stars(project)
    signal = _score(project)
    name = project.get("name")
    repo = project.get("repo")
    return (
        -(signal if signal is not None else -1),
        -(stars if stars is not None else -1),
        str(name or "").casefold(),
        str(repo or "").casefold(),
    )


def _tags(project: dict[str, Any]) -> str:
    tags = project.get("tags")
    if not isinstance(tags, list) or not tags:
        return "—"
    rendered = [markdown_escape(tag) for tag in tags if tag is not None and tag != ""]
    return "、".join(rendered) if rendered else "—"


def _github_field(project: dict[str, Any], field: str) -> Any:
    github = project.get("github")
    return github.get(field) if isinstance(github, dict) else None


def _render_row(project: dict[str, Any]) -> str:
    name = markdown_escape(project.get("name") or project.get("repo"))
    url = _project_url(project)
    description = markdown_escape(project.get("description_zh"))
    license_name = markdown_escape(_github_field(project, "license_spdx"))
    stars = _stars(project)
    stars_text = f"{stars:,}" if stars is not None else "—"
    latest_release = markdown_escape(_github_field(project, "latest_release"))
    signal = _score(project)
    signal_text = f"{signal:.1f}" if signal is not None else "—"
    reviewed_at = markdown_escape(project.get("reviewed_at"))
    return (
        f"| [{name}]({url}) | {description} | {_tags(project)} | "
        f"{license_name} | {stars_text} | {latest_release} | {signal_text} | {reviewed_at} |"
    )


def render_catalog(projects: list[dict[str, Any]]) -> str:
    """Render accepted projects as a deterministic, category-grouped catalog."""
    accepted = [project for project in projects if project.get("status") == "accepted"]
    grouped = {key: [] for key, _ in CATEGORIES}
    for project in accepted:
        category = project.get("category")
        if category not in grouped:
            raise CatalogGenerationError(f"accepted 项目使用了未知分类 {category!r}")
        grouped[category].append(project)

    lines = [
        "<!-- 此文件由 scripts/generate_readme.py 生成，请勿手工编辑。 -->",
        "",
        "# 正式项目目录",
        "",
        "本页仅展示状态为 `accepted` 的项目。Star 是抓取快照；信号分用于目录排序，不代表绝对质量。",
        "",
    ]
    if not accepted:
        lines.extend(["目前暂无通过审核的项目。", ""])

    for category, title in CATEGORIES:
        lines.extend([f"## {title}", ""])
        entries = sorted(grouped[category], key=_sort_key)
        if not entries:
            lines.extend(["暂无已通过审核的项目。", ""])
            continue
        lines.extend(
            [
                "| 项目 | 客观简介 | 标签 | License | Star | 最新 Release | 信号分 | 最后复核日 |",
                "|---|---|---|---|---:|---|---:|---|",
                *(_render_row(project) for project in entries),
                "",
            ]
        )
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def generate(input_path: Path, output_path: Path, check: bool = False) -> int:
    projects = load_projects(input_path)
    rendered = render_catalog(projects)

    if check:
        current = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        if current != rendered:
            print(
                f"失败：{output_path} 与 {input_path} 不一致，请运行 "
                "`python3 scripts/generate_readme.py`。",
                file=sys.stderr,
            )
            return 1
        print(f"通过：正式目录已同步（{len(projects)} 个项目）")
        return 0

    _atomic_write(output_path, rendered)
    try:
        display_path = output_path.relative_to(ROOT)
    except ValueError:
        display_path = output_path
    print(f"已写入 {display_path}：{len(projects)} 个项目")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只检查生成文件是否同步")
    parser.add_argument("--input", type=Path, default=PROJECTS, help="正式项目 YAML 文件")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="生成的 Markdown 文件")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return generate(args.input, args.output, args.check)
    except (CatalogGenerationError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
