from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.config.loader import ConfigError, ConfigLoader


class ConfigLoaderTests(unittest.TestCase):
    def test_load_valid_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "mode": "polling",
                        "poll_interval": 60,
                        "webhook": {"enabled": True, "port": 8080, "secret": ""},
                        "repositories": [
                            {
                                "owner": "microsoft",
                                "repo": "vscode",
                                "token": "",
                                "enabled": True,
                            }
                        ],
                        "notify_users": ["octocat"],
                        "sound_notification": True,
                        "start_with_windows": False,
                        "log_level": "INFO",
                    }
                ),
                encoding="utf-8",
            )

            config = ConfigLoader(path).load()
            self.assertEqual(config.mode, "polling")
            self.assertEqual(config.poll_interval, 60)
            self.assertEqual(config.repositories[0].full_name, "microsoft/vscode")
            self.assertEqual(config.notify_users, ["octocat"])

    def test_rejects_missing_repositories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"mode": "polling", "repositories": []}), encoding="utf-8")

            with self.assertRaises(ConfigError):
                ConfigLoader(path).load()


if __name__ == "__main__":
    unittest.main()
