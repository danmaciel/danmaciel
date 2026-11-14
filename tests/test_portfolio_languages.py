import unittest
from unittest.mock import patch
from io import BytesIO
import json
import xml.etree.ElementTree as ET

from scripts.generate_portfolio_languages import (
    REPOSITORIES, build_svg, languages_for,
)


class LanguagesChartTest(unittest.TestCase):
    def test_chart_is_valid_svg_and_sorts_by_total_bytes(self):
        svg = build_svg({"Go": 600, "Java": 250, "Dart": 150}, "2026-11-13")
        root = ET.fromstring(svg)
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertLess(svg.find(">Go</text>"), svg.find(">Java</text>"))
        self.assertIn("60.0%", svg)
        self.assertIn("25.0%", svg)
        self.assertIn("15.0%", svg)
        self.assertIn("6 repositórios públicos", svg)

    def test_overflow_is_grouped_as_other(self):
        totals = {f"Language-{i}": 10 + i for i in range(9)}
        svg = build_svg(totals, "2026-11-13")
        self.assertIn("Outras", svg)
        self.assertNotIn("Language-0</text>", svg)

    def test_empty_data_fails_without_publishing_fake_chart(self):
        with self.assertRaises(ValueError):
            build_svg({}, "2026-11-13")

    def test_repository_set_is_exactly_the_six_featured(self):
        self.assertEqual(len(REPOSITORIES), 6)
        self.assertEqual(len(set(REPOSITORIES)), 6)
        self.assertIn("agendador_app_monorepo", REPOSITORIES)
        self.assertNotIn("hoppscotch", REPOSITORIES)

    def test_api_response_is_validated(self):
        response = BytesIO(json.dumps({"Go": 4096}).encode())
        class Response:
            def __enter__(self):
                return response
            def __exit__(self, *_):
                pass
        with patch("scripts.generate_portfolio_languages.urlopen", return_value=Response()) as fetch:
            result = languages_for("api", "fake-token")
        self.assertEqual(result, {"Go": 4096})
        request = fetch.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.github.com/repos/danmaciel/api/languages")


if __name__ == "__main__":
    unittest.main()
