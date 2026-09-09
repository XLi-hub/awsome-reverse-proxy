#!/usr/bin/env python3
"""Validate and merge Awesome Reverse Proxy candidate files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "data" / "inbox"
MERGED = ROOT / "data" / "candidates.yaml"

CATEGORIES = {
    "general-reverse-proxy",
    "load-balancer",
    "lightweight-proxy",
    "proxy-library",
    "cloud-native-proxy",
    "ingress-controller",
    "api-gateway",
    "service-mesh-gateway",
    "reverse-tunnel",
    "zero-trust-access",
    "proxy-management-ui",
}

REQUIRED_FIELDS = {
    "repo",
    "name",
    "category",
    "description_zh",
    "tags",
    "why_candidate",
    "source_queries",
    "status",
}

CANDIDATE_STATUSES = {"candidate", "needs-review", "historical"}

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9+.-]*$")


class CatalogError(Exception):
    """A human-readable catalog validation error."""


def load_candidate_file(path: Path) -> list[dict[str, Any]]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CatalogError(f"{path}: YAML 解析失败：{exc}") from exc

    if not isinstance(payload, list):
        raise CatalogError(f"{path}: 顶层必须是 YAML 数组")

    projects: list[dict[str, Any]] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise CatalogError(f"{path}:{index}: 每个候选必须是对象")
        projects.append(item)
    return projects


def _require_text(item: dict[str, Any], field: str, location: str) -> None:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{location}: {field} 必须是非空字符串")


def _require_string_list(item: dict[str, Any], field: str, location: str) -> None:
    value = item.get(field)
    if not isinstance(value, list) or not value:
        raise CatalogError(f"{location}: {field} 必须是非空数组")
    if any(not isinstance(entry, str) or not entry.strip() for entry in value):
        raise CatalogError(f"{location}: {field} 只能包含非空字符串")
    if len(value) != len(set(value)):
        raise CatalogError(f"{location}: {field} 含有重复值")


def validate_item(item: dict[str, Any], location: str) -> None:
    missing = sorted(REQUIRED_FIELDS - item.keys())
    if missing:
        raise CatalogError(f"{location}: 缺少字段：{', '.join(missing)}")

    unknown = sorted(item.keys() - REQUIRED_FIELDS)
    if unknown:
        raise CatalogError(f"{location}: 候选阶段存在未知字段：{', '.join(unknown)}")

    for field in ("repo", "name", "description_zh", "why_candidate"):
        _require_text(item, field, location)
    for field in ("tags", "source_queries"):
        _require_string_list(item, field, location)

    if not REPO_RE.fullmatch(item["repo"]):
        raise CatalogError(f"{location}: repo 必须采用 owner/name 格式")
    if item["category"] not in CATEGORIES:
        raise CatalogError(f"{location}: 未知分类 {item['category']!r}")
    if item["status"] not in CANDIDATE_STATUSES:
        allowed = ", ".join(sorted(CANDIDATE_STATUSES))
        raise CatalogError(f"{location}: inbox 中 status 必须是以下之一：{allowed}")

    invalid_tags = [tag for tag in item["tags"] if not TAG_RE.fullmatch(tag)]
    if invalid_tags:
        raise CatalogError(
            f"{location}: 标签必须是小写 ASCII 短标签：{', '.join(invalid_tags)}"
        )


def collect_candidates() -> tuple[list[dict[str, Any]], list[Path]]:
    paths = sorted(INBOX.glob("*.yaml"))
    if not paths:
        raise CatalogError(f"{INBOX}: 没有候选文件")

    candidates: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    for path in paths:
        for index, item in enumerate(load_candidate_file(path), start=1):
            location = f"{path.relative_to(ROOT)}:{index}"
            validate_item(item, location)
            key = item["repo"].casefold()
            if key in seen:
                raise CatalogError(
                    f"{location}: 仓库 {item['repo']} 与 {seen[key]} 重复"
                )
            seen[key] = location
            candidates.append(item)

    candidates.sort(key=lambda item: item["repo"].casefold())
    return candidates, paths


def render_candidates(candidates: list[dict[str, Any]]) -> str:
    header = "# 此文件由 scripts/catalog.py merge 生成，请勿手工编辑。\n"
    body = yaml.safe_dump(
        candidates,
        allow_unicode=True,
        sort_keys=False,
        width=100,
    )
    return header + body


def command_validate() -> int:
    candidates, paths = collect_candidates()
    print(f"通过：{len(paths)} 个候选文件，{len(candidates)} 个唯一仓库")
    return 0


def command_merge(check: bool) -> int:
    candidates, paths = collect_candidates()
    rendered = render_candidates(candidates)

    if check:
        current = MERGED.read_text(encoding="utf-8") if MERGED.exists() else ""
        if current != rendered:
            print(
                "失败：data/candidates.yaml 与候选文件不一致，请运行 "
                "`python3 scripts/catalog.py merge`。",
                file=sys.stderr,
            )
            return 1
        print(f"通过：合并文件已同步（{len(paths)} 个文件，{len(candidates)} 个仓库）")
        return 0

    MERGED.parent.mkdir(parents=True, exist_ok=True)
    MERGED.write_text(rendered, encoding="utf-8")
    print(f"已写入 {MERGED.relative_to(ROOT)}：{len(candidates)} 个仓库")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="校验所有 inbox 候选文件")
    merge = subparsers.add_parser("merge", help="生成统一候选池")
    merge.add_argument("--check", action="store_true", help="只检查生成文件是否同步")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "validate":
            return command_validate()
        return command_merge(args.check)
    except (CatalogError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
