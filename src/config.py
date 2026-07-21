from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """Raised when configuration is missing or invalid."""


def _replace_env(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _replace_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_env(item) for item in value]
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_name = value[2:-1]
        return os.getenv(env_name, "")
    return value


def load_config(config_path: str | None = None) -> dict[str, Any]:
    """Load YAML config and expand ${ENV_VAR} placeholders."""

    load_dotenv()
    path = Path(config_path or os.getenv("GHE_CONFIG_PATH") or ".ghe/config.yml")
    if not path.exists():
        raw = _default_config()
    else:
        with path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
    config = _replace_env(raw)
    _validate_config(config)
    return config


def get_repo_full_name(config: dict[str, Any], cli_repo: str | None = None) -> str:
    """Return owner/name from CLI or config."""

    if cli_repo:
        return _validate_repo_full_name(cli_repo)

    repo = config.get("repo", {})
    if repo.get("full_name"):
        return _validate_repo_full_name(str(repo["full_name"]))
    owner = repo.get("owner")
    name = repo.get("name")
    if owner and name:
        return _validate_repo_full_name(f"{owner}/{name}")
    raise ConfigError("Set repo.full_name or both repo.owner and repo.name.")


def _validate_repo_full_name(value: str) -> str:
    """Validate the owner/repository form before it reaches the API or filesystem."""

    candidate = value.strip()
    parts = candidate.split("/")
    if len(parts) != 2 or not all(parts) or any(part in {".", ".."} for part in parts):
        raise ConfigError("Repository must use the form owner/name.")
    if any("\\" in part or "/" in part for part in parts):
        raise ConfigError("Repository must use the form owner/name.")
    return candidate


def _validate_config(config: dict[str, Any]) -> None:
    if not isinstance(config, dict):
        raise ConfigError("Configuration root must be a mapping.")
    model = config.get("model", {})
    if not isinstance(model, dict):
        raise ConfigError("model must be a mapping.")
    if not model.get("api_key"):
        raise ConfigError("Missing model.api_key. Set LLM_API_KEY or config value.")
    if not model.get("model_name"):
        raise ConfigError("Missing model.model_name. Set LLM_MODEL or config value.")

    for section in ("repo", "github", "output"):
        value = config.get(section, {})
        if not isinstance(value, dict):
            raise ConfigError(f"{section} must be a mapping.")

    analysis = config.get("analysis", {})
    if not isinstance(analysis, dict):
        raise ConfigError("analysis must be a mapping.")
    for key, minimum in (("lookback_days", 1), ("max_issues_for_llm", 1), ("top_n", 1)):
        if key not in analysis:
            continue
        try:
            value = int(analysis[key])
        except (TypeError, ValueError) as exc:
            raise ConfigError(f"analysis.{key} must be an integer.") from exc
        if value < minimum:
            raise ConfigError(f"analysis.{key} must be at least {minimum}.")


def _default_config() -> dict[str, Any]:
    return {
        "repo": {},
        "github": {"token": "${GITHUB_TOKEN}"},
        "model": {
            "provider": "openai-compatible",
            "base_url": "${LLM_BASE_URL}",
            "api_key": "${LLM_API_KEY}",
            "model_name": "${LLM_MODEL}",
        },
        "output": {
            "format": "markdown",
            "output_dir": "reports",
            "title": "Maintainer Brief - {date}",
        },
        "analysis": {
            "lookback_days": 7,
            "top_n": 3,
            "min_issue_age_hours": 24,
            "max_issues_for_llm": 50,
        },
    }
