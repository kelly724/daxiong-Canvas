import os
import asyncio
import unittest
from unittest.mock import patch

import main


class CodexCliCommandDetectionTests(unittest.TestCase):
    def test_finds_openai_windows_install_when_codex_is_not_on_path(self):
        root = os.path.join(main.BASE_DIR, "output", "_test_codex_cli_detection")
        local_appdata = os.path.join(root, "LocalAppData")
        codex_exe = os.path.join(local_appdata, "Programs", "OpenAI", "Codex", "bin", "codex.exe")
        os.makedirs(os.path.dirname(codex_exe), exist_ok=True)
        with open(codex_exe, "w", encoding="utf-8") as f:
            f.write("")

        env = {
            "LOCALAPPDATA": local_appdata,
            "APPDATA": os.path.join(root, "Roaming"),
            "USERPROFILE": os.path.join(root, "User"),
            "ProgramFiles": os.path.join(root, "ProgramFiles"),
            "ProgramFiles(x86)": os.path.join(root, "ProgramFilesX86"),
        }

        def fake_env_flag(key):
            return "" if key == "CODEX_CLI_BIN" else os.environ.get(key, "")

        with patch.dict(os.environ, env, clear=False):
            with patch.object(main, "codex_cli_env_flag", side_effect=fake_env_flag):
                with patch.object(main.shutil, "which", return_value=None):
                    self.assertEqual(codex_exe, main.codex_cli_command_path())

    def test_explicit_codex_path_takes_precedence_over_path_lookup(self):
        root = os.path.join(main.BASE_DIR, "output", "_test_codex_cli_detection")
        explicit = os.path.join(root, "Manual", "codex.exe")
        os.makedirs(os.path.dirname(explicit), exist_ok=True)
        with open(explicit, "w", encoding="utf-8") as f:
            f.write("")

        with patch.object(main, "codex_cli_env_flag", return_value=""):
            with patch.object(main.shutil, "which", return_value=None):
                self.assertEqual(explicit, main.codex_cli_command_path(explicit))

    def test_configure_local_auth_uses_manual_codex_path(self):
        root = os.path.join(main.BASE_DIR, "output", "_test_codex_cli_detection")
        explicit = os.path.join(root, "ManualConfigure", "codex.exe")
        os.makedirs(os.path.dirname(explicit), exist_ok=True)
        with open(explicit, "w", encoding="utf-8") as f:
            f.write("")

        updates = {}

        def fake_status(command_hint=""):
            return {
                "ready": True,
                "commandPath": command_hint,
                "checks": {"loggedIn": True},
                "authCache": {"path": os.path.join(root, ".codex", "auth.json")},
            }

        with patch.object(main, "codex_cli_status_payload", side_effect=fake_status):
            with patch.object(main, "update_env_values", side_effect=lambda value: updates.update(value)):
                with patch.object(main, "reload_env_globals"):
                    with patch.object(main, "codex_cli_mark_provider_configured", return_value={"id": "codex_cli"}):
                        result = asyncio.run(
                            main.codex_cli_configure_local_auth(
                                main.CodexCliConfigureRequest(codex_cli_bin=explicit)
                            )
                        )

        self.assertTrue(result["configured"])
        self.assertEqual(explicit, updates["CODEX_CLI_BIN"])


if __name__ == "__main__":
    unittest.main()
