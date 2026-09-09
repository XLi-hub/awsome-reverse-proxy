from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "enrich_github.py"
SPEC = importlib.util.spec_from_file_location("enrich_github", SCRIPT)
assert SPEC and SPEC.loader
enrich = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(enrich)


def repository(repo: str = "example/proxy") -> dict[str, object]:
    return {
        "full_name": repo,
        "html_url": f"https://github.com/{repo}",
        "description": "A reverse proxy",
        "stargazers_count": 123,
        "forks_count": 12,
        "language": "Go",
        "license": {"spdx_id": "Apache-2.0"},
        "archived": False,
        "fork": False,
        "pushed_at": "2026-09-08T10:11:12Z",
    }


class FakeResponse:
    def __init__(self, payload: object, headers: dict[str, str]) -> None:
        self.payload = json.dumps(payload).encode()
        self.headers = headers

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class FakeOpener:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.requests: list[object] = []

    def open(self, request: object, timeout: float) -> FakeResponse:
        self.requests.append(request)
        return self.responses.pop(0)


class PureFunctionTests(unittest.TestCase):
    def test_normalize_time_to_utc(self) -> None:
        self.assertEqual(
            enrich.normalize_github_time("2026-09-08T18:11:12+08:00"),
            "2026-09-08T10:11:12Z",
        )

    def test_build_metadata_has_documented_shape(self) -> None:
        result = enrich.build_github_metadata(
            repository(), "2026-09-08T12:00:00+00:00"
        )
        self.assertEqual(result["stars"], 123)
        self.assertEqual(result["license_spdx"], "Apache-2.0")
        self.assertEqual(result["fetched_at"], "2026-09-08T12:00:00Z")
        self.assertIsNone(result["latest_release"])

    def test_batches_stay_within_query_budget(self) -> None:
        repos = [f"owner/project-{index}" for index in range(12)]
        batches = enrich.repository_batches(repos, max_query_length=55)
        self.assertEqual([repo for batch in batches for repo in batch], repos)
        self.assertTrue(
            all(
                len(" ".join(f"repo:{repo}" for repo in batch)) <= 55
                for batch in batches
            )
        )

    def test_parse_rate_headers_is_case_insensitive(self) -> None:
        parsed = enrich.parse_rate_headers(
            {"X-RateLimit-Resource": "search", "x-ratelimit-remaining": "2"}
        )
        self.assertEqual(parsed["resource"], "search")
        self.assertEqual(parsed["remaining"], 2)

    def test_merge_preserves_existing_manual_fields_and_orphans(self) -> None:
        candidates = [{"repo": "example/proxy", "name": "Candidate", "status": "candidate"}]
        existing = [
            {
                "repo": "Example/Proxy",
                "name": "Reviewed name",
                "status": "accepted",
                "review_notes": "人工结论",
                "github": {"stars": 1},
            },
            {"repo": "other/proxy", "name": "Orphan", "status": "accepted"},
        ]
        merged = enrich.merge_project_sources(candidates, existing)
        self.assertEqual(merged[0]["name"], "Reviewed name")
        self.assertEqual(merged[0]["review_notes"], "人工结论")
        self.assertEqual(merged[1]["repo"], "other/proxy")

    def test_merge_drops_unreviewed_candidate_orphans(self) -> None:
        merged = enrich.merge_project_sources(
            [{"repo": "example/proxy", "status": "candidate"}],
            [
                {"repo": "example/proxy", "status": "candidate"},
                {"repo": "removed/proxy", "status": "candidate"},
            ],
        )
        self.assertEqual([item["repo"] for item in merged], ["example/proxy"])

    def test_merge_refreshes_unreviewed_fields_but_keeps_github(self) -> None:
        merged = enrich.merge_project_sources(
            [
                {
                    "repo": "example/proxy",
                    "name": "Updated candidate",
                    "status": "needs-review",
                }
            ],
            [
                {
                    "repo": "example/proxy",
                    "name": "Old candidate",
                    "status": "candidate",
                    "github": {"stars": 42},
                }
            ],
        )
        self.assertEqual(merged[0]["name"], "Updated candidate")
        self.assertEqual(merged[0]["status"], "needs-review")
        self.assertEqual(merged[0]["github"], {"stars": 42})


class NetworkAndCacheTests(unittest.TestCase):
    def test_search_uses_auth_without_exposing_it_in_url(self) -> None:
        opener = FakeOpener(
            [
                FakeResponse(
                    {"items": [repository()]},
                    {
                        "X-RateLimit-Resource": "search",
                        "X-RateLimit-Remaining": "9",
                    },
                )
            ]
        )
        client = enrich.GitHubClient("secret-token", opener=opener)
        items, _ = client.search_repositories(["example/proxy"])
        self.assertEqual(items[0]["full_name"], "example/proxy")
        request = opener.requests[0]
        self.assertNotIn("secret-token", request.full_url)
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-token")

    def test_search_miss_falls_back_to_repository_endpoint(self) -> None:
        opener = FakeOpener(
            [
                FakeResponse(
                    {"items": []},
                    {
                        "X-RateLimit-Resource": "search",
                        "X-RateLimit-Remaining": "9",
                    },
                ),
                FakeResponse(
                    repository(),
                    {
                        "X-RateLimit-Resource": "core",
                        "X-RateLimit-Remaining": "50",
                    },
                ),
            ]
        )
        client = enrich.GitHubClient(opener=opener)
        accepted: list[str] = []
        done, stopped, errors = enrich.fetch_uncached(
            ["example/proxy"],
            client,
            on_repository=lambda repo, data, fetched: accepted.append(repo),
        )
        self.assertEqual(done, {"example/proxy"})
        self.assertFalse(stopped)
        self.assertEqual(errors, [])
        self.assertEqual(len(opener.requests), 2)
        self.assertIn("/repos/example/proxy", opener.requests[1].full_url)

    def test_cache_avoids_network_and_replaces_only_github(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory)
            enrich.save_cache(
                cache_dir,
                "example/proxy",
                repository(),
                "2026-09-08T12:00:00Z",
            )
            projects = [
                {
                    "repo": "example/proxy",
                    "description_zh": "人工简介。",
                    "review_notes": "人工审核。",
                    "github": {"stars": 1},
                }
            ]
            opener = FakeOpener([])
            count, stopped, errors = enrich.enrich_projects(
                projects,
                ["example/proxy"],
                enrich.GitHubClient(opener=opener),
                cache_dir=cache_dir,
                refresh=False,
                write_cache=True,
            )
            self.assertEqual(count, 1)
            self.assertFalse(stopped)
            self.assertEqual(errors, [])
            self.assertEqual(projects[0]["description_zh"], "人工简介。")
            self.assertEqual(projects[0]["review_notes"], "人工审核。")
            self.assertEqual(projects[0]["github"]["stars"], 123)
            self.assertEqual(opener.requests, [])

    def test_low_core_quota_stops_before_next_repository(self) -> None:
        opener = FakeOpener(
            [
                FakeResponse(
                    {"items": []},
                    {
                        "X-RateLimit-Resource": "search",
                        "X-RateLimit-Remaining": "9",
                    },
                ),
                FakeResponse(
                    repository("one/proxy"),
                    {
                        "X-RateLimit-Resource": "core",
                        "X-RateLimit-Remaining": "5",
                    },
                ),
            ]
        )
        client = enrich.GitHubClient(opener=opener)
        accepted: list[str] = []
        done, stopped, _ = enrich.fetch_uncached(
            ["one/proxy", "two/proxy"],
            client,
            on_repository=lambda repo, data, fetched: accepted.append(repo),
        )
        self.assertEqual(done, {"one/proxy"})
        self.assertTrue(stopped)
        self.assertEqual(accepted, ["one/proxy"])
        self.assertEqual(len(opener.requests), 2)

    def test_atomic_write_leaves_complete_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "projects.yaml"
            enrich.atomic_write_text(target, "- repo: example/proxy\n")
            self.assertEqual(target.read_text(), "- repo: example/proxy\n")
            self.assertEqual(list(target.parent.glob(".projects.yaml.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
