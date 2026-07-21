from __future__ import annotations

import unittest

from src.main import format_error


class FormatErrorTest(unittest.TestCase):
    """The CLI must surface actionable hints, not bare exception strings."""

    def test_missing_api_key_hint(self):
        message = format_error(Exception("Missing model.api_key. Set LLM_API_KEY or config value."))
        self.assertIn("Set the LLM_API_KEY environment variable", message)

    def test_rate_limit_hint(self):
        message = format_error(Exception("GitHub API rate limit exceeded."))
        self.assertIn("Wait for the GitHub API rate limit", message)

    def test_unknown_error_falls_back(self):
        message = format_error(Exception("completely unrecognised failure mode"))
        self.assertEqual(message, "Error: completely unrecognised failure mode")
        self.assertNotIn("Hint:", message)

    def test_empty_message_uses_class_name(self):
        message = format_error(Exception(""))
        self.assertIn("Error:", message)


if __name__ == "__main__":
    unittest.main()
