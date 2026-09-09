#!/usr/bin/env python3
"""Validate category review files and apply decisions to data/projects.yaml."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]
REVIEWS_DIR = ROOT / "data" / "reviews"
PROJECTS = ROOT / "data" / "projects.yaml"

DECISIONS = {"accepted", "needs-review", "rejected"}
REQUIRED_FIELDS = {
    "repo", "decision", "suitable_for", "limitations", "review_notes",
    "evidence_urls", "reviewed_at",
}
UNSAFE_LICENSE_VALUES = {None, "", "NOASSERTION", "OTHER"}


class ReviewError(Exception):
    """A human-readable review validation error."""


def load_yaml_list(path: Path) -> list[dict[str, Any]]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ReviewError(f"{path}: YAML 解析失败：{exc}") from exc
    if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
        raise ReviewError(f"{path}: 顶层必须是对象数组")
    return payload


def _string_list(value: Any, *, field: str, location: str, allow_empty: bool) -> None:
    if not isinstance(value, list) or (not allow_empty and not value):
        suffix = "数组" if allow_empty else "非空数组"
        raise ReviewError(f"{location}: {field} 必须是{suffix}")
    if any(not isinstance(entry, str) or not entry.strip() for entry in value):
        raise ReviewError(f"{location}: {field} 只能包含非空字符串")
    if len(value) != len(set(value)):
        raise ReviewError(f"{location}: {field} 含重复值")


def validate_review(review: dict[str, Any], location: str) -> None:
    missing = sorted(REQUIRED_FIELDS - review.keys())
    unknown = sorted(review.keys() - REQUIRED_FIELDS)
    if missing:
        raise ReviewError(f"{location}: 缺少字段：{', '.join(missing)}")
    if unknown:
        raise ReviewError(f"{location}: 未知字段：{', '.join(unknown)}")

    repo = review.get("repo")
    if not isinstance(repo, str) or repo.count("/") != 1:
        raise ReviewError(f"{location}: repo 必须采用 owner/name 格式")
    if review.get("decision") not in DECISIONS:
        raise ReviewError(f"{location}: decision 必须是 accepted、needs-review 或 rejected")
    _string_list(review.get("suitable_for"), field="suitable_for", location=location, allow_empty=False)
    _string_list(review.get("limitations"), field="limitations", location=location, allow_empty=True)
    _string_list(review.get("evidence_urls"), field="evidence_urls", location=location, allow_empty=False)
    notes = review.get("review_notes")
    if not isinstance(notes, str) or not notes.strip():
        raise ReviewError(f"{location}: review_notes 必须是非空字符串")

    reviewed_at = review.get("reviewed_at")
    if isinstance(reviewed_at, dt.datetime):
        raise ReviewError(f"{location}: reviewed_at 必须是日期而不是时间")
    if isinstance(reviewed_at, dt.date):
        reviewed_at = reviewed_at.isoformat()
    if not isinstance(reviewed_at, str):
        raise ReviewError(f"{location}: reviewed_at 必须采用 YYYY-MM-DD")
    try:
        dt.date.fromisoformat(reviewed_at)
    except ValueError as exc:
        raise ReviewError(f"{location}: reviewed_at 必须采用 YYYY-MM-DD") from exc

    urls = review["evidence_urls"]
    if any(urlparse(url).scheme != "https" or not urlparse(url).netloc for url in urls):
        raise ReviewError(f"{location}: evidence_urls 必须是 HTTPS URL")
    expected = f"github.com/{repo}".casefold()
    if not any(expected in url.casefold() for url in urls):
        raise ReviewError(f"{location}: evidence_urls 至少包含项目 GitHub 仓库")


def collect_reviews(reviews_dir: Path) -> dict[str, dict[str, Any]]:
    paths = sorted(reviews_dir.glob("*.yaml"))
    if not paths:
        raise ReviewError(f"{reviews_dir}: 没有审核文件")
    reviews: dict[str, dict[str, Any]] = {}
    for path in paths:
        for index, review in enumerate(load_yaml_list(path), start=1):
            location = f"{path}:{index}"
            validate_review(review, location)
            key = review["repo"].casefold()
            if key in reviews:
                raise ReviewError(f"{location}: 重复审核仓库 {review['repo']}")
            reviews[key] = review
    return reviews


def _assert_acceptable(project: dict[str, Any]) -> None:
    github = project.get("github")
    repo = project.get("repo", "<unknown>")
    if not isinstance(github, dict):
        raise ReviewError(f"{repo}: accepted 项目缺少 GitHub 元数据")
    if github.get("archived") is not False:
        raise ReviewError(f"{repo}: archived 未明确为 false，不能 accepted")
    if github.get("is_fork") is not False:
        raise ReviewError(f"{repo}: is_fork 未明确为 false，不能 accepted")
    if github.get("license_spdx") in UNSAFE_LICENSE_VALUES:
        raise ReviewError(f"{repo}: License 未能由单一 SPDX 值确认，不能 accepted")


def apply_reviews(
    projects: list[dict[str, Any]], review_map: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    project_keys = {
        project["repo"].casefold()
        for project in projects
        if isinstance(project.get("repo"), str)
    }
    missing = sorted(project_keys - review_map.keys())
    unknown = sorted(review_map.keys() - project_keys)
    if missing:
        raise ReviewError(f"缺少审核记录：{', '.join(missing)}")
    if unknown:
        raise ReviewError(f"审核文件包含未知仓库：{', '.join(unknown)}")

    result: list[dict[str, Any]] = []
    for original in projects:
        project = copy.deepcopy(original)
        review = review_map[project["repo"].casefold()]
        project["status"] = review["decision"]
        for field in (
            "suitable_for", "limitations", "review_notes", "evidence_urls", "reviewed_at"
        ):
            value = review[field]
            if isinstance(value, dt.date):
                value = value.isoformat()
            project[field] = copy.deepcopy(value)
        if project["status"] == "accepted":
            _assert_acceptable(project)
        result.append(project)
    return result


def render_projects(projects: list[dict[str, Any]]) -> str:
    return yaml.safe_dump(projects, allow_unicode=True, sort_keys=False, width=100)


def atomic_write(path: Path, content: str) -> None:
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = handle.name
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="验证审核已完整应用，不写文件")
    args = parser.parse_args()
    try:
        projects = load_yaml_list(PROJECTS)
        review_map = collect_reviews(REVIEWS_DIR)
        applied = apply_reviews(projects, review_map)
        rendered = render_projects(applied)
        if args.check:
            if PROJECTS.read_text(encoding="utf-8") != rendered:
                print("失败：审核结论尚未同步，请运行 `python3 scripts/apply_reviews.py`。", file=sys.stderr)
                return 1
            print(f"通过：{len(applied)} 个项目的审核结论已同步")
            return 0
        atomic_write(PROJECTS, rendered)
        counts = {
            decision: sum(p["status"] == decision for p in applied)
            for decision in sorted(DECISIONS)
        }
        summary = "，".join(f"{key}={value}" for key, value in counts.items())
        print(f"已应用 {len(applied)} 条审核：{summary}")
        return 0
    except (ReviewError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

