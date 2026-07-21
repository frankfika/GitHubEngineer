from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from src.delegation import CodexAdapter, DelegationError, execute_delegation
from src.memory_manager import DecisionMemory
from src.models import DecisionRecord, IssueMetrics, IssuePriority
from src.task_preparer import TaskPreparer


def sample_issue(number: int = 7) -> IssueMetrics:
    now = datetime.now(timezone.utc)
    return IssueMetrics(
        number=number,
        title="Saving a document fails",
        body="Open a document, click Save, then the application shows an error.",
        created_at=now,
        updated_at=now,
        url=f"https://github.com/acme/widgets/issues/{number}",
    )


class FutureCapabilitiesTest(unittest.TestCase):
    def test_rejected_memory_filters_issue_and_persists(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory" / "decisions.yml"
            memory = DecisionMemory.load(path)
            memory.record_decision(DecisionRecord(status="rejected", issue_numbers=[7], reason="out of scope"))
            reloaded = DecisionMemory.load(path)
            self.assertEqual(reloaded.filter_issues([sample_issue()]), [])

    def test_task_preparer_falls_back_without_unverified_repro(self):
        issue = sample_issue()
        priority = IssuePriority(
            issue_number=7,
            title=issue.title,
            priority_score=8,
            reason="Core workflow breaks.",
            user_impact="Documents cannot be saved.",
            estimated_effort="medium",
        )
        llm = Mock()
        llm.generate_json.return_value = {"objective": "Fix save", "reproduction_steps": ["invented"], "reproduction_evidence": "not in issue"}
        task = TaskPreparer(llm).prepare(priority, issue, allowed_directories=["src/"], forbidden_directories=["infra/"])
        self.assertIn("待定位", task)
        self.assertIn("未知：Issue 未提供可验证的复现步骤", task)
        self.assertIn("src/", task)

    def test_delegation_is_dry_run_until_explicitly_enabled(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = CodexAdapter(allowed_root=directory).plan("# Approved task", directory)
            self.assertTrue(plan.dry_run)
            self.assertEqual(plan.command, ("codex", "exec", "-"))
            with self.assertRaises(DelegationError):
                execute_delegation(plan)


if __name__ == "__main__":
    unittest.main()
