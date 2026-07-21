import os
from pathlib import Path
import tempfile
import unittest

from src.config import load_config


class ConfigTest(unittest.TestCase):
    def test_missing_config_uses_environment_defaults(self):
        old_values = {
            "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN"),
            "LLM_API_KEY": os.environ.get("LLM_API_KEY"),
            "LLM_BASE_URL": os.environ.get("LLM_BASE_URL"),
            "LLM_MODEL": os.environ.get("LLM_MODEL"),
        }
        try:
            os.environ["GITHUB_TOKEN"] = "ghs_test"
            os.environ["LLM_API_KEY"] = "sk_test"
            os.environ["LLM_BASE_URL"] = "https://example.test/v1"
            os.environ["LLM_MODEL"] = "test-model"

            with tempfile.TemporaryDirectory() as tmpdir:
                missing_path = Path(tmpdir) / "missing.yml"
                config = load_config(str(missing_path))

                self.assertEqual(config["github"]["token"], "ghs_test")
                self.assertEqual(config["model"]["api_key"], "sk_test")
                self.assertEqual(config["model"]["model_name"], "test-model")
        finally:
            for key, value in old_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
