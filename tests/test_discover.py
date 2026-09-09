from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "discover.py"
SPEC = importlib.util.spec_from_file_location("discover", SCRIPT)
assert SPEC and SPEC.loader
discover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discover)


class DiscoveryTests(unittest.TestCase):
    def test_invalid_repository_is_ignored(self) -> None:
        self.assertIsNone(discover.make_entry({}, "query", "2026-09-09"))

    def test_irrelevant_readme_match_is_ignored(self) -> None:
        repo = {
            "full_name": "example/awesome-list",
            "name": "awesome-list",
            "description": "A curated list of self-hosted software",
            "topics": ["awesome-list"],
        }
        self.assertIsNone(discover.make_entry(repo, '"proxy manager" in:readme', "2026-09-09"))

    def test_relevant_topic_records_explainable_signal(self) -> None:
        repo = {
            "full_name": "example/edge",
            "name": "edge",
            "description": "Traffic entry point",
            "topics": ["reverse-proxy"],
        }
        result = discover.make_entry(repo, "topic:reverse-proxy", "2026-09-09")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["relevance_score"], 3)
        self.assertEqual(result["matched_signals"], ["topic:reverse-proxy"])

    def test_merge_preserves_triage_and_combines_queries(self) -> None:
        old = [{"repo": "A/Proxy", "stars_at_discovery": 1, "found_by": ["q1"], "triage_status": "keep"}]
        new = [{"repo": "a/proxy", "stars_at_discovery": 2, "found_by": ["q2"], "triage_status": "unreviewed"}]
        result = discover.merge_entries(old, new)
        self.assertEqual(result[0]["found_by"], ["q1", "q2"])
        self.assertEqual(result[0]["triage_status"], "keep")

    def test_merge_drops_stale_unreviewed_results(self) -> None:
        old = [{"repo": "A/Old", "stars_at_discovery": 1, "triage_status": "unreviewed"}]
        self.assertEqual(discover.merge_entries(old, []), [])

    def test_refilter_preserves_human_triage_below_threshold(self) -> None:
        old = [{"repo": "A/Reviewed", "name": "misc", "triage_status": "rejected"}]
        result = discover.refilter_entries(old)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["relevance_score"], 0)

    def test_refilter_rejects_case_insensitive_duplicates(self) -> None:
        old = [{"repo": "A/Proxy"}, {"repo": "a/proxy"}]
        with self.assertRaisesRegex(ValueError, "重复仓库"):
            discover.refilter_entries(old)


if __name__ == "__main__":
    unittest.main()
