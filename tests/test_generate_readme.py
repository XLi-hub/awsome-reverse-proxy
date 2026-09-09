from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_readme.py"
SPEC = importlib.util.spec_from_file_location("generate_readme", SCRIPT)
assert SPEC and SPEC.loader
generate_readme = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generate_readme)


def project(
    repo: str,
    name: str,
    category: str = "general-reverse-proxy",
    stars: int | None = 1,
) -> dict[str, object]:
    github: dict[str, object] = {"license_spdx": "MIT"}
    if stars is not None:
        github["stars"] = stars
    return {
        "repo": repo,
        "name": name,
        "category": category,
        "description_zh": "测试项目。",
        "tags": ["http"],
        "status": "accepted",
        "reviewed_at": "2026-09-08",
        "github": github,
    }


class RenderCatalogTests(unittest.TestCase):
    def test_categories_and_projects_have_deterministic_order(self) -> None:
        items = [
            project("example/zulu", "Zulu", stars=10),
            project("example/lb", "Balancer", "load-balancer", stars=999),
            project("example/alpha", "Alpha", stars=20),
            project("example/alpha-two", "alpha", stars=20),
        ]

        rendered = generate_readme.render_catalog(items)

        self.assertLess(rendered.index("## 通用反向代理"), rendered.index("## 负载均衡器"))
        self.assertLess(rendered.index("example/alpha)"), rendered.index("example/alpha-two)"))
        self.assertLess(rendered.index("example/alpha-two)"), rendered.index("example/zulu)"))

    def test_markdown_is_escaped_in_table_fields(self) -> None:
        item = project("example/proxy", "A [proxy] | fast")
        item["description_zh"] = "支持 *HTTP* | TLS\n第二行"
        item["tags"] = ["http|3", "under_score"]
        item["github"] = {"stars": 12, "license_spdx": "Custom|License"}

        rendered = generate_readme.render_catalog([item])

        self.assertIn(r"[A \[proxy\] \| fast](https://github.com/example/proxy)", rendered)
        self.assertIn(r"支持 \*HTTP\* \| TLS<br>第二行", rendered)
        self.assertIn(r"http\|3、under\_score", rendered)
        self.assertIn(r"Custom\|License", rendered)

    def test_empty_fields_and_non_accepted_projects(self) -> None:
        accepted = project("example/minimal", "Minimal", stars=None)
        accepted["description_zh"] = None
        accepted["tags"] = []
        accepted["reviewed_at"] = None
        accepted["github"] = {}
        candidate = project("example/candidate", "Candidate")
        candidate["status"] = "candidate"

        rendered = generate_readme.render_catalog([accepted])
        rendered_with_candidate = generate_readme.render_catalog([accepted, candidate])

        self.assertIn("| [Minimal]", rendered)
        self.assertIn("| — | — | — | — | — | — | — |", rendered)
        self.assertNotIn("Candidate", rendered_with_candidate)
        self.assertIn("暂无已通过审核的项目。", generate_readme.render_catalog([]))


class GenerateCheckTests(unittest.TestCase):
    def test_check_detects_stale_and_then_synced_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "projects.yaml"
            output = root / "CATALOG.md"
            source.write_text(
                yaml.safe_dump([project("example/proxy", "Proxy")], allow_unicode=True),
                encoding="utf-8",
            )

            self.assertEqual(generate_readme.generate(source, output, check=True), 1)
            self.assertEqual(generate_readme.generate(source, output), 0)
            self.assertEqual(generate_readme.generate(source, output, check=True), 0)


if __name__ == "__main__":
    unittest.main()
