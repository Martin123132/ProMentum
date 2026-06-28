from __future__ import annotations

import html
import unittest

from idea_collider_app.engine import generate_collision, readiness, share_card_to_html, share_card_to_text
from scripts.sample_collisions import DEMO_CASES
from idea_collider_app.storage import load_default_state


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = load_default_state()

    def test_same_seed_is_deterministic(self) -> None:
        options = {"seed": 12345, "mode": "Concept Mashup", "weirdness": 60, "ingredient_count": 5}
        first = generate_collision(self.state, options)
        second = generate_collision(self.state, options)
        self.assertEqual(first["text"], second["text"])
        self.assertEqual(first["trace_lines"], second["trace_lines"])

    def test_different_seed_changes_output(self) -> None:
        first = generate_collision(self.state, {"seed": 111, "mode": "Sketch Hook"})
        second = generate_collision(self.state, {"seed": 222, "mode": "Sketch Hook"})
        self.assertNotEqual(first["text"], second["text"])

    def test_trace_lines_include_seven_steps(self) -> None:
        result = generate_collision(self.state, {"seed": 333, "mode": "Personal Myth"})
        for item in result["ingredients"]:
            self.assertEqual(len(item["trace"]["steps"]), 7)

    def test_result_has_required_sections(self) -> None:
        result = generate_collision(self.state, {"seed": 444, "mode": "Video Idea"})
        self.assertIn("best_hook", result)
        self.assertIn("expanded_concept", result)
        self.assertIn("next_steps", result)
        self.assertIn("best_ingredient", result)
        self.assertIn("WHY THIS HAPPENED", result["text"])
        self.assertIn("Next Moves", result["text"])
        self.assertGreaterEqual(len(result["hooks"]), 3)

    def test_share_card_renderers_include_repeatable_context(self) -> None:
        result = generate_collision(self.state, {"seed": 555, "mode": "Concept Mashup"})
        text = share_card_to_text(result)
        card_html = share_card_to_html(result)
        self.assertIn("ProMentum Spark:", text)
        self.assertIn(result["best_hook"], text)
        self.assertIn(result["recipe"], text)
        self.assertIn("ProMentum Share Card", card_html)
        self.assertIn(html.escape(result["best_hook"]), card_html)
        self.assertIn(result["recipe"], card_html)

    def test_readiness_traffic_lights(self) -> None:
        empty = {key: [] for key in ["ideas", "phrases", "people", "places", "obsessions", "questions", "formats", "rules"]}
        self.assertEqual(readiness(empty)["level"], "red")
        self.assertEqual(readiness(self.state)["level"], "green")

    def test_locked_ingredients_are_preserved(self) -> None:
        first = generate_collision(self.state, {"seed": 123, "mode": "Scene Seed", "ingredient_count": 5})
        locked = [{"category": item["category"], "text": item["text"]} for item in first["ingredients"]]
        second = generate_collision(
            self.state,
            {"seed": 456, "mode": "Scene Seed", "ingredient_count": 5, "locked_ingredients": locked},
        )
        self.assertEqual([(item["category"], item["text"]) for item in second["ingredients"]], [(item["category"], item["text"]) for item in first["ingredients"]])

    def test_locked_text_is_included(self) -> None:
        locked_text = self.state["ideas"][0]
        result = generate_collision(self.state, {"seed": 789, "mode": "Concept Mashup", "locked_text": locked_text})
        self.assertIn(locked_text, [item["text"] for item in result["ingredients"]])

    def test_demo_cases_render_valid_results(self) -> None:
        self.assertGreaterEqual(len(DEMO_CASES), 20)
        self.assertLessEqual(len(DEMO_CASES), 30)
        for seed, mode, weirdness, ingredient_count in DEMO_CASES:
            result = generate_collision(
                self.state,
                {"seed": seed, "mode": mode, "weirdness": weirdness, "ingredient_count": ingredient_count},
            )
            self.assertEqual(result["mode"], mode)
            self.assertIn("best_hook", result)
            self.assertIn("Next Moves", result["text"])
            self.assertNotIn("undefined", result["text"])


if __name__ == "__main__":
    unittest.main()
