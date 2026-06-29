from __future__ import annotations

import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from urllib import error, request


class AppSmokeTests(unittest.TestCase):
    def test_server_spa_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["PROMENTUM_HOME"] = tmp
            env["IDEA_COLLIDER_DISABLE_OPEN"] = "1"
            proc = subprocess.Popen(
                [sys.executable, "-m", "idea_collider_app.app", "--no-open", "--port", "0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            try:
                url = self._read_url(proc)
                for path in ("/", "/today", "/start", "/bank", "/collide", "/result", "/momentum", "/library", "/settings"):
                    with request.urlopen(f"{url}{path}", timeout=5) as response:
                        self.assertEqual(response.status, 200)
                        body = response.read().decode("utf-8")
                        self.assertIn("text/html", response.headers.get("content-type", ""))
                        self.assertIn("<main id=\"pageRoot\"", body)
                        self.assertIn("ProMentum", body)
                try:
                    request.urlopen(f"{url}/does-not-exist", timeout=5)
                    self.fail("Unknown route should return 404")
                except error.HTTPError as exc:
                    self.assertEqual(getattr(exc, "code", None), 404)
                    payload = json.loads((exc.read() if hasattr(exc, "read") else b"{}").decode("utf-8"))
                else:
                    self.fail("Unknown route should return 404")
                self.assertFalse(payload["ok"])
                app_js = Path("idea_collider_app/static/app.js").read_text(encoding="utf-8")
                app_css = Path("idea_collider_app/static/app.css").read_text(encoding="utf-8")
                launcher = Path("START_ProMentum_WINDOWS.bat").read_text(encoding="utf-8")
                self.assertIn("PROMENTUM_HOME", launcher)
                self.assertIn("D:\\ProMentumData", launcher)
                self.assertIn("ProMentum v", app_js)
                self.assertIn("PROJECT_STAGES", app_js)
                self.assertIn("renderToday", app_js)
                self.assertIn("bindToday", app_js)
                self.assertIn("Today's 10 Minutes", app_js)
                self.assertIn("renderProgressTrack", app_js)
                self.assertIn("const activeIndex = firstIncomplete === -1 ? -1 : firstIncomplete", app_js)
                self.assertIn("coachGenerateButton", app_js)
                self.assertIn("withBusyAction(\"coachGenerateButton\"", app_js)
                self.assertIn("renderCollisionPreview", app_js)
                self.assertIn("updateCollisionPreview", app_js)
                self.assertIn("renderFirstRunCard", app_js)
                self.assertIn("applyFirstRunDefaults", app_js)
                self.assertIn("Seed needs a number", app_js)
                self.assertIn("refreshProgressUI(\"result\")", app_js)
                self.assertIn("coachStorageCheckButton", app_js)
                self.assertIn("withBusyAction(\"coachStorageCheckButton\"", app_js)
                self.assertIn("librarySearchInput", app_js)
                self.assertIn("filteredLibraryFavourites", app_js)
                self.assertIn("renderLibraryStats", app_js)
                self.assertIn("data-copy-favourite-hook", app_js)
                self.assertIn("visual-card-lab", app_js)
                self.assertIn("empty-art-library", app_js)
                self.assertIn("renderStartLaunchStrip", app_js)
                self.assertIn("BANK_CATEGORY_GUIDES", app_js)
                self.assertIn("bankEditorPulse", app_js)
                self.assertIn("updateBankEditorPulse", app_js)
                self.assertIn("renderResultUseMap", app_js)
                self.assertIn("renderShareCard", app_js)
                self.assertIn("shareSummaryText", app_js)
                self.assertIn("renderResultHandoffPanel", app_js)
                self.assertIn("markResultAction", app_js)
                self.assertIn("setResultMessage", app_js)
                self.assertIn("renderMomentum", app_js)
                self.assertIn("bindMomentum", app_js)
                self.assertIn("Save as Project", app_js)
                self.assertIn("Export Today Plan", app_js)
                self.assertIn("Export Progress Log", app_js)
                self.assertIn("project-journal-grid", app_js)
                self.assertIn("Export Project Card", app_js)
                self.assertIn("projectBriefText", app_js)
                self.assertIn("clientProjectReadiness", app_js)
                self.assertIn("if (el(\"settingsMessage\"))", app_js)
                self.assertIn("resultModeNudge", app_js)
                self.assertIn("settingsHealthGrid", app_js)
                self.assertIn("renderSettingsPathList", app_js)
                self.assertIn("updateSettingsDoctor", app_js)
                self.assertIn("promentum-workshop.webp", app_css)
                self.assertIn(".today-layout", app_css)
                self.assertIn(".today-action-card", app_css)
                self.assertIn("promentum-console.webp", app_css)
                self.assertIn("spark-bank-workbench.webp", app_css)
                self.assertIn("saved-sparks-shelf.webp", app_css)
                self.assertIn(".start-launch-strip", app_css)
                self.assertIn(".start-console-art", app_css)
                self.assertIn(".collision-preview-card", app_css)
                self.assertIn(".first-run-card", app_css)
                self.assertIn(".library-toolbar", app_css)
                self.assertIn(".library-stats", app_css)
                self.assertIn(".empty-state-visual", app_css)
                self.assertIn(".bank-category-guide", app_css)
                self.assertIn(".bank-editor-pulse", app_css)
                self.assertIn(".result-use-map", app_css)
                self.assertIn(".result-use-card", app_css)
                self.assertIn(".share-card-panel", app_css)
                self.assertIn(".project-layout", app_css)
                self.assertIn(".project-journal-grid", app_css)
                self.assertIn(".history-entry", app_css)
                self.assertIn(".project-workflow", app_css)
                self.assertIn(".project-action-row", app_css)
                self.assertIn(".result-handoff-panel", app_css)
                self.assertIn(".handoff-card", app_css)
                self.assertIn(".result-export-path", app_css)
                self.assertIn(".settings-health-grid", app_css)
                self.assertIn(".settings-path-row", app_css)
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                if proc.stdout:
                    proc.stdout.close()

    def test_server_doctor_and_generate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["PROMENTUM_HOME"] = tmp
            env["IDEA_COLLIDER_DISABLE_OPEN"] = "1"
            proc = subprocess.Popen(
                [sys.executable, "-m", "idea_collider_app.app", "--no-open", "--port", "0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            try:
                url = self._read_url(proc)
                doctor = self._json(url + "/api/doctor")
                self.assertTrue(doctor["ok"])
                self.assertTrue(doctor["doctor"]["state_ok"])
                self.assertTrue(doctor["doctor"]["data_dir"].startswith(tmp))
                self.assertIn("today", doctor["doctor"])

                started = time.perf_counter()
                generated = self._post_json(
                    url + "/api/generate",
                    {"seed": 5150, "mode": "Sketch Hook", "weirdness": 72, "ingredient_count": 5},
                )
                elapsed = time.perf_counter() - started
                self.assertLess(elapsed, 2)
                self.assertTrue(generated["ok"])
                self.assertIn("best_hook", generated["result"])

                project = self._post_json(url + "/api/projects", {"result": generated["result"]})
                self.assertTrue(project["ok"])
                self.assertIn("actions", project["project"])
                self.assertEqual(project["project"]["readiness"]["level"], "amber")
                self.assertEqual(project["project"]["stage"], "Spark")
                self.assertIn("history", project["project"])
                self.assertTrue(project["project"]["id"].startswith("project-"))

                projects = self._json(url + "/api/projects")
                self.assertEqual(len(projects["projects"]), 1)
                self.assertTrue(projects["today"]["has_action"])
                today = self._json(url + "/api/today")
                self.assertTrue(today["today"]["has_action"])

                project["project"]["readiness_level"] = "green"
                project["project"]["stage"] = "First Step"
                project["project"]["wins"] = ["Made a first pass."]
                project["project"]["blockers"] = ["Need a screenshot."]
                project["project"]["actions"][0]["done"] = True
                updated = self._post_json(url + "/api/projects", {"project": project["project"]})
                self.assertEqual(updated["project"]["readiness"]["level"], "green")
                self.assertEqual(updated["project"]["readiness"]["done"], 1)
                self.assertEqual(updated["project"]["stage"], "First Step")

                project_export = self._post_json(url + "/api/projects/export", {"project": updated["project"]})
                self.assertTrue(project_export["ok"])
                self.assertEqual(project_export["export"]["format"], "project-card")
                self.assertTrue(project_export["export"]["path"].endswith("-project-card.html"))
                brief_export = self._post_json(url + "/api/projects/export", {"project": updated["project"], "format": "project-brief"})
                self.assertEqual(brief_export["export"]["format"], "project-brief")
                today_export = self._post_json(url + "/api/projects/export", {"project": updated["project"], "format": "today-plan"})
                self.assertEqual(today_export["export"]["format"], "today-plan")
                progress_export = self._post_json(url + "/api/projects/export", {"project": updated["project"], "format": "progress-log"})
                self.assertEqual(progress_export["export"]["format"], "progress-log")

                exported = self._post_json(url + "/api/export", {"result": generated["result"], "format": "share"})
                self.assertTrue(exported["ok"])
                self.assertEqual(exported["export"]["format"], "share")
                self.assertTrue(exported["export"]["path"].endswith("-share-card.html"))

                data_folders = self._post_json(url + "/api/open-exports", {})
                self.assertFalse(data_folders["exports_folder"]["opened"])

                reset = self._post_json(url + "/api/state", {"reset": "blank"})
                self.assertTrue(reset["ok"])
                self.assertEqual(reset["readiness"]["level"], "red")

                deleted = self._delete_json(url + "/api/projects", {"id": updated["project"]["id"]})
                self.assertTrue(deleted["ok"])
                self.assertEqual(deleted["projects"], [])
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                if proc.stdout:
                    proc.stdout.close()

    def _read_url(self, proc: subprocess.Popen[str]) -> str:
        assert proc.stdout is not None
        deadline = time.time() + 8
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                continue
            match = re.search(r"http://127\.0\.0\.1:\d+", line)
            if match:
                return match.group(0)
        self.fail("Server did not print a local URL")

    def _json(self, url: str) -> dict:
        with request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _post_json(self, url: str, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, headers={"content-type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _delete_json(self, url: str, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, headers={"content-type": "application/json"}, method="DELETE")
        with request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
