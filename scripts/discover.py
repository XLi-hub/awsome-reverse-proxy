#!/usr/bin/env python3
"""Discover GitHub repositories into a staging file without auto-admitting them."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from enrich_github import API_ROOT, EnrichmentError, GitHubClient, atomic_write_text, load_yaml_list


ROOT = SCRIPT_DIR.parent
QUERIES = ROOT / "data" / "discovery-queries.yaml"
DISCOVERED = ROOT / "data" / "discovered.yaml"
CANDIDATES = ROOT / "data" / "candidates.yaml"
REJECTED = ROOT / "data" / "rejected.yaml"

MIN_RELEVANCE_SCORE = 3
RELEVANT_TOPICS = {
    "api-gateway",
    "edge-proxy",
    "gateway-api",
    "identity-aware-proxy",
    "ingress-controller",
    "load-balancer",
    "proxy-manager",
    "reverse-proxy",
    "reverse-tunnel",
    "service-mesh",
    "tcp-proxy",
    "zero-trust-access",
}
RELEVANT_PHRASES = {
    "api gateway",
    "edge proxy",
    "gateway api",
    "identity aware proxy",
    "ingress controller",
    "load balancer",
    "proxy manager",
    "reverse proxy",
    "reverse tunnel",
    "service mesh gateway",
    "tcp proxy",
    "zero trust access",
}
NOISE_TOPICS = {"awesome", "awesome-list", "curated-list"}
NOISE_NAME_PARTS = {"awesome", "examples", "guide", "handbook", "learning", "tutorial"}


def load_queries(path: Path) -> list[str]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload or any(not isinstance(q, str) or not q for q in payload):
        raise ValueError(f"{path}: 必须是非空查询字符串数组")
    return payload


def relevance(repo: dict[str, Any]) -> tuple[int, list[str]]:
    """Score only scope relevance, never project quality."""
    topics = {
        str(topic).strip().casefold().replace("_", "-")
        for topic in repo.get("topics", [])
        if isinstance(topic, str)
    }
    topic_hits = sorted(topics & RELEVANT_TOPICS)
    signals = [f"topic:{topic}" for topic in topic_hits]
    score = min(6, 3 * len(topic_hits))

    full_name = str(repo.get("full_name") or repo.get("repo") or "")
    name = str(repo.get("name") or full_name.rsplit("/", 1)[-1])
    description = str(repo.get("description") or "")
    searchable = f"{name} {description}".casefold().replace("-", " ").replace("_", " ")
    phrase_hits = sorted(phrase for phrase in RELEVANT_PHRASES if phrase in searchable)
    if phrase_hits:
        score += min(6, 3 * len(phrase_hits))
        signals.extend(f"metadata:{phrase}" for phrase in phrase_hits)

    noise = sorted(topics & NOISE_TOPICS)
    name_tokens = set(name.casefold().replace("-", " ").replace("_", " ").split())
    noise.extend(f"name:{part}" for part in sorted(name_tokens & NOISE_NAME_PARTS))
    if noise:
        score -= 4
        signals.extend(f"penalty:{item}" for item in noise)
    return max(0, score), signals


def make_entry(repo: dict[str, Any], query: str, discovered_at: str) -> dict[str, Any] | None:
    full_name = repo.get("full_name")
    if not isinstance(full_name, str) or full_name.count("/") != 1:
        return None
    relevance_score, matched_signals = relevance(repo)
    if relevance_score < MIN_RELEVANCE_SCORE:
        return None
    return {
        "repo": full_name,
        "name": repo.get("name") or full_name.split("/", 1)[1],
        "description": repo.get("description"),
        "stars_at_discovery": repo.get("stargazers_count"),
        "language": repo.get("language"),
        "license_spdx": (repo.get("license") or {}).get("spdx_id") if isinstance(repo.get("license"), dict) else None,
        "topics": repo.get("topics") if isinstance(repo.get("topics"), list) else [],
        "found_by": [query],
        "relevance_score": relevance_score,
        "matched_signals": matched_signals,
        "discovered_at": discovered_at,
        "triage_status": "unreviewed",
    }


def merge_entries(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Unreviewed rows are a replaceable search snapshot. Human-triaged rows survive
    # result-window changes, so a monthly refresh cannot silently discard decisions.
    merged = {
        item["repo"].casefold(): dict(item)
        for item in existing
        if isinstance(item.get("repo"), str) and item.get("triage_status", "unreviewed") != "unreviewed"
    }
    for item in incoming:
        key = item["repo"].casefold()
        if key in merged:
            queries = list(dict.fromkeys([*merged[key].get("found_by", []), *item["found_by"]]))
            previous_status = merged[key].get("triage_status", "unreviewed")
            merged[key].update(item)
            merged[key]["found_by"] = queries
            merged[key]["triage_status"] = previous_status
        else:
            merged[key] = item
    return sorted(merged.values(), key=lambda item: (-int(item.get("stars_at_discovery") or 0), item["repo"].casefold()))


def refilter_entries(existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in existing:
        repo = item.get("repo")
        if not isinstance(repo, str) or repo.count("/") != 1:
            raise ValueError("data/discovered.yaml: repo 必须是 owner/name")
        key = repo.casefold()
        if key in seen:
            raise ValueError(f"data/discovered.yaml: 重复仓库 {repo}")
        seen.add(key)
        score, signals = relevance(item)
        if score < MIN_RELEVANCE_SCORE and item.get("triage_status", "unreviewed") == "unreviewed":
            continue
        updated = dict(item)
        updated["relevance_score"] = score
        updated["matched_signals"] = signals
        result.append(updated)
    return sorted(result, key=lambda item: (-int(item.get("stars_at_discovery") or 0), item["repo"].casefold()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-query", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--refilter-only",
        action="store_true",
        help="仅按当前规则重筛已有暂存数据，不请求 GitHub",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="检查暂存数据是否符合当前规则，不请求 GitHub 或写文件",
    )
    args = parser.parse_args()
    if not 1 <= args.per_query <= 100:
        print("错误：--per-query 必须在 1..100", file=sys.stderr)
        return 1
    try:
        known = {x["repo"].casefold() for x in load_yaml_list(CANDIDATES)}
        known |= {x["repo"].casefold() for x in load_yaml_list(REJECTED)}
        loaded = load_yaml_list(DISCOVERED)
        existing = [
            x
            for x in loaded
            if not isinstance(x.get("repo"), str) or x["repo"].casefold() not in known
        ]
        if args.refilter_only or args.check:
            result = refilter_entries(existing)
            rendered = yaml.safe_dump(result, allow_unicode=True, sort_keys=False, width=100)
            if args.check:
                if rendered != DISCOVERED.read_text(encoding="utf-8"):
                    print(
                        "失败：data/discovered.yaml 与当前发现规则或已知项目集合不一致，请运行 "
                        "`python3 scripts/discover.py --refilter-only`。",
                        file=sys.stderr,
                    )
                    return 1
                print(f"通过：发现暂存区已同步（{len(result)} 个仓库）")
                return 0
            if not args.dry_run:
                atomic_write_text(DISCOVERED, rendered)
            print(f"发现暂存：按当前相关性规则保留 {len(result)}/{len(existing)} 个仓库")
            return 0
        client = GitHubClient(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
        stamp = dt.datetime.now(dt.timezone.utc).date().isoformat()
        incoming: list[dict[str, Any]] = []
        for query in load_queries(QUERIES):
            params = urllib.parse.urlencode({"q": query, "sort": "stars", "order": "desc", "per_page": args.per_query})
            payload, _ = client._request(f"{API_ROOT}/search/repositories?{params}")
            for raw in payload.get("items", []):
                entry = make_entry(raw, query, stamp)
                if entry and entry["repo"].casefold() not in known:
                    incoming.append(entry)
        result = merge_entries(existing, incoming)
        if not args.dry_run:
            atomic_write_text(DISCOVERED, yaml.safe_dump(result, allow_unicode=True, sort_keys=False, width=100))
        print(f"发现暂存：新增命中 {len(incoming)} 条，去重后共 {len(result)} 个待分流仓库")
        return 0
    except (EnrichmentError, OSError, ValueError, KeyError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
