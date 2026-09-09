from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "apply_reviews.py"
SPEC = importlib.util.spec_from_file_location("apply_reviews", SCRIPT)
assert SPEC and SPEC.loader
reviews = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviews)


def project(repo: str = "example/proxy", license_spdx: str = "MIT") -> dict:
    return {
        "repo": repo,
        "name": "Proxy",
        "status": "candidate",
        "github": {"archived": False, "is_fork": False, "license_spdx": license_spdx},
    }


def review(repo: str = "example/proxy", decision: str = "accepted") -> dict:
    return {
        "repo": repo,
        "decision": decision,
        "suitable_for": ["自托管服务入口"],
        "limitations": [],
        "review_notes": "已核对上游 README 和许可证。",
        "evidence_urls": [f"https://github.com/{repo}"],
        "reviewed_at": "2026-09-08",
    }


class ApplyReviewTests(unittest.TestCase):
    def test_accepts_complete_review(self) -> None:
        item = review()
        reviews.validate_review(item, "fixture:1")
        result = reviews.apply_reviews([project()], {"example/proxy": item})
        self.assertEqual(result[0]["status"], "accepted")
        self.assertEqual(result[0]["reviewed_at"], "2026-09-08")

    def test_rejects_incomplete_coverage(self) -> None:
        with self.assertRaisesRegex(reviews.ReviewError, "缺少审核记录"):
            reviews.apply_reviews([project()], {})

    def test_does_not_accept_ambiguous_license(self) -> None:
        with self.assertRaisesRegex(reviews.ReviewError, "License"):
            reviews.apply_reviews(
                [project(license_spdx="NOASSERTION")],
                {"example/proxy": review()},
            )

    def test_needs_review_can_keep_ambiguous_license(self) -> None:
        result = reviews.apply_reviews(
            [project(license_spdx="NOASSERTION")],
            {"example/proxy": review(decision="needs-review")},
        )
        self.assertEqual(result[0]["status"], "needs-review")


if __name__ == "__main__":
    unittest.main()
