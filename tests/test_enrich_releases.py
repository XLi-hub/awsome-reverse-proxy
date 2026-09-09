from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "enrich_releases.py"
SPEC = importlib.util.spec_from_file_location("enrich_releases", SCRIPT)
assert SPEC and SPEC.loader
releases = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(releases)


class ReleaseTests(unittest.TestCase):
    def test_cache_round_trip_includes_fetch_time(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            old = releases.CACHE
            releases.CACHE = Path(directory)
            try:
                release = {"tag_name": "v1.2.3", "published_at": "2026-09-01T00:00:00Z"}
                releases.save_release("example/proxy", release, "2026-09-09T00:00:00Z")
                self.assertEqual(
                    releases.load_release("example/proxy"),
                    (release, "2026-09-09T00:00:00Z"),
                )
            finally:
                releases.CACHE = old

    def test_apply_release_records_snapshot(self) -> None:
        project = {"github": {}}
        releases.apply_release(
            project,
            {"tag_name": "v2", "published_at": "2026-09-01T00:00:00Z"},
            "2026-09-09T00:00:00Z",
        )
        self.assertEqual(project["github"]["latest_release"], "v2")
        self.assertEqual(project["github"]["release_fetched_at"], "2026-09-09T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
