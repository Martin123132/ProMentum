from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


class ReleaseScriptTests(unittest.TestCase):
    def _write_valid_release_zip(self, zip_path: Path, *, extra_files: dict[str, str] | None = None) -> None:
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
            release.writestr("idea_collider_app/static/assets/spark-bank-workbench.webp", "fake-webp\n")
            release.writestr("idea_collider_app/static/assets/saved-sparks-shelf.webp", "fake-webp\n")
            release.writestr("scripts/sample_collisions.py", "\n")
            release.writestr("scripts/stop_dev_processes.ps1", "\n")
            release.writestr("docs/demo-bench/README.md", "# Demo Bench\n")
            release.writestr("docs/release-notes/v0.2.0.md", "# ProMentum v0.2.0 Release Review\n")
            release.writestr("docs/screenshots/promentum-start.png", "fake-png\n")
            release.writestr("docs/screenshots/promentum-result.png", "fake-png\n")
            release.writestr("docs/screenshots/promentum-momentum.png", "fake-png\n")
            release.writestr("docs/screenshots/promentum-share-card.png", "fake-png\n")
            for name, content in (extra_files or {}).items():
                release.writestr(name, content)

    def test_verify_release_zip_accepts_valid_zip(self) -> None:
        if sys.platform != "win32":
            self.skipTest("PowerShell release verification is Windows-first.")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "release.zip"
            self._write_valid_release_zip(zip_path)

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

    def test_verify_release_zip_rejects_extra_screenshot(self) -> None:
        if sys.platform != "win32":
            self.skipTest("PowerShell release verification is Windows-first.")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "release.zip"
            self._write_valid_release_zip(
                zip_path,
                extra_files={"docs/screenshots/promentum-concept.png": "stale-image\n"},
            )

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
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("unexpected screenshot file", result.stdout)

    def test_stop_dev_process_script_is_narrowly_scoped(self) -> None:
        script = Path("scripts/stop_dev_processes.ps1").read_text(encoding="utf-8")
        self.assertIn("idea_collider_app\\.app", script)
        self.assertIn("Stop-Process", script)
        self.assertNotIn("Get-Process | Stop-Process", script)


if __name__ == "__main__":
    unittest.main()
