from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest


class StorageTests(unittest.TestCase):
    def test_storage_saves_to_override_and_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("PROMENTUM_HOME")
            old_disable = os.environ.get("IDEA_COLLIDER_DISABLE_OPEN")
            os.environ["PROMENTUM_HOME"] = tmp
            os.environ["IDEA_COLLIDER_DISABLE_OPEN"] = "1"
            try:
                from idea_collider_app import storage
                from idea_collider_app.engine import generate_collision

                state = storage.load_default_state()
                state["ideas"][0] = "test idea"
                storage.save_state(state)
                loaded = storage.load_state()
                self.assertEqual(loaded["ideas"][0], "test idea")

                result = generate_collision(loaded, {"seed": 1, "mode": "Concept Mashup"})
                favourite = storage.save_favourite(result)
                self.assertEqual(storage.list_favourites()[0]["id"], favourite["id"])

                exported = storage.export_result(result, "txt")
                self.assertTrue(Path(exported["path"]).exists())
                self.assertTrue(str(exported["path"]).startswith(tmp))

                share_export = storage.export_result(result, "share")
                share_path = Path(share_export["path"])
                self.assertEqual(share_export["format"], "share")
                self.assertTrue(share_path.exists())
                self.assertTrue(share_path.name.endswith("-share-card.html"))
                self.assertIn("ProMentum Share Card", share_path.read_text(encoding="utf-8"))

                opened = storage.open_data_folder()
                self.assertFalse(opened["opened"])
                self.assertEqual(Path(opened["path"]), Path(tmp).resolve())

                opened_exports = storage.open_exports_folder()
                self.assertFalse(opened_exports["opened"])
                self.assertEqual(Path(opened_exports["path"]), Path(tmp).resolve() / "exports")

                project = storage.save_project_from_result(result)
                self.assertEqual(storage.list_projects()[0]["id"], project["id"])
                self.assertEqual(project["stage"], "Spark")
                self.assertEqual(project["readiness"]["level"], "amber")
                self.assertIn("history", project)
                project["actions"][0]["done"] = True
                project["readiness_level"] = "green"
                project["stage"] = "First Step"
                project["wins"] = ["Made a first pass."]
                project["blockers"] = ["Need a title."]
                project["history"] = [{"kind": "win", "text": "Made a first pass.", "created_at": "2026-06-29T00:00:00Z"}]
                updated = storage.save_project(project)
                self.assertEqual(updated["readiness"]["done"], 1)
                self.assertEqual(updated["readiness"]["level"], "green")
                self.assertEqual(updated["stage"], "First Step")
                self.assertEqual(updated["wins"], ["Made a first pass."])
                self.assertEqual(updated["blockers"], ["Need a title."])
                today = storage.today_plan()
                self.assertTrue(today["has_action"])
                self.assertEqual(today["project_id"], updated["id"])
                project_export = storage.export_project(updated)
                project_path = Path(project_export["path"])
                self.assertEqual(project_export["format"], "project-card")
                self.assertTrue(project_path.exists())
                self.assertTrue(project_path.name.endswith("-project-card.html"))
                self.assertIn("ProMentum Project Card", project_path.read_text(encoding="utf-8"))
                self.assertTrue(project_path.is_relative_to(Path(tmp)))
                brief_export = storage.export_project(updated, "project-brief")
                self.assertEqual(brief_export["format"], "project-brief")
                self.assertTrue(Path(brief_export["path"]).name.endswith("-project-brief.txt"))
                today_export = storage.export_project(updated, "today-plan")
                self.assertEqual(today_export["format"], "today-plan")
                self.assertIn("ProMentum Today Plan", Path(today_export["path"]).read_text(encoding="utf-8"))
                log_export = storage.export_project(updated, "progress-log")
                self.assertEqual(log_export["format"], "progress-log")
                self.assertIn("ProMentum Progress Log", Path(log_export["path"]).read_text(encoding="utf-8"))
                storage.delete_project(updated["id"])
                self.assertEqual(storage.list_projects(), [])
                self.assertFalse(storage.today_plan()["has_action"])

                blank = storage.reset_blank_state()
                self.assertEqual(sum(len(blank[key]) for key in storage.INGREDIENT_KEYS), 0)
                self.assertEqual(storage.doctor()["readiness"]["level"], "red")
            finally:
                if old_home is None:
                    os.environ.pop("PROMENTUM_HOME", None)
                else:
                    os.environ["PROMENTUM_HOME"] = old_home
                if old_disable is None:
                    os.environ.pop("IDEA_COLLIDER_DISABLE_OPEN", None)
                else:
                    os.environ["IDEA_COLLIDER_DISABLE_OPEN"] = old_disable

    def test_legacy_home_env_still_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_promentum = os.environ.get("PROMENTUM_HOME")
            old_legacy = os.environ.get("IDEA_COLLIDER_HOME")
            os.environ.pop("PROMENTUM_HOME", None)
            os.environ["IDEA_COLLIDER_HOME"] = tmp
            try:
                from idea_collider_app import storage

                self.assertEqual(Path(storage.app_data_dir()), Path(tmp))
            finally:
                if old_promentum is None:
                    os.environ.pop("PROMENTUM_HOME", None)
                else:
                    os.environ["PROMENTUM_HOME"] = old_promentum
                if old_legacy is None:
                    os.environ.pop("IDEA_COLLIDER_HOME", None)
                else:
                    os.environ["IDEA_COLLIDER_HOME"] = old_legacy


if __name__ == "__main__":
    unittest.main()
