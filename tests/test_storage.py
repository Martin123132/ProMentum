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

                opened = storage.open_data_folder()
                self.assertFalse(opened["opened"])
                self.assertTrue(opened["path"].startswith(tmp))

                opened_exports = storage.open_exports_folder()
                self.assertFalse(opened_exports["opened"])
                self.assertTrue(opened_exports["path"].startswith(tmp))

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
