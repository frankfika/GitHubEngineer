import json
from types import SimpleNamespace
from unittest.mock import patch

from src.repair_worker import _pull_request_url, run_repair_job


def test_pull_request_url_extracts_created_draft_pr():
    output = "Creating pull request...\nhttps://github.com/acme/widgets/pull/42\n"
    assert _pull_request_url(output) == "https://github.com/acme/widgets/pull/42"


def test_pull_request_url_returns_empty_when_cli_has_no_url():
    assert _pull_request_url("no pull request was created") == ""


def test_external_repair_uses_isolated_agent_and_fork_pr(tmp_path):
    job_path = tmp_path / "job.json"
    workspace = tmp_path / "workspace"
    job_path.write_text(
        json.dumps(
            {
                "id": "abc123",
                "status": "queued",
                "repository": "upstream/project",
                "viewer": "alice",
                "issue_number": 42,
                "issue_title": "Fix the bug",
                "default_branch": "main",
                "delivery_mode": "fork_pr",
                "workspace": str(workspace),
                "task_markdown": "Fix issue 42 and add a regression test.",
            }
        ),
        encoding="utf-8",
    )
    calls: list[list[str]] = []

    def fake_run(arguments, *, cwd, check=True):
        calls.append(arguments)
        if arguments[:3] == ["git", "status", "--porcelain"]:
            return SimpleNamespace(returncode=0, stdout=" M app.py\n", stderr="")
        if arguments[:3] == ["gh", "repo", "view"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="not found")
        if arguments[:3] == ["gh", "pr", "create"]:
            return SimpleNamespace(
                returncode=0,
                stdout="https://github.com/upstream/project/pull/7\n",
                stderr="",
            )
        return SimpleNamespace(
            returncode=0,
            stdout="Implemented the fix and tests." if arguments[0] == "claude" else "",
            stderr="",
        )

    with patch("src.repair_worker._run", side_effect=fake_run):
        run_repair_job(job_path)
        review = json.loads(job_path.read_text(encoding="utf-8"))
        assert review["status"] == "review_ready"
        assert review["changed_files"] == ["app.py"]

        review["status"] = "queued"
        review["guidance"] = [{"text": "Keep the public API backward compatible."}]
        job_path.write_text(json.dumps(review), encoding="utf-8")
        run_repair_job(job_path, mode="revise")
        revised = json.loads(job_path.read_text(encoding="utf-8"))
        assert revised["status"] == "review_ready"

        run_repair_job(job_path, mode="publish")

    completed = json.loads(job_path.read_text(encoding="utf-8"))
    assert completed["status"] == "completed"
    assert completed["pr_url"] == "https://github.com/upstream/project/pull/7"
    claude_command = next(arguments for arguments in calls if arguments[0] == "claude")
    assert "--bare" in claude_command
    assert any("Fix issue 42" in argument for argument in claude_command)
    revise_command = [arguments for arguments in calls if arguments[0] == "claude"][-1]
    assert any("Keep the public API backward compatible." in argument for argument in revise_command)
    assert ["gh", "repo", "fork", "upstream/project", "--clone=false"] in calls
    assert any(arguments[:2] == ["git", "push"] and "contributor" in arguments for arguments in calls)
