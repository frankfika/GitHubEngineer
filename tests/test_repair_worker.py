import hashlib
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.coding_agent import CodingAgentResult
from src.diff_view import parse_unified_diff, select_unified_diff_hunks
from src.repair_worker import (
    _agent_pass,
    _verification_commands,
    _verify_changes,
    _write_job,
    _prepare_review_index,
    _publish_repair,
    _pull_request_url,
    _run,
    _reviewed_patch,
    render_repair_prompt,
    run_repair_job,
)


def test_write_job_records_distinct_progress_updates(tmp_path):
    job_path = tmp_path / "job.json"
    job = {"id": "abc123", "status": "queued", "message": "已排队"}

    _write_job(job_path, job, status="cloning", message="正在准备工作区")
    _write_job(job_path, job, branch="ghe/issue-1")
    _write_job(job_path, job, status="coding", message="正在修改代码")

    saved = json.loads(job_path.read_text(encoding="utf-8"))
    assert [(item["status"], item["message"]) for item in saved["progress_history"]] == [
        ("cloning", "正在准备工作区"),
        ("coding", "正在修改代码"),
    ]


def test_pull_request_url_extracts_created_draft_pr():
    output = "Creating pull request...\nhttps://github.com/acme/widgets/pull/42\n"
    assert _pull_request_url(output) == "https://github.com/acme/widgets/pull/42"


def test_pull_request_url_returns_empty_when_cli_has_no_url():
    assert _pull_request_url("no pull request was created") == ""


def test_external_repair_uses_isolated_agent_and_fork_pr(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    job_path = tmp_path / "job.json"
    workspace = tmp_path / "workspace"
    job_path.write_text(
        json.dumps(
            {
                "id": "abc123",
                "status": "queued",
                "repository": "upstream/project",
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
    # The worker used to shell out to ``claude --bare`` directly; after
    # the Round 8 refactor the agent is a pluggable provider. The test
    # injects a fake provider that mimics the old behaviour: every
    # ``run()`` call succeeds with the same summary the old claude
    # invocation produced, so the rest of the test can still assert on
    # the worker deriving changed_files from ``git status``.
    provider_calls: list[str] = []

    class _FakeProvider:
        def name(self) -> str:
            return "test_provider"

        def run(self, prompt, workspace, *, on_event=None):
            provider_calls.append(prompt)
            return CodingAgentResult(summary="Implemented the fix and tests.")

    def fake_run(arguments, *, cwd, check=True, env_purpose="worker"):
        calls.append(arguments)
        if arguments[:3] == ["git", "status", "--porcelain"]:
            return SimpleNamespace(returncode=0, stdout=" M app.py\n", stderr="")
        if arguments[:2] == ["git", "ls-files"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if arguments[:2] == ["git", "diff"] and "--stat" not in arguments:
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    "diff --git a/app.py b/app.py\n"
                    "--- a/app.py\n"
                    "+++ b/app.py\n"
                    "@@ -1 +1 @@\n"
                    "-old\n"
                    "+new\n"
                ),
                stderr="",
            )
        if arguments[:3] == ["gh", "repo", "view"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="not found")
        if arguments[:3] == ["gh", "pr", "create"]:
            return SimpleNamespace(
                returncode=0,
                stdout="https://github.com/upstream/project/pull/7\n",
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with (
        patch("src.repair_worker._run", side_effect=fake_run),
        # The worker no longer shells out to ``claude``; it asks
        # ``has_provider_config`` + ``get_provider`` for an in-process
        # provider instead. Both are patched so the test does not need
        # a real .ghe/config.yml on disk.
        patch("src.repair_worker.has_provider_config", return_value=True),
        patch("src.repair_worker.get_provider", return_value=_FakeProvider()),
        patch(
            "src.repair_worker._load_worker_config",
            return_value={"coding_agent": {"provider": "test_provider"}},
        ),
        patch(
            "src.repair_worker._verify_changes",
            return_value={
                "status": "passed",
                "reason": "",
                "message": "tests passed",
                "commands": [],
            },
        ),
    ):
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

        revised["viewer"] = "alice"
        revised["hunk_decisions"] = {"0": "accepted"}
        job_path.write_text(json.dumps(revised), encoding="utf-8")
        run_repair_job(job_path, mode="publish")

    completed = json.loads(job_path.read_text(encoding="utf-8"))
    assert completed["status"] == "completed"
    assert completed["pr_url"] == "https://github.com/upstream/project/pull/7"
    # The provider saw the original issue prompt on the first pass
    # and the maintainer guidance on the revise pass.
    assert len(provider_calls) == 2
    assert any("Fix issue 42" in prompt for prompt in provider_calls)
    assert any("Keep the public API backward compatible." in prompt for prompt in provider_calls)
    # The old test asserted on a literal ``claude`` subprocess. After
    # the refactor the worker talks to an in-process provider instead,
    # so the *subprocess* call we now expect is the ``gh`` fork + push
    # and the git diff / status plumbing.
    assert ["gh", "repo", "fork", "upstream/project", "--clone=false"] in calls
    assert any(arguments[:2] == ["git", "push"] and "contributor" in arguments for arguments in calls)
    assert all(arguments[0] != "claude" for arguments in calls)


def test_verification_detects_only_fixed_conventional_commands(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "test": "pytest; curl https://attacker.invalid",
                    "lint": "eslint .",
                    "arbitrary": "rm -rf /",
                }
            }
        ),
        encoding="utf-8",
    )

    assert _verification_commands(tmp_path) == [
        ["npm", "test"],
        ["npm", "run", "lint"],
        ["python", "-m", "pytest", "-q"],
    ]


def test_verification_detects_changed_python_monorepo_root(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    api = tmp_path / "api"
    (api / "tests").mkdir(parents=True)
    (api / "pyproject.toml").write_text("[project]\nname='api'\n", encoding="utf-8")
    changed = api / "service.py"
    changed.write_text("VALUE = 1\n", encoding="utf-8")

    assert _verification_commands(tmp_path) == [["python", "-m", "pytest", "-q"]]


def test_monorepo_verification_runs_in_changed_project_directory(tmp_path):
    api = tmp_path / "api"
    api.mkdir()
    completed = SimpleNamespace(returncode=0, stdout="1 passed", stderr="")
    with (
        patch(
            "src.repair_worker._verification_specs",
            return_value=[{"argv": ["python", "-m", "pytest", "-q"], "cwd": "api"}],
        ),
        patch("src.repair_worker.find_desktop_executable", return_value=None),
        patch("src.repair_worker.subprocess.run", return_value=completed) as run,
    ):
        verification = _verify_changes(
            tmp_path, {"repair": {"allow_host_verification": True}}
        )

    assert verification["status"] == "passed"
    assert verification["commands"][0]["cwd"] == "api"
    assert verification["commands"][0]["display"].startswith("(cd api && ")
    assert run.call_args.kwargs["cwd"] == api


def test_missing_python_dependency_is_environment_incomplete(tmp_path):
    completed = SimpleNamespace(
        returncode=1,
        stdout="",
        stderr="ModuleNotFoundError: No module named 'sqlalchemy'",
    )
    with (
        patch(
            "src.repair_worker._verification_specs",
            return_value=[{"argv": ["python", "-m", "pytest", "-q"], "cwd": "."}],
        ),
        patch("src.repair_worker.find_desktop_executable", return_value=None),
        patch("src.repair_worker.subprocess.run", return_value=completed),
    ):
        verification = _verify_changes(
            tmp_path, {"repair": {"allow_host_verification": True}}
        )

    assert verification["status"] == "unverified"
    assert verification["reason"] == "dependency_missing"
    assert verification["commands"][0]["exit_code"] == 1


def test_verification_refuses_host_execution_without_explicit_opt_in(tmp_path):
    (tmp_path / "go.mod").write_text("module example.test/x\n", encoding="utf-8")
    with (
        patch("src.repair_worker.find_desktop_executable", return_value=None),
        patch("src.repair_worker.subprocess.run") as run,
    ):
        verification = _verify_changes(tmp_path, {"repair": {}})

    assert verification["status"] == "unverified"
    assert verification["reason"] == "sandbox_unavailable"
    run.assert_not_called()


def test_host_opt_in_verification_uses_secret_free_env_and_records_failure(tmp_path):
    (tmp_path / "go.mod").write_text("module example.test/x\n", encoding="utf-8")
    completed = SimpleNamespace(returncode=1, stdout="FAIL package", stderr="boom")
    with (
        patch("src.repair_worker.find_desktop_executable", return_value=None),
        patch("src.repair_worker.safe_subprocess_env", return_value={"PATH": "/bin"}) as env,
        patch("src.repair_worker.subprocess.run", return_value=completed) as run,
    ):
        verification = _verify_changes(
            tmp_path, {"repair": {"allow_host_verification": True}}
        )

    assert verification["status"] == "failed"
    assert verification["reason"] == "test_failed"
    assert verification["commands"][0]["exit_code"] == 1
    assert run.call_args.args[0] == ["go", "test", "./..."]
    assert run.call_args.kwargs["shell"] is False
    assert run.call_args.kwargs["timeout"] == 300
    assert run.call_args.kwargs["env"] == {"PATH": "/bin"}
    env.assert_called_with("delegate")


def test_host_opt_in_python_verification_uses_current_interpreter(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='x'\nversion='0.0.0'\n",
        encoding="utf-8",
    )
    completed = SimpleNamespace(returncode=0, stdout="1 passed", stderr="")
    with (
        patch("src.repair_worker.find_desktop_executable", return_value=None),
        patch("src.repair_worker.subprocess.run", return_value=completed) as run,
    ):
        verification = _verify_changes(
            tmp_path, {"repair": {"allow_host_verification": True}}
        )

    assert verification["status"] == "passed"
    assert run.call_args.args[0][0] == __import__("sys").executable
    assert run.call_args.args[0][1:] == ["-m", "pytest", "-q"]


def test_repeated_python_verification_does_not_reuse_stale_bytecode(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='x'\nversion='0.0.0'\n",
        encoding="utf-8",
    )
    module = tmp_path / "calc.py"
    module.write_text("def add(a, b):\n    return a * b\n", encoding="utf-8")
    (tmp_path / "tests" / "test_calc.py").write_text(
        "from calc import add\n"
        "def test_add(): assert add(2, 3) == 5\n",
        encoding="utf-8",
    )

    first = _verify_changes(
        tmp_path, {"repair": {"allow_host_verification": True}}
    )
    # Same byte length and potentially the same filesystem mtime second: the
    # classic timestamp-based pyc false-cache case.
    module.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    second = _verify_changes(
        tmp_path, {"repair": {"allow_host_verification": True}}
    )

    assert first["status"] == "failed"
    assert second["status"] == "passed"


def test_frozen_host_verification_discovers_external_python(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='x'\nversion='0.0.0'\n",
        encoding="utf-8",
    )
    completed = SimpleNamespace(returncode=0, stdout="1 passed", stderr="")
    with (
        patch("src.repair_worker.sys.frozen", True, create=True),
        patch(
            "src.repair_worker.find_desktop_executable",
            side_effect=lambda name: "/opt/homebrew/bin/python3" if name == "python3" else None,
        ),
        patch("src.repair_worker.subprocess.run", return_value=completed) as run,
    ):
        verification = _verify_changes(
            tmp_path, {"repair": {"allow_host_verification": True}}
        )

    assert verification["status"] == "passed"
    assert run.call_args.args[0][:2] == ["/opt/homebrew/bin/python3", "-m"]


def test_demo_job_is_rejected_by_worker_publish_boundary(tmp_path):
    job_path = tmp_path / "job.json"
    job_path.write_text(
        json.dumps(
            {
                "id": "demo123",
                "status": "review_ready",
                "repository": "acme/widgets",
                "issue_number": 3,
                "viewer": "alice",
                "workspace": str(tmp_path / "workspace"),
                "is_demo": True,
                "coding_agent_provider": "fake",
            }
        ),
        encoding="utf-8",
    )

    run_repair_job(job_path, mode="publish")

    failed = json.loads(job_path.read_text(encoding="utf-8"))
    assert failed["status"] == "failed"
    assert "cannot be published" in failed["message"]


def test_explicit_per_task_consent_reruns_host_verification(tmp_path):
    job_path = tmp_path / "job.json"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    job_path.write_text(
        json.dumps(
            {
                "id": "verify123",
                "status": "review_ready",
                "repository": "acme/widgets",
                "issue_number": 3,
                "workspace": str(workspace),
                "allow_host_verification": True,
            }
        ),
        encoding="utf-8",
    )
    passed = {
        "status": "passed",
        "message": "1 passed",
        "commands": [{"display": "python -m pytest -q", "exit_code": 0}],
    }

    with patch("src.repair_worker._verify_changes", return_value=passed) as verify:
        run_repair_job(job_path, mode="verify")

    result = json.loads(job_path.read_text(encoding="utf-8"))
    assert result["status"] == "review_ready"
    assert result["verification"] == passed
    config = verify.call_args.args[1]
    assert config["repair"]["allow_host_verification"] is True


def test_host_reverification_fails_closed_without_per_task_consent(tmp_path):
    job_path = tmp_path / "job.json"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    job_path.write_text(
        json.dumps(
            {
                "id": "verify124",
                "status": "review_ready",
                "repository": "acme/widgets",
                "issue_number": 3,
                "workspace": str(workspace),
            }
        ),
        encoding="utf-8",
    )

    run_repair_job(job_path, mode="verify")

    result = json.loads(job_path.read_text(encoding="utf-8"))
    assert result["status"] == "failed"
    assert "explicit per-task consent" in result["message"]


def test_render_repair_prompt_uses_shared_template():
    """Round 7 P1: the web UI, Tauri shell, and CLI all read the same
    prompts/repair.md so a one-line tweak reaches every entry point.
    """

    prompt = render_repair_prompt(42, "acme/widgets", "fix the bug")
    assert "#42" in prompt
    assert "acme/widgets" in prompt
    assert "fix the bug" in prompt
    # The untrusted-evidence warning is the most security-critical
    # sentence; we verify it survives the round-trip so an accidental
    # edit cannot strip it.
    assert "untrusted evidence" in prompt
    assert "commit, push, create forks" in prompt


def test_gh_subprocess_uses_gh_environment(tmp_path):
    completed = SimpleNamespace(returncode=0, stdout="", stderr="")
    with (
        patch("src.repair_worker.safe_subprocess_env", return_value={"GH_TOKEN": "token"}) as env,
        patch("src.repair_worker.subprocess.run", return_value=completed) as run,
        patch("src.repair_worker.find_desktop_executable", return_value="/usr/bin/gh"),
    ):
        _run(["gh", "auth", "status"], cwd=tmp_path, env_purpose="gh")
    env.assert_called_once_with("gh")
    assert run.call_args.kwargs["env"] == {"GH_TOKEN": "token"}


def test_missing_viewer_is_persisted_as_publish_failure(tmp_path):
    job_path = tmp_path / "job.json"
    job_path.write_text(
        json.dumps(
            {
                "id": "missingviewer",
                "status": "review_ready",
                "repository": "acme/widgets",
                "issue_number": 3,
                "workspace": str(tmp_path / "workspace"),
                "verification": {"status": "passed", "commands": []},
            }
        ),
        encoding="utf-8",
    )
    run_repair_job(job_path, mode="publish")
    failed = json.loads(job_path.read_text(encoding="utf-8"))
    assert failed["status"] == "failed"
    assert "No authenticated viewer" in failed["message"]


def _init_repo(workspace):
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.com"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.name", "Tests"], cwd=workspace, check=True)
    original = "".join(f"line {number}\n" for number in range(1, 31))
    (workspace / "app.txt").write_text(original, encoding="utf-8")
    subprocess.run(["git", "add", "app.txt"], cwd=workspace, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=workspace, check=True)


def _review_job(workspace, decisions):
    _prepare_review_index(workspace)
    diff = subprocess.run(
        ["git", "diff", "--binary", "--full-index", "--no-color", "--no-ext-diff"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return {
        "hunk_decisions": decisions,
        "review_diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
        "coding_agent_provider": "real_provider",
        "verification": {"status": "passed", "commands": []},
    }


def test_failed_verification_never_enters_review_ready(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_repo(workspace)
    job_path = tmp_path / "job.json"
    job = {
        "id": "verifyfailed",
        "status": "queued",
        "repository": "acme/widgets",
        "issue_number": 9,
        "workspace": str(workspace),
    }
    job_path.write_text(json.dumps(job), encoding="utf-8")

    class _Provider:
        def name(self):
            return "real_provider"

        def run(self, prompt, target, *, on_event=None):
            (target / "app.txt").write_text("broken change\n", encoding="utf-8")
            return CodingAgentResult(summary="Changed app.txt")

    failed_verification = {
        "status": "failed",
        "reason": "test_failed",
        "message": "验证失败：python -m pytest -q",
        "commands": [
            {
                "argv": ["python", "-m", "pytest", "-q"],
                "exit_code": 1,
                "stderr_summary": "one regression failed",
            }
        ],
    }
    with patch("src.repair_worker._verify_changes", return_value=failed_verification):
        with pytest.raises(RuntimeError, match="验证失败"):
            _agent_pass(job_path, job, workspace, "fix it", provider=_Provider())

    persisted = json.loads(job_path.read_text(encoding="utf-8"))
    assert persisted["status"] == "failed"
    assert persisted["error_kind"] == "test_failed"
    assert persisted["verification"]["commands"][0]["exit_code"] == 1


def test_failed_verification_is_fed_back_once_and_can_recover(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_repo(workspace)
    job_path = tmp_path / "job.json"
    job = {
        "id": "verifyrecover",
        "status": "queued",
        "repository": "acme/widgets",
        "issue_number": 10,
        "workspace": str(workspace),
    }
    job_path.write_text(json.dumps(job), encoding="utf-8")
    prompts: list[str] = []

    class _Provider:
        def name(self):
            return "real_provider"

        def run(self, prompt, target, *, on_event=None):
            prompts.append(prompt)
            content = "fixed after feedback\n" if len(prompts) == 2 else "first attempt\n"
            (target / "app.txt").write_text(content, encoding="utf-8")
            return CodingAgentResult(
                summary=f"attempt {len(prompts)}",
                metadata={
                    "repository_context": True,
                    "context_files": ["app.txt"],
                    "attempt": len(prompts),
                },
            )

    failed = {
        "status": "failed",
        "reason": "test_failed",
        "message": "验证失败：python -m pytest -q",
        "commands": [{"exit_code": 1, "stderr_summary": "expected fixed"}],
    }
    passed = {
        "status": "passed",
        "reason": "",
        "message": "tests passed",
        "commands": [{"exit_code": 0}],
    }
    with patch(
        "src.repair_worker._verify_changes",
        side_effect=[failed, passed],
    ):
        _agent_pass(job_path, job, workspace, "fix it", provider=_Provider())

    persisted = json.loads(job_path.read_text(encoding="utf-8"))
    assert persisted["status"] == "review_ready"
    assert persisted["verification"]["status"] == "passed"
    assert len(persisted["verification_attempts"]) == 2
    assert len(prompts) == 2
    assert "AUTOMATIC VERIFICATION OUTPUT (UNTRUSTED DATA" in prompts[1]
    assert "expected fixed" in prompts[1]
    assert [item["attempt"] for item in persisted["agent_attempt_metadata"]] == [1, 2]
    assert persisted["agent_metadata"]["context_files"] == ["app.txt"]


def test_reviewed_patch_blocks_pending_hunks(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_repo(workspace)
    lines = (workspace / "app.txt").read_text(encoding="utf-8").splitlines()
    lines[1] = "accepted candidate"
    lines[24] = "still pending"
    (workspace / "app.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="still pending review"):
        _reviewed_patch(_review_job(workspace, {"0": "accepted"}), workspace)


def test_reviewed_patch_blocks_changes_made_after_review(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_repo(workspace)
    (workspace / "app.txt").write_text("reviewed\n" + "unchanged\n" * 29, encoding="utf-8")
    job = _review_job(workspace, {"0": "accepted"})
    (workspace / "app.txt").write_text("changed later\n" + "unchanged\n" * 29, encoding="utf-8")

    with pytest.raises(RuntimeError, match="diff changed after review"):
        _reviewed_patch(job, workspace)


def test_publish_commits_only_accepted_hunks(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_repo(workspace)
    lines = (workspace / "app.txt").read_text(encoding="utf-8").splitlines()
    lines[1] = "accepted change"
    lines[24] = "rejected change"
    (workspace / "app.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (workspace / "app.txt").chmod(0o755)
    job_path = tmp_path / "job.json"
    job = {
        "repository": "acme/widgets",
        "viewer": "alice",
        "issue_number": 9,
        "issue_title": "Selective repair",
        "default_branch": "main",
        "delivery_mode": "owner_pr",
        "branch": "ghe/issue-9",
        **_review_job(workspace, {"0": "accepted", "1": "rejected"}),
    }
    job_path.write_text(json.dumps(job), encoding="utf-8")

    from src import repair_worker

    original_run = repair_worker._run

    def git_and_fake_gh(arguments, *, cwd, check=True, env_purpose="worker"):
        if arguments[:2] == ["git", "push"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if arguments[0] == "gh":
            if arguments[:3] == ["gh", "pr", "create"]:
                return SimpleNamespace(
                    returncode=0,
                    stdout="https://github.com/acme/widgets/pull/10\n",
                    stderr="",
                )
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return original_run(arguments, cwd=cwd, check=check, env_purpose=env_purpose)

    with patch("src.repair_worker._run", side_effect=git_and_fake_gh):
        _publish_repair(job_path, job, workspace)

    committed = subprocess.run(
        ["git", "show", "HEAD:app.txt"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    working_tree = (workspace / "app.txt").read_text(encoding="utf-8")
    assert "accepted change" in committed
    assert "rejected change" not in committed
    assert "rejected change" in working_tree
    committed_mode = subprocess.run(
        ["git", "ls-tree", "HEAD", "app.txt"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()[0]
    assert committed_mode == "100644"
    assert (workspace / "app.txt").stat().st_mode & 0o111
    assert json.loads(job_path.read_text(encoding="utf-8"))["status"] == "completed"


def test_untracked_file_is_exposed_to_review_diff(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_repo(workspace)
    (workspace / "new file.txt").write_text("new content\n", encoding="utf-8")

    _prepare_review_index(workspace)

    diff = subprocess.run(
        ["git", "diff", "--no-color", "--no-ext-diff"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "new file.txt" in diff
    assert "+new content" in diff

    patch_text = _reviewed_patch(_review_job(workspace, {"0": "accepted"}), workspace)
    subprocess.run(
        ["git", "apply", "--cached", "--whitespace=nowarn", "-"],
        cwd=workspace,
        check=True,
        input=patch_text,
        text=True,
        capture_output=True,
    )
    cached = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert cached.strip() == "new file.txt"


def test_publish_push_failure_restores_review_and_reuses_commit(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_repo(workspace)
    (workspace / "app.txt").write_text("accepted\n" + "line\n" * 29, encoding="utf-8")
    job_path = tmp_path / "job.json"
    job = {
        "repository": "acme/widgets", "viewer": "alice", "issue_number": 11,
        "issue_title": "Retry publish", "default_branch": "main",
        "delivery_mode": "owner_pr", "branch": "ghe/issue-11",
        **_review_job(workspace, {"0": "accepted"}),
    }
    job_path.write_text(json.dumps(job), encoding="utf-8")
    base_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=workspace, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    from src import repair_worker

    original_run = repair_worker._run
    push_attempts = 0

    def fail_once(arguments, *, cwd, check=True, env_purpose="worker"):
        nonlocal push_attempts
        if arguments[:2] == ["git", "push"]:
            push_attempts += 1
            if push_attempts == 1:
                raise RuntimeError("injected push failure")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if arguments[:3] == ["gh", "pr", "list"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if arguments[:3] == ["gh", "pr", "create"]:
            return SimpleNamespace(
                returncode=0,
                stdout="https://github.com/acme/widgets/pull/11\n", stderr="",
            )
        return original_run(arguments, cwd=cwd, check=check, env_purpose=env_purpose)

    with patch("src.repair_worker._run", side_effect=fail_once):
        _publish_repair(job_path, job, workspace)
        failed = json.loads(job_path.read_text(encoding="utf-8"))
        assert failed["status"] == "review_ready"
        assert failed["publish_commit_sha"]
        assert subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=workspace, check=True,
            capture_output=True, text=True,
        ).stdout.strip() == base_sha
        _publish_repair(job_path, job, workspace)

    completed = json.loads(job_path.read_text(encoding="utf-8"))
    assert completed["status"] == "completed"
    assert push_attempts == 2
    assert subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=workspace, check=True,
        capture_output=True, text=True,
    ).stdout.strip() == completed["publish_commit_sha"]


def test_publish_pr_failure_reuses_push_and_discovers_existing_pr(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _init_repo(workspace)
    (workspace / "app.txt").write_text("accepted\n" + "line\n" * 29, encoding="utf-8")
    job_path = tmp_path / "job.json"
    job = {
        "repository": "acme/widgets", "viewer": "alice", "issue_number": 12,
        "issue_title": "Retry PR", "default_branch": "main",
        "delivery_mode": "owner_pr", "branch": "ghe/issue-12",
        **_review_job(workspace, {"0": "accepted"}),
    }
    job_path.write_text(json.dumps(job), encoding="utf-8")
    from src import repair_worker

    original_run = repair_worker._run
    push_calls = list_calls = create_calls = 0

    def lost_response(arguments, *, cwd, check=True, env_purpose="worker"):
        nonlocal push_calls, list_calls, create_calls
        if arguments[:2] == ["git", "push"]:
            push_calls += 1
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if arguments[:3] == ["gh", "pr", "list"]:
            list_calls += 1
            url = "https://github.com/acme/widgets/pull/12\n" if list_calls > 1 else ""
            return SimpleNamespace(returncode=0, stdout=url, stderr="")
        if arguments[:3] == ["gh", "pr", "create"]:
            create_calls += 1
            raise RuntimeError("injected lost PR response")
        return original_run(arguments, cwd=cwd, check=check, env_purpose=env_purpose)

    with patch("src.repair_worker._run", side_effect=lost_response):
        _publish_repair(job_path, job, workspace)
        assert json.loads(job_path.read_text(encoding="utf-8"))["status"] == "review_ready"
        _publish_repair(job_path, job, workspace)

    completed = json.loads(job_path.read_text(encoding="utf-8"))
    assert completed["status"] == "completed"
    assert completed["pr_url"].endswith("/pull/12")
    assert push_calls == 1
    assert create_calls == 1


def test_diff_selection_drops_mode_metadata_and_blocks_rename():
    mode_patch = (
        "diff --git a/tool.sh b/tool.sh\nold mode 100644\nnew mode 100755\n"
        "--- a/tool.sh\n+++ b/tool.sh\n@@ -1 +1 @@\n-old\n+new\n"
    )
    selected, total, unsupported = select_unified_diff_hunks(mode_patch, {0})
    assert (total, unsupported) == (1, 0)
    assert "old mode" not in selected and "new mode" not in selected

    rename_patch = (
        "diff --git a/old.py b/new.py\nsimilarity index 80%\n"
        "rename from old.py\nrename to new.py\n--- a/old.py\n+++ b/new.py\n"
        "@@ -1 +1 @@\n-old\n+new\n"
    )
    selected, total, unsupported = select_unified_diff_hunks(rename_patch, {0})
    assert selected == ""
    assert (total, unsupported) == (1, 1)


def test_diff_parser_preserves_header_and_decodes_quoted_paths():
    parsed = parse_unified_diff(
        'diff --git "a/foo bar.py" "b/foo bar.py"\n'
        '--- "a/foo bar.py"\n+++ "b/foo bar.py"\n'
        "@@ -1 +1 @@ def run():\n-old\n+new\n"
        "diff --git a/bacon.py b/bacon.py\n--- a/bacon.py\n+++ b/bacon.py\n"
        "@@ -2 +2 @@\n-a\n+b\n"
    )
    assert parsed["files"][0]["path"] == "foo bar.py"
    assert parsed["files"][0]["hunks"][0]["header"] == "@@ -1 +1 @@ def run():"
    assert parsed["files"][1]["path"] == "bacon.py"
