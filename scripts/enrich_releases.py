#!/usr/bin/env python3
"""Add latest GitHub Release metadata to reviewed catalog projects."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path

from enrich_github import (
    API_ROOT,
    APIError,
    GitHubClient,
    PROJECTS,
    atomic_write_text,
    load_yaml_list,
    normalize_github_time,
    render_projects,
    utc_now,
)


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "github" / "releases"


def release_cache_path(repo: str) -> Path:
    owner, name = repo.split("/", 1)
    return CACHE / urllib.parse.quote(owner, safe="") / (urllib.parse.quote(name, safe="") + ".json")


def load_release(repo: str) -> tuple[dict | None, str] | object:
    path = release_cache_path(repo)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return MISSING
    if not isinstance(payload, dict) or "release" not in payload or not isinstance(payload.get("fetched_at"), str):
        return MISSING
    value = payload["release"]
    return (value, payload["fetched_at"]) if isinstance(value, dict) or value is None else MISSING


def save_release(repo: str, release: dict | None, fetched_at: str) -> None:
    content = json.dumps(
        {"fetched_at": fetched_at, "release": release}, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    atomic_write_text(release_cache_path(repo), content)


def apply_release(project: dict, release: dict | None, fetched_at: str | None = None) -> None:
    github = project.setdefault("github", {})
    github["latest_release"] = release.get("tag_name") if release else None
    github["latest_release_at"] = (
        normalize_github_time(release.get("published_at")) if release else None
    )
    github["release_fetched_at"] = fetched_at or utc_now()


MISSING = object()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--all-statuses", action="store_true")
    args = parser.parse_args()
    try:
        projects = load_yaml_list(PROJECTS)
        selected = [p for p in projects if args.all_statuses or p.get("status") == "accepted"]
        if args.limit is not None:
            if args.limit < 1:
                raise ValueError("--limit 必须是正整数")
            selected = selected[: args.limit]
        client = GitHubClient(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
        completed = 0
        for project in selected:
            repo = project["repo"]
            cached = MISSING if args.refresh else load_release(repo)
            if cached is MISSING:
                encoded = "/".join(urllib.parse.quote(part, safe="") for part in repo.split("/", 1))
                rate = {}
                try:
                    payload, rate = client._request(f"{API_ROOT}/repos/{encoded}/releases/latest")
                    release = payload if isinstance(payload, dict) else None
                except APIError as exc:
                    if exc.status == 404:
                        release = None
                    else:
                        print(f"警告：{repo}: {exc}", file=sys.stderr)
                        break
                fetched_at = utc_now()
                save_release(repo, release, fetched_at)
                if isinstance(rate.get("remaining"), int) and rate["remaining"] <= 2:
                    apply_release(project, release, fetched_at)
                    completed += 1
                    break
            else:
                release, fetched_at = cached
            apply_release(project, release, fetched_at)
            completed += 1
        atomic_write_text(PROJECTS, render_projects(projects))
        print(f"Release 补全：{completed}/{len(selected)}")
        return 0 if completed == len(selected) else 2
    except (OSError, ValueError, KeyError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
