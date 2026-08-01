"""Extended coverage for src/config.py.

The original ``tests/test_config.py`` only exercised the legacy single-repo
form. v1.0 added ``get_target_repos`` and ``load_config_lenient``; both need
their own tests.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from src.config import (
    ConfigError,
    get_repo_full_name,
    get_target_repos,
    load_config,
    load_config_lenient,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(yaml.safe_dump(payload, allow_unicode=True), encoding="utf-8")
    return path


def test_load_config_expands_env_placeholders(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GHE_TEST_KEY", "secret-key-1234")
    config_path = _write(
        tmp_path / "config.yml",
        {
            "repo": {"full_name": "acme/widgets"},
            "model": {"api_key": "${GHE_TEST_KEY}", "model_name": "gpt-x"},
        },
    )
    config = load_config(str(config_path))
    assert config["model"]["api_key"] == "secret-key-1234"


def test_load_config_rejects_missing_model_keys(tmp_path: Path):
    config_path = _write(
        tmp_path / "config.yml",
        {"repo": {"full_name": "acme/widgets"}, "model": {}},
    )
    with pytest.raises(ConfigError) as exc:
        load_config(str(config_path))
    assert "api_key" in str(exc.value)


def test_load_config_accepts_codex_without_api_key_or_model(tmp_path: Path):
    config_path = _write(
        tmp_path / "config.yml",
        {
            "repo": {"full_name": "acme/widgets"},
            "model": {"provider": "codex_cli"},
        },
    )
    config = load_config(str(config_path))
    assert config["model"] == {"provider": "codex_cli"}


def test_load_config_lenient_does_not_require_api_key(tmp_path: Path):
    config_path = _write(
        tmp_path / "config.yml",
        {"repo": {"full_name": "acme/widgets"}},
    )
    config = load_config_lenient(str(config_path))
    assert config["repo"]["full_name"] == "acme/widgets"


def test_get_target_repos_returns_single_when_no_list(tmp_path: Path):
    config = {"repo": {"full_name": "acme/widgets"}}
    assert get_target_repos(config) == ["acme/widgets"]


def test_get_target_repos_uses_repos_list(tmp_path: Path):
    config = {"repos": ["acme/widgets", "acme/gadgets"]}
    assert get_target_repos(config) == ["acme/widgets", "acme/gadgets"]


def test_get_target_repos_handles_comma_separated_cli_repo():
    config: dict = {}
    assert get_target_repos(config, cli_repo="a/b,c/d") == ["a/b", "c/d"]


def test_get_target_repos_dedupes_preserving_order():
    config = {"repos": ["a/b", "c/d", "a/b"]}
    assert get_target_repos(config) == ["a/b", "c/d"]


def test_get_target_repos_rejects_malformed_repo_name():
    with pytest.raises(ConfigError):
        get_target_repos({}, cli_repo="not-a-valid-name")
    with pytest.raises(ConfigError):
        get_target_repos({}, cli_repo="owner/")


def test_get_target_repos_rejects_empty_inputs():
    with pytest.raises(ConfigError):
        get_target_repos({})


def test_get_repo_full_name_accepts_owner_and_name():
    config = {"repo": {"owner": "acme", "name": "widgets"}}
    assert get_repo_full_name(config) == "acme/widgets"


def test_get_repo_full_name_prefers_cli_argument():
    config = {"repo": {"full_name": "acme/widgets"}}
    assert get_repo_full_name(config, cli_repo="other/repo") == "other/repo"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
