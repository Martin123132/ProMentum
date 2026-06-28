from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from idea_collider_app.engine import MODES, generate_collision  # noqa: E402
from idea_collider_app.storage import load_default_state  # noqa: E402


DEMO_CASES = [
    (101, "Sketch Hook", 45, 5),
    (202, "Video Idea", 54, 5),
    (303, "Title Storm", 63, 4),
    (404, "Scene Seed", 72, 5),
    (505, "Concept Mashup", 81, 6),
    (606, "Personal Myth", 52, 5),
    (707, "Serious To Absurd", 88, 5),
    (808, "Sketch Hook", 67, 4),
    (909, "Video Idea", 76, 5),
    (1001, "Title Storm", 49, 6),
    (1102, "Scene Seed", 58, 4),
    (1203, "Concept Mashup", 73, 6),
    (1304, "Personal Myth", 84, 5),
    (1405, "Serious To Absurd", 42, 5),
    (1506, "Sketch Hook", 91, 7),
    (1607, "Video Idea", 61, 4),
    (1708, "Title Storm", 78, 5),
    (1809, "Scene Seed", 86, 6),
    (1910, "Concept Mashup", 55, 5),
    (2011, "Personal Myth", 70, 4),
    (2112, "Serious To Absurd", 64, 6),
    (2213, "Sketch Hook", 50, 5),
    (2314, "Video Idea", 83, 6),
    (2415, "Title Storm", 57, 4),
    (2516, "Scene Seed", 69, 5),
    (2617, "Concept Mashup", 90, 7),
    (2718, "Personal Myth", 47, 5),
    (2819, "Serious To Absurd", 79, 5),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic ProMentum samples.")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--demo", action="store_true", help="Use the curated fixed demo seed set.")
    args = parser.parse_args()

    state = load_default_state()
    output_dir = Path(args.output_dir) if args.output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    cases = DEMO_CASES[: args.count] if args.demo else _generated_cases(args.count)
    for index, (seed, mode, weirdness, ingredient_count) in enumerate(cases):
        result = generate_collision(
            state,
            {"seed": seed, "mode": mode, "weirdness": weirdness, "ingredient_count": ingredient_count},
        )
        header = f"Seed: {seed} | Mode: {mode} | Weirdness: {result['weirdness']} | Ingredients: {ingredient_count}\n"
        text = header + "\n" + result["text"]
        if output_dir:
            path = output_dir / f"{index + 1:02d}-{_slug(mode)}-{seed}.txt"
            path.write_text(text, encoding="utf-8")
        else:
            print("=" * 78)
            print(text)


def _generated_cases(count: int) -> list[tuple[int, str, int, int]]:
    cases = []
    for index in range(count):
        seed = 101 + index * 101
        mode = MODES[1 + (index % (len(MODES) - 1))]
        weirdness = 45 + (index * 9) % 50
        ingredient_count = 4 + index % 4
        cases.append((seed, mode, weirdness, ingredient_count))
    return cases


def _slug(value: str) -> str:
    return "-".join(value.lower().split())


if __name__ == "__main__":
    main()
