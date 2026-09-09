#!/usr/bin/env python3
"""Calculate a transparent, versioned signal score for accepted projects."""

from __future__ import annotations

import argparse
import datetime as dt
import math
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from enrich_github import PROJECTS, atomic_write_text, load_yaml_list, render_projects


VERSION = "signal-v1"


def parse_time(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(dt.timezone.utc) if parsed.tzinfo else None


def freshness_points(age_days: int, maximum: float, *, no_signal: float = 0) -> float:
    if age_days < 0:
        return maximum
    for days, ratio in ((30, 1), (90, .85), (180, .7), (365, .5), (730, .25)):
        if age_days <= days:
            return maximum * ratio
    return no_signal


def log_points(value: Any, maximum: float, ceiling_power: float) -> float:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return 0
    return maximum * min(math.log10(value + 1) / ceiling_power, 1)


def calculate_score(project: dict[str, Any], as_of: dt.date) -> dict[str, Any]:
    github = project.get("github") if isinstance(project.get("github"), dict) else {}
    stars = log_points(github.get("stars"), 22, 5)
    forks = log_points(github.get("forks"), 8, 4)
    community = stars + forks

    pushed = parse_time(github.get("pushed_at"))
    pushed_age = (as_of - pushed.date()).days if pushed else 10_000
    push_score = freshness_points(pushed_age, 20)
    released = parse_time(github.get("latest_release_at"))
    release_age = (as_of - released.date()).days if released else 10_000
    release_score = freshness_points(release_age, 15, no_signal=5 if released is None else 0)
    maintenance = push_score + release_score

    license_score = 10 if github.get("license_spdx") not in (None, "", "NOASSERTION", "OTHER") else 0
    review_score = 15 if all(project.get(k) for k in ("reviewed_at", "review_notes", "suitable_for")) else 0
    trace_score = 10 if project.get("evidence_urls") and project.get("source_queries") else 0
    evidence = license_score + review_score + trace_score

    return {
        "version": VERSION,
        "total": round(community + maintenance + evidence, 1),
        "community": round(community, 1),
        "maintenance": round(maintenance, 1),
        "evidence": round(evidence, 1),
        "as_of": as_of.isoformat(),
    }


def score_projects(projects: list[dict[str, Any]], as_of: dt.date) -> list[dict[str, Any]]:
    for project in projects:
        if project.get("status") == "accepted":
            project["score"] = calculate_score(project, as_of)
        else:
            project.pop("score", None)
    return projects


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", type=dt.date.fromisoformat)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        projects = load_yaml_list(PROJECTS)
        if args.check:
            dates = {p.get("score", {}).get("as_of") for p in projects if p.get("status") == "accepted"}
            if len(dates) != 1 or None in dates:
                print("失败：正式项目缺少统一评分日期。", file=sys.stderr)
                return 1
            as_of = dt.date.fromisoformat(dates.pop())
        else:
            as_of = args.as_of or dt.datetime.now(dt.timezone.utc).date()
        rendered = render_projects(score_projects(projects, as_of))
        if args.check:
            if PROJECTS.read_text(encoding="utf-8") != rendered:
                print("失败：评分已过期，请运行 `python3 scripts/score_projects.py`。", file=sys.stderr)
                return 1
            print(f"通过：评分已同步（{VERSION}，{as_of}）")
            return 0
        atomic_write_text(PROJECTS, rendered)
        print(f"已评分：{sum(p.get('status') == 'accepted' for p in projects)} 个项目（{VERSION}）")
        return 0
    except (OSError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
