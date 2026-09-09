from __future__ import annotations

import datetime as dt
import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "score_projects.py"
SPEC = importlib.util.spec_from_file_location("score_projects", SCRIPT)
assert SPEC and SPEC.loader
score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score)


class ScoreTests(unittest.TestCase):
    def test_score_is_bounded_and_versioned(self) -> None:
        project = {
            "status": "accepted", "reviewed_at": "2026-09-09", "review_notes": "ok",
            "suitable_for": ["web"], "evidence_urls": ["https://github.com/a/b"],
            "source_queries": ["repo:a/b"],
            "github": {"stars": 100000, "forks": 10000, "license_spdx": "MIT",
                       "pushed_at": "2026-09-08T00:00:00Z", "latest_release_at": "2026-09-01T00:00:00Z"},
        }
        result = score.calculate_score(project, dt.date(2026, 9, 9))
        self.assertEqual(result["total"], 100)
        self.assertEqual(result["version"], "signal-v1")

    def test_unreviewed_projects_do_not_keep_score(self) -> None:
        items = [{"status": "needs-review", "score": {"total": 99}}]
        score.score_projects(items, dt.date(2026, 9, 9))
        self.assertNotIn("score", items[0])


if __name__ == "__main__":
    unittest.main()
