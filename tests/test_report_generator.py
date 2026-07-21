from __future__ import annotations

from datetime import datetime, timezone
import unittest

from src.models import IssueCluster, IssuePriority, MaintainerBrief
from src.report_generator import ReportGenerator


class ReportGeneratorTest(unittest.TestCase):
    def _priority(self, number: int, *, url: str = "") -> IssuePriority:
        return IssuePriority(
            issue_number=number,
            title=f"Issue {number}",
            priority_score=7.0,
            reason="Reason",
            user_impact="Impact",
            estimated_effort="low",
            url=url,
        )

    def test_renders_clickable_issue_link_when_url_present(self):
        brief = MaintainerBrief(
            generated_at=datetime(2026, 7, 21, tzinfo=timezone.utc),
            period="last 7 days",
            summary="Summary",
            new_issues_count=1,
            top_priorities=[
                self._priority(42, url="https://github.com/acme/widgets/issues/42"),
            ],
        )
        markdown = ReportGenerator().generate_markdown(brief, "acme/widgets")
        self.assertIn(
            "[#42](https://github.com/acme/widgets/issues/42): Issue 42",
            markdown,
        )

    def test_falls_back_to_plain_number_when_url_missing(self):
        brief = MaintainerBrief(
            generated_at=datetime.now(timezone.utc),
            period="last 7 days",
            summary="Summary",
            new_issues_count=1,
            top_priorities=[self._priority(7)],
        )
        markdown = ReportGenerator().generate_markdown(brief, "owner/repo")
        self.assertIn("#7: Issue 7", markdown)
        self.assertNotIn("[#7]", markdown)

    def test_renders_empty_brief_with_explicit_messages(self):
        brief = MaintainerBrief(
            generated_at=datetime.now(timezone.utc),
            period="last 7 days",
            summary="Nothing to report this week.",
            new_issues_count=0,
        )
        markdown = ReportGenerator().generate_markdown(brief, "owner/repo")
        self.assertIn("No high-confidence priorities were identified.", markdown)
        self.assertNotIn("## Quick Wins", markdown)
        self.assertIn("## Trend", markdown)
        self.assertIn("Nothing to report this week.", markdown)

    def test_renders_multiple_clusters_and_truncates_missing_info(self):
        brief = MaintainerBrief(
            generated_at=datetime.now(timezone.utc),
            period="last 7 days",
            summary="Summary",
            new_issues_count=20,
            top_priorities=[self._priority(1)],
            issue_clusters=[
                IssueCluster(
                    cluster_name="Login broken",
                    issue_numbers=[1, 2, 3],
                    common_theme="Login flow regressions",
                ),
            ],
            missing_info_issues=list(range(1, 30)),
        )
        markdown = ReportGenerator().generate_markdown(brief, "owner/repo")
        self.assertIn("## Possible Duplicate Clusters", markdown)
        self.assertIn("#1, #2, #3", markdown)
        # Missing info is capped to 10 entries
        self.assertIn("## Missing Information", markdown)
        # Count lines starting with "- #" in missing info: must be <= 10
        in_missing = False
        count = 0
        for line in markdown.splitlines():
            if line.strip() == "## Missing Information":
                in_missing = True
                continue
            if in_missing and line.startswith("## "):
                break
            if in_missing and line.startswith("- #"):
                count += 1
        self.assertLessEqual(count, 10)


if __name__ == "__main__":
    unittest.main()
