from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "catalog.py"
SPEC = importlib.util.spec_from_file_location("catalog", SCRIPT)
assert SPEC and SPEC.loader
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)


class CatalogValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.item = {
            "repo": "example/proxy",
            "name": "Example Proxy",
            "category": "general-reverse-proxy",
            "description_zh": "一个用于测试的反向代理。",
            "tags": ["http", "tls"],
            "why_candidate": "覆盖基础反向代理能力。",
            "source_queries": ["topic:reverse-proxy"],
            "status": "candidate",
        }

    def test_valid_candidate(self) -> None:
        catalog.validate_item(self.item, "fixture:1")

    def test_invalid_repo(self) -> None:
        self.item["repo"] = "https://github.com/example/proxy"
        with self.assertRaisesRegex(catalog.CatalogError, "owner/name"):
            catalog.validate_item(self.item, "fixture:1")

    def test_unknown_category(self) -> None:
        self.item["category"] = "forward-proxy"
        with self.assertRaisesRegex(catalog.CatalogError, "未知分类"):
            catalog.validate_item(self.item, "fixture:1")

    def test_duplicate_tag(self) -> None:
        self.item["tags"] = ["http", "http"]
        with self.assertRaisesRegex(catalog.CatalogError, "重复值"):
            catalog.validate_item(self.item, "fixture:1")

    def test_needs_review_candidate(self) -> None:
        self.item["status"] = "needs-review"
        catalog.validate_item(self.item, "fixture:1")

    def test_accepted_is_not_an_inbox_status(self) -> None:
        self.item["status"] = "accepted"
        with self.assertRaisesRegex(catalog.CatalogError, "status 必须"):
            catalog.validate_item(self.item, "fixture:1")


if __name__ == "__main__":
    unittest.main()
