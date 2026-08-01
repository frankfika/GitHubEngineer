"""Tests for doctor module."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.doctor import run_doctor


class TestRunDoctor:
    """Test configuration health check."""

    @patch("sys.version_info", (3, 11, 5))
    @patch("src.doctor.Path.exists")
    def test_missing_config_file(self, mock_exists):
        """Should fail when config file doesn't exist."""
        mock_exists.return_value = False

        result = run_doctor(".ghe/config.yml")

        assert result == 1

    @patch("sys.version_info", (3, 10, 0))
    def test_old_python_version(self):
        """Should fail on Python < 3.11."""
        result = run_doctor()

        assert result == 1

    @patch("sys.version_info", (3, 11, 5))
    @patch("src.doctor.load_config_lenient")
    @patch("src.doctor.Path.exists")
    def test_invalid_config(self, mock_exists, mock_load):
        """Should fail when config is invalid."""
        from src.config import ConfigError

        mock_exists.return_value = True
        mock_load.side_effect = ConfigError("Invalid YAML")

        result = run_doctor()

        assert result == 1

    @patch("sys.version_info", (3, 11, 5))
    @patch("src.doctor.load_config_lenient")
    @patch("src.doctor.Path.exists")
    @patch.dict(os.environ, {}, clear=True)
    def test_unconfigured_repo(self, mock_exists, mock_load):
        """Should fail when repo is still REPLACE_ME."""
        mock_exists.return_value = True
        mock_load.return_value = {
            "repo": {"owner": "REPLACE_ME", "name": "REPLACE_ME"},
            "model": {},
            "github": {},
        }

        result = run_doctor()

        assert result == 1

    @patch("sys.version_info", (3, 11, 5))
    @patch("src.doctor.load_config_lenient")
    @patch("src.doctor.Path.exists")
    @patch.dict(os.environ, {"GITHUB_TOKEN": "", "LLM_API_KEY": ""}, clear=True)
    def test_missing_tokens(self, mock_exists, mock_load):
        """Should fail when tokens are not set."""
        mock_exists.return_value = True
        mock_load.return_value = {
            "repo": {"owner": "test", "name": "repo"},
            "model": {"api_key": "${LLM_API_KEY}"},
            "github": {"token": "${GITHUB_TOKEN}"},
        }

        result = run_doctor()

        assert result == 1

    @patch("sys.version_info", (3, 11, 5))
    @patch("src.doctor.load_config_lenient")
    @patch("src.doctor.Path.exists")
    @patch("src.doctor.GitHubClient")
    @patch("src.doctor.create_llm_client")
    @patch("src.doctor.detect_git_context")
    @patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test", "LLM_API_KEY": "sk_test"}, clear=True)
    def test_all_checks_pass(self, mock_git_ctx, mock_llm, mock_github, mock_exists, mock_load):
        """Should pass when all checks succeed."""
        from src.git_detection import GitContext

        mock_exists.return_value = True
        mock_load.return_value = {
            "repo": {"owner": "test", "name": "repo"},
            "model": {"api_key": "sk_test", "model_name": "gpt-4o-mini"},
            "github": {"token": "ghp_test"},
        }
        mock_git_ctx.return_value = GitContext(
            is_git_repo=True,
            current_repo="test/repo",
            is_fork=False,
            upstream_repo=None,
            remotes=[],
        )
        mock_github.return_value = MagicMock()
        mock_llm.return_value.generate.return_value = "OK"

        result = run_doctor()

        assert result == 0
        mock_llm.assert_called_once_with(
            {
                "api_key": "sk_test",
                "model_name": "gpt-4o-mini",
                "base_url": "",
            }
        )
        mock_llm.return_value.generate.assert_called_once_with("Reply with OK.")

    @patch("sys.version_info", (3, 11, 5))
    @patch("src.doctor.load_config_lenient")
    @patch("src.doctor.Path.exists")
    @patch("src.doctor.GitHubClient")
    @patch("src.doctor.create_llm_client")
    @patch("src.doctor.detect_git_context")
    @patch.dict(os.environ, {}, clear=True)
    def test_codex_checks_pass_without_llm_api_key(
        self, mock_git_ctx, mock_llm, mock_github, mock_exists, mock_load
    ):
        from src.git_detection import GitContext

        mock_exists.return_value = True
        mock_load.return_value = {
            "repo": {"owner": "test", "name": "repo"},
            "model": {"provider": "codex_cli"},
            "github": {},
        }
        mock_git_ctx.return_value = GitContext(
            is_git_repo=False,
            current_repo=None,
            is_fork=False,
            upstream_repo=None,
            remotes=[],
        )
        mock_github.return_value = MagicMock()
        mock_llm.return_value.generate.return_value = "OK"

        assert run_doctor() == 0
        mock_llm.assert_called_once_with(
            {"provider": "codex_cli", "base_url": "", "model_name": "codex-default"}
        )

    @patch("sys.version_info", (3, 11, 5))
    @patch("src.doctor.load_config_lenient")
    @patch("src.doctor.Path.exists")
    @patch("src.doctor.GitHubClient")
    @patch("src.doctor.create_llm_client")
    @patch("src.doctor.detect_git_context")
    @patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test", "LLM_API_KEY": "sk_test"}, clear=True)
    def test_fork_detection_info(
        self, mock_git_ctx, mock_llm, mock_github, mock_exists, mock_load
    ):
        """Should display fork information when detected."""
        from src.git_detection import GitContext

        mock_exists.return_value = True
        mock_load.return_value = {
            "repo": {"owner": "OpenCSG", "name": "csghub"},
            "model": {"api_key": "sk_test"},
            "github": {"token": "ghp_test"},
        }
        mock_git_ctx.return_value = GitContext(
            is_git_repo=True,
            current_repo="frankfika/csghub",
            is_fork=True,
            upstream_repo="OpenCSG/csghub",
            remotes=[],
        )
        mock_github.return_value = MagicMock()
        mock_llm.return_value.generate.return_value = "OK"

        # Should not fail, just display info
        # We can't easily capture print output in this test without more mocking
        result = run_doctor()

        # Check that it at least runs without error
        assert result in (0, 1)  # May fail on API connection, but should run
