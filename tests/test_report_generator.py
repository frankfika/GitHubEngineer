from datetime import datetime, timezone
import unittest

from src.models import IssuePriority, MaintainerBrief
from src.report_generator import ReportGenerator


class ReportGeneratorTest(unittest.TestCase):
    def test_generate_markdown_contains_priority(self):
        brief = MaintainerBrief(
            generated_at=datetime.now(timezone.utc),
            period="last 7 days",
            summary="Several users hit the same install issue.",
            new_issues_count=3,
            top_priorities=[
                IssuePriority(
                    issue_number=12,
                    title="Install fails on macOS",
                    priority_score=8.0,
                    reason="Multiple comments report the same failure.",
                    user_impact="Blocks installation.",
                    estimated_effort="low",
                )
            ],
        )

        markdown = ReportGenerator().generate_markdown(brief, "owner/repo")

        self.assertIn("# Maintainer Brief", markdown)
        self.assertIn("#12: Install fails on macOS", markdown)
        self.assertIn("Multiple comments", markdown)


if __name__ == "__main__":
    unittest.main()

