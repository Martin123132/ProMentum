from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


class ReleaseScriptTests(unittest.TestCase):
    def test_verify_release_zip_accepts_valid_zip(self) -> None:
        if sys.platform != "win32":
            self.skipTest("PowerShell release verification is Windows-first.")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "release.zip"
            with zipfile.ZipFile(zip_path, "w") as release:
                release.writestr("START_ProMentum_WINDOWS.bat", "@echo off\n")
                release.writestr("LICENSE", "PolyForm Noncommercial License 1.0.0\n")
                release.writestr("README.md", "# ProMentum\n")
                release.writestr("pyproject.toml", "[project]\nname='promentum'\n")
                release.writestr("idea_collider_app/app.py", "print('doctor')\n")
                release.writestr("idea_collider_app/engine.py", "\n")
                release.writestr("idea_collider_app/storage.py", "\n")
                release.writestr("idea_collider_app/seeds/default_idea_bank.json", "{}\n")
                release.writestr("idea_collider_app/templates/index.html", "<!doctype html>\n")
                release.writestr("idea_collider_app/static/app.js", "\n")
                release.writestr("idea_collider_app/static/app.css", "\n")
                release.writestr("idea_collider_app/static/assets/promentum-workshop.webp", "fake-webp\n")
                release.writestr("idea_collider_app/static/assets/promentum-console.webp", "fake-webp\n")
                release.writestr("scripts/sample_collisions.py", "\n")
                release.writestr("scripts/stop_dev_processes.ps1", "\n")
                release.writestr("docs/demo-bench/README.md", "# Demo Bench\n")

            result = subprocess.run(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    "scripts\\verify_release_zip.ps1",
                    "-ZipPath",
                    str(zip_path),
                    "-WorkRoot",
                    str(root / "verify-work"),
                    "-SkipDoctor",
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("Release ZIP verified", result.stdout)

    def test_stop_dev_process_script_is_narrowly_scoped(self) -> None:
        script = Path("scripts/stop_dev_processes.ps1").read_text(encoding="utf-8")
        self.assertIn("idea_collider_app\\.app", script)
        self.assertIn("Stop-Process", script)
        self.assertNotIn("Get-Process | Stop-Process", script)


if __name__ == "__main__":
    unittest.main()
