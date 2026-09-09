#!/usr/bin/env python3
"""Enrich catalog candidates with metadata from the GitHub REST API.

The script uses repository search to fetch small batches efficiently, stores every
successful result in a per-repository cache, and falls back to the repository
endpoint for search misses. Existing project fields are preserved; only the
``github`` object is replaced.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import yaml


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates.yaml"
PROJECTS = ROOT / "data" / "projects.yaml"
CACHE_DIR = ROOT / ".cache" / "github" / "repos"
API_ROOT = "https://api.github.com"

# GitHub documents a 256-character search-query limit. Leaving some headroom
# makes the batching rule robust if GitHub changes how it counts whitespace.
MAX_SEARCH_QUERY_LENGTH = 230
SEARCH_RATE_FLOOR = 1
CORE_RATE_FLOOR = 5


class EnrichmentError(Exception):
    """A human-readable enrichment failure."""


class APIError(EnrichmentError):
    """An HTTP or response-shape error from GitHub."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        resource: str | None = None,
        remaining: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.resource = resource
        self.remaining = remaining


def utc_now() -> str:
    """Return a seconds-precision ISO 8601 timestamp in UTC."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def normalize_github_time(value: Any) -> str | None:
    """Normalize a GitHub timestamp to seconds-precision UTC ISO 8601."""

    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise EnrichmentError(f"GitHub 返回了无效时间：{value!r}") from exc
    if parsed.tzinfo is None:
        raise EnrichmentError(f"GitHub 时间缺少时区：{value!r}")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def parse_rate_headers(headers: Mapping[str, str]) -> dict[str, Any]:
    """Extract normalized rate-limit values from case-insensitive HTTP headers."""

    lowered = {str(key).lower(): value for key, value in headers.items()}
    remaining_text = lowered.get("x-ratelimit-remaining")
    try:
        remaining = int(remaining_text) if remaining_text is not None else None
    except (TypeError, ValueError):
        remaining = None
    return {
        "resource": lowered.get("x-ratelimit-resource"),
        "remaining": remaining,
        "reset": lowered.get("x-ratelimit-reset"),
    }


def repository_batches(
    repos: Iterable[str], max_query_length: int = MAX_SEARCH_QUERY_LENGTH
) -> list[list[str]]:
    """Group repository names without exceeding GitHub's query-length budget."""

    if max_query_length < len("repo:a/b"):
        raise ValueError("max_query_length 太小，无法容纳仓库限定符")
    batches: list[list[str]] = []
    current: list[str] = []
    current_length = 0
    for repo in repos:
        qualifier = f"repo:{repo}"
        extra = len(qualifier) + (1 if current else 0)
        if current and current_length + extra > max_query_length:
            batches.append(current)
            current = []
            current_length = 0
            extra = len(qualifier)
        if len(qualifier) > max_query_length:
            raise ValueError(f"仓库名过长，无法构建搜索查询：{repo}")
        current.append(repo)
        current_length += extra
    if current:
        batches.append(current)
    return batches


def build_github_metadata(repository: Mapping[str, Any], fetched_at: str) -> dict[str, Any]:
    """Convert a GitHub repository response into the catalog's automatic fields."""

    license_info = repository.get("license")
    spdx = license_info.get("spdx_id") if isinstance(license_info, Mapping) else None
    if not isinstance(spdx, str) or not spdx.strip():
        spdx = None

    def integer(field: str) -> int | None:
        value = repository.get(field)
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    def text(field: str) -> str | None:
        value = repository.get(field)
        return value if isinstance(value, str) and value.strip() else None

    return {
        "url": text("html_url"),
        "description": text("description"),
        "stars": integer("stargazers_count"),
        "forks": integer("forks_count"),
        "language": text("language"),
        "license_spdx": spdx,
        "archived": repository.get("archived")
        if isinstance(repository.get("archived"), bool)
        else None,
        "is_fork": repository.get("fork")
        if isinstance(repository.get("fork"), bool)
        else None,
        "pushed_at": normalize_github_time(repository.get("pushed_at")),
        # Release requests are intentionally omitted: one request per repository
        # would consume substantially more quota. A later release-specific pass
        # can replace these nulls without changing the schema.
        "latest_release": None,
        "latest_release_at": None,
        "fetched_at": normalize_github_time(fetched_at),
    }


def merge_project_sources(
    candidates: list[dict[str, Any]], existing: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Seed projects from candidates while preserving all existing manual fields."""

    existing_by_repo: dict[str, dict[str, Any]] = {}
    for item in existing:
        repo = item.get("repo")
        if isinstance(repo, str):
            existing_by_repo[repo.casefold()] = item

    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        repo = candidate.get("repo")
        if not isinstance(repo, str):
            raise EnrichmentError("候选项目缺少 repo 字段")
        key = repo.casefold()
        previous = existing_by_repo.get(key)
        if previous is not None and previous.get("status") in {"accepted", "historical"}:
            source = previous
        else:
            # inbox remains the source of truth until a project is formally
            # reviewed. Preserve only the expensive automatic metadata cache.
            source = candidate
            if previous is not None and isinstance(previous.get("github"), dict):
                source = copy.deepcopy(candidate)
                source["github"] = copy.deepcopy(previous["github"])
        merged.append(copy.deepcopy(source))
        seen.add(key)

    # Never silently delete a formally reviewed project just because it no longer
    # occurs in the generated candidate pool. Unreviewed candidate orphans are
    # intentionally dropped after they move to data/rejected.yaml.
    orphans = [
        copy.deepcopy(item)
        for item in existing
        if isinstance(item.get("repo"), str)
        and item["repo"].casefold() not in seen
        and item.get("status") in {"accepted", "historical"}
    ]
    orphans.sort(key=lambda item: item["repo"].casefold())
    merged.extend(orphans)
    return merged


def load_yaml_list(path: Path) -> list[dict[str, Any]]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise EnrichmentError(f"{path}: YAML 解析失败：{exc}") from exc
    if payload is None:
        return []
    if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
        raise EnrichmentError(f"{path}: 顶层必须是对象数组")
    return payload


def render_projects(projects: list[dict[str, Any]]) -> str:
    return yaml.safe_dump(projects, allow_unicode=True, sort_keys=False, width=100)


def atomic_write_text(path: Path, content: str) -> None:
    """Replace a UTF-8 text file atomically using a sibling temporary file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def cache_path(cache_dir: Path, repo: str) -> Path:
    owner, name = repo.split("/", 1)
    return cache_dir / urllib.parse.quote(owner, safe="") / (
        urllib.parse.quote(name, safe="") + ".json"
    )


def load_cache(cache_dir: Path, repo: str) -> tuple[dict[str, Any], str] | None:
    path = cache_path(cache_dir, repo)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None
    repository = payload.get("repository")
    fetched_at = payload.get("fetched_at")
    if not isinstance(repository, dict) or not isinstance(fetched_at, str):
        return None
    try:
        normalized = normalize_github_time(fetched_at)
    except EnrichmentError:
        return None
    if normalized is None:
        return None
    return repository, normalized


def save_cache(
    cache_dir: Path, repo: str, repository: Mapping[str, Any], fetched_at: str
) -> None:
    path = cache_path(cache_dir, repo)
    content = json.dumps(
        {"fetched_at": fetched_at, "repository": repository},
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    atomic_write_text(path, content)


class GitHubClient:
    """Minimal GitHub REST client with separately tracked rate-limit resources."""

    def __init__(
        self,
        token: str | None = None,
        *,
        opener: Any = None,
        timeout: float = 20.0,
    ) -> None:
        self.token = token
        self.opener = opener if opener is not None else urllib.request.build_opener()
        self.timeout = timeout
        self.rates: dict[str, int] = {}

    def _request(self, url: str) -> tuple[Any, dict[str, Any]]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "awesome-reverse-proxy-catalog",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, headers=headers)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read()
                rate = parse_rate_headers(response.headers)
        except urllib.error.HTTPError as exc:
            rate = parse_rate_headers(exc.headers or {})
            resource = rate["resource"]
            remaining = rate["remaining"]
            if resource and remaining is not None:
                self.rates[resource] = remaining
            message = "GitHub API 请求失败"
            try:
                body = json.loads(exc.read().decode("utf-8"))
                if isinstance(body, dict) and isinstance(body.get("message"), str):
                    message = body["message"]
            except (UnicodeDecodeError, json.JSONDecodeError, OSError):
                pass
            raise APIError(
                f"GitHub API HTTP {exc.code}: {message}",
                status=exc.code,
                resource=resource,
                remaining=remaining,
            ) from exc
        except urllib.error.URLError as exc:
            raise APIError(f"无法连接 GitHub API：{exc.reason}") from exc

        resource = rate["resource"]
        remaining = rate["remaining"]
        if resource and remaining is not None:
            self.rates[resource] = remaining
        try:
            return json.loads(raw.decode("utf-8")), rate
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise APIError("GitHub API 返回了无效 JSON") from exc

    def search_repositories(self, repos: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        query = " ".join(f"repo:{repo}" for repo in repos)
        parameters = urllib.parse.urlencode({"q": query, "per_page": 100})
        payload, rate = self._request(f"{API_ROOT}/search/repositories?{parameters}")
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            raise APIError("GitHub 仓库搜索返回了意外结构")
        items = [item for item in payload["items"] if isinstance(item, dict)]
        return items, rate

    def get_repository(self, repo: str) -> tuple[dict[str, Any], dict[str, Any]]:
        owner, name = repo.split("/", 1)
        encoded = "/".join(
            (urllib.parse.quote(owner, safe=""), urllib.parse.quote(name, safe=""))
        )
        payload, rate = self._request(f"{API_ROOT}/repos/{encoded}")
        if not isinstance(payload, dict):
            raise APIError(f"{repo}: GitHub 仓库接口返回了意外结构")
        return payload, rate


def rate_is_low(rate: Mapping[str, Any]) -> bool:
    remaining = rate.get("remaining")
    resource = rate.get("resource")
    if not isinstance(remaining, int):
        return False
    floor = SEARCH_RATE_FLOOR if resource == "search" else CORE_RATE_FLOOR
    return remaining <= floor


def _index_search_results(
    requested: list[str], items: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    requested_keys = {repo.casefold() for repo in requested}
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        full_name = item.get("full_name")
        if isinstance(full_name, str) and full_name.casefold() in requested_keys:
            indexed[full_name.casefold()] = item
    return indexed


def fetch_uncached(
    repos: list[str],
    client: GitHubClient,
    *,
    on_repository: Callable[[str, dict[str, Any], str], None],
) -> tuple[set[str], bool, list[str]]:
    """Fetch repositories, returning completed keys, stopped flag, and errors."""

    completed: set[str] = set()
    errors: list[str] = []
    core_low = False
    search_low = False

    for batch in repository_batches(repos):
        if core_low:
            break
        indexed: dict[str, dict[str, Any]] = {}
        if not search_low:
            try:
                items, rate = client.search_repositories(batch)
                indexed = _index_search_results(batch, items)
                search_low = rate_is_low(rate)
            except APIError as exc:
                # Search and core use independent rate-limit buckets. A depleted
                # search bucket should therefore fall back to repository requests.
                if exc.resource == "search" and exc.remaining is not None:
                    search_low = exc.remaining <= SEARCH_RATE_FLOOR
                else:
                    errors.append(str(exc))

        missing: list[str] = []
        fetched_at = utc_now()
        for repo in batch:
            repository = indexed.get(repo.casefold())
            if repository is None:
                missing.append(repo)
                continue
            on_repository(repo, repository, fetched_at)
            completed.add(repo.casefold())

        for repo in missing:
            if core_low:
                break
            try:
                repository, rate = client.get_repository(repo)
            except APIError as exc:
                errors.append(f"{repo}: {exc}")
                if exc.resource == "core" and exc.remaining is not None:
                    core_low = exc.remaining <= CORE_RATE_FLOOR
                continue
            fetched_at = utc_now()
            on_repository(repo, repository, fetched_at)
            completed.add(repo.casefold())
            core_low = rate_is_low(rate)

    stopped = core_low or len(completed) < len(repos)
    return completed, stopped, errors


def enrich_projects(
    projects: list[dict[str, Any]],
    selected_repos: list[str],
    client: GitHubClient,
    *,
    cache_dir: Path,
    refresh: bool,
    write_cache: bool,
) -> tuple[int, bool, list[str]]:
    """Replace GitHub fields for selected projects using cache and the REST API."""

    by_repo = {
        item["repo"].casefold(): item
        for item in projects
        if isinstance(item.get("repo"), str)
    }
    uncached: list[str] = []
    enriched = 0

    for repo in selected_repos:
        cached = None if refresh else load_cache(cache_dir, repo)
        if cached is None:
            uncached.append(repo)
            continue
        repository, fetched_at = cached
        by_repo[repo.casefold()]["github"] = build_github_metadata(
            repository, fetched_at
        )
        enriched += 1

    def accept(repo: str, repository: dict[str, Any], fetched_at: str) -> None:
        nonlocal enriched
        by_repo[repo.casefold()]["github"] = build_github_metadata(
            repository, fetched_at
        )
        if write_cache:
            save_cache(cache_dir, repo, repository, fetched_at)
        enriched += 1

    _, stopped, errors = fetch_uncached(uncached, client, on_repository=accept)
    return enriched, stopped, errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit", type=int, help="只处理排序后的前 N 个项目（用于试运行）"
    )
    parser.add_argument(
        "--refresh", action="store_true", help="忽略现有缓存并重新请求 GitHub"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="执行抓取但不写缓存或 projects.yaml"
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.limit is not None and args.limit < 1:
        print("错误：--limit 必须是正整数", file=sys.stderr)
        return 1

    try:
        candidates = load_yaml_list(CANDIDATES)
        existing = load_yaml_list(PROJECTS) if PROJECTS.exists() else []
        projects = merge_project_sources(candidates, existing)
        selected = [item["repo"] for item in projects]
        if args.limit is not None:
            selected = selected[: args.limit]

        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        client = GitHubClient(token)
        enriched, stopped, errors = enrich_projects(
            projects,
            selected,
            client,
            cache_dir=CACHE_DIR,
            refresh=args.refresh,
            write_cache=not args.dry_run,
        )

        if not args.dry_run:
            atomic_write_text(PROJECTS, render_projects(projects))

        mode = "试运行" if args.dry_run else "已写入 data/projects.yaml"
        print(f"{mode}：补全 {enriched}/{len(selected)} 个项目")
        for error in errors:
            print(f"警告：{error}", file=sys.stderr)
        if stopped:
            print("已安全停止：API 配额不足或部分请求失败，可稍后断点续跑。", file=sys.stderr)
            return 2
        return 0
    except (EnrichmentError, OSError, ValueError, KeyError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
