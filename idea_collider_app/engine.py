from __future__ import annotations

import html
import random
import time
from typing import Any


MODES = [
    "Random Spark",
    "Sketch Hook",
    "Video Idea",
    "Title Storm",
    "Scene Seed",
    "Concept Mashup",
    "Personal Myth",
    "Serious To Absurd",
]

INGREDIENT_KEYS = ["ideas", "phrases", "people", "places", "obsessions", "questions", "formats", "rules"]
PRIMES = [17, 19, 23, 29, 31, 37, 41, 43]
DRIFTS = ["preserve", "invert", "exaggerate", "misremember", "literalize", "compress", "collide", "make official"]
COLLISIONS = ["fusion", "argument", "ceremony", "bad rule", "useful accident", "callback loop", "public misunderstanding"]
MODE_NEXT_STEPS = {
    "Sketch Hook": ["Find the first visual gag.", "Give one character a practical need.", "End on the smallest callback."],
    "Video Idea": ["Open with the strangest image.", "Cut before the explanation catches up.", "Make the caption carry the premise."],
    "Title Storm": ["Pick the title with a verb in it.", "Write the fake subtitle.", "Use the dullest title as the serious version."],
    "Scene Seed": ["Name who enters first.", "Give the room one rule.", "Let the interruption win the scene."],
    "Concept Mashup": ["Keep the human motive simple.", "Let one ingredient become the mechanism.", "Save the weirdest ingredient for the turn."],
    "Personal Myth": ["Make the private feeling visible.", "Choose the object that represents it.", "End with a ritual nobody asked for."],
    "Serious To Absurd": ["Write the serious pitch first.", "Add one over-logical rule.", "Let the conclusion embarrass the premise."],
}


def readiness(state: dict[str, Any]) -> dict[str, Any]:
    counts = {key: len(_clean_list(state.get(key))) for key in INGREDIENT_KEYS}
    total = sum(counts.values())
    populated = sum(1 for count in counts.values() if count > 0)
    if total >= 20 and populated >= 5:
        level = "green"
        label = "Ready"
        next_action = "Generate a first move"
    elif total >= 10 and populated >= 3:
        level = "amber"
        label = "Enough to try"
        next_action = "Add a few sharper ingredients or generate now"
    else:
        level = "red"
        label = "Needs fuel"
        missing = max(0, 10 - total)
        next_action = f"Add {missing} more ingredients" if missing else "Add more variety"
    return {
        "level": level,
        "label": label,
        "next_action": next_action,
        "total": total,
        "populated_categories": populated,
        "counts": counts,
    }


def generate_collision(state: dict[str, Any], options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or {}
    seed = _coerce_seed(options.get("seed"))
    rng = random.Random(seed)
    mode = str(options.get("mode") or "Random Spark")
    if mode == "Random Spark":
        mode = rng.choice(MODES[1:])
    elif mode not in MODES:
        mode = "Concept Mashup"
    weirdness = _clamp_int(options.get("weirdness"), 0, 100, 55)
    ingredient_count = _clamp_int(options.get("ingredient_count"), 3, 7, 5)

    bank = _bank_items(state)
    selected = _select_ingredients(bank, rng, ingredient_count, options)
    traces = [_trace_for(item, index, seed, weirdness) for index, item in enumerate(selected)]
    drifted = [_drift_item(item, traces[index], rng, weirdness) for index, item in enumerate(selected)]
    collision = _resolve_collision(drifted, traces, rng, weirdness, mode)

    title = _make_title(drifted, rng, mode)
    hooks = _make_hooks(drifted, collision, rng, mode, weirdness)
    best_hook = _choose_best_hook(hooks, mode, weirdness)
    expanded = _expand_concept(drifted, collision, rng, mode, best_hook)
    sketch_seed = _make_sketch_seed(drifted, collision, rng, mode)
    next_steps = _make_next_steps(drifted, mode, rng)
    best_ingredient = _choose_best_ingredient(drifted)
    trace_lines = _trace_lines(traces, drifted, collision)
    recipe = f"ProMentum seed {seed} | mode {mode} | weirdness {weirdness} | ingredients {ingredient_count}"

    text = collision_to_text(
        {
            "title": title,
            "best_hook": best_hook,
            "mode": mode,
            "seed": seed,
            "weirdness": weirdness,
            "ingredients": drifted,
            "hooks": hooks,
            "expanded_concept": expanded,
            "sketch_seed": sketch_seed,
            "next_steps": next_steps,
            "trace_lines": trace_lines,
            "collision": collision,
            "recipe": recipe,
        }
    )

    return {
        "title": title,
        "best_hook": best_hook,
        "mode": mode,
        "seed": seed,
        "weirdness": weirdness,
        "ingredient_count": ingredient_count,
        "ingredients": drifted,
        "hooks": hooks,
        "expanded_concept": expanded,
        "sketch_seed": sketch_seed,
        "next_steps": next_steps,
        "best_ingredient": best_ingredient,
        "trace_lines": trace_lines,
        "collision": collision,
        "recipe": recipe,
        "text": text,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def collision_to_text(result: dict[str, Any]) -> str:
    lines = [
        str(result.get("title") or "Untitled Spark").upper(),
        "",
        f"Best hook: {result.get('best_hook')}",
        f"Mode: {result.get('mode')} | Seed: {result.get('seed')} | Weirdness: {result.get('weirdness')}",
        "",
        "Ingredients:",
    ]
    for item in result.get("ingredients", []):
        lines.append(f"- {item.get('category')}: {item.get('text')}")
    lines.extend(["", "Hooks:"])
    for hook in result.get("hooks", []):
        lines.append(f"- {hook}")
    lines.extend(["", "What This Could Become:", str(result.get("expanded_concept") or ""), "", "Scene Or Format Seed:", str(result.get("sketch_seed") or "")])
    next_steps = result.get("next_steps") or []
    if next_steps:
        lines.extend(["", "Next Moves:"])
        for step in next_steps:
            lines.append(f"- {step}")
    lines.extend(["", "WHY THIS HAPPENED"])
    lines.append(str(result.get("collision", {}).get("summary") or "The ingredients sparked."))
    for line in result.get("trace_lines", []):
        lines.append(f"- {line}")
    lines.extend(["", str(result.get("recipe") or "")])
    return "\n".join(lines).strip() + "\n"


def collision_to_html(result: dict[str, Any]) -> str:
    title = html.escape(str(result.get("title") or "Untitled Spark"))
    body = html.escape(collision_to_text(result)).replace("\n", "<br>\n")
    return f"<!doctype html>\n<html><head><meta charset=\"utf-8\"><title>{title}</title></head><body><main>{body}</main></body></html>\n"


def share_card_to_text(result: dict[str, Any]) -> str:
    next_steps = result.get("next_steps") or []
    next_move = str(next_steps[0]) if next_steps else "Pick the strongest hook and make one rough version."
    return "\n".join(
        [
            f"ProMentum Spark: {result.get('title') or 'Untitled Spark'}",
            "",
            f"Best hook: {result.get('best_hook') or ''}",
            f"Next move: {next_move}",
            "",
            str(result.get("recipe") or ""),
        ]
    ).strip() + "\n"


def share_card_to_html(result: dict[str, Any]) -> str:
    title = html.escape(str(result.get("title") or "Untitled Spark"))
    hook = html.escape(str(result.get("best_hook") or ""))
    next_steps = result.get("next_steps") or []
    next_move = html.escape(str(next_steps[0]) if next_steps else "Pick the strongest hook and make one rough version.")
    recipe = html.escape(str(result.get("recipe") or ""))
    mode = html.escape(str(result.get("mode") or "Spark"))
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} - ProMentum Share Card</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, Segoe UI, Arial, sans-serif; }}
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #eef2f1; color: #172026; }}
    main {{ width: min(760px, calc(100vw - 32px)); }}
    article {{ border: 1px solid #d8dee3; border-left: 8px solid #00a8c6; border-radius: 18px; background: #ffffff; box-shadow: 0 18px 44px rgba(23, 32, 38, 0.14); padding: clamp(22px, 5vw, 42px); }}
    .kicker {{ color: #64717b; font-size: 12px; font-weight: 900; letter-spacing: 0.08em; margin: 0 0 10px; text-transform: uppercase; }}
    h1 {{ font-size: clamp(30px, 7vw, 58px); line-height: 1.02; margin: 0; }}
    .hook {{ background: #eefbfe; border-left: 5px solid #00a8c6; border-radius: 12px; font-size: clamp(20px, 4vw, 30px); font-weight: 850; line-height: 1.28; margin: 24px 0 0; padding: 18px; }}
    .move {{ color: #3f4b54; font-size: 18px; font-weight: 750; line-height: 1.45; margin: 18px 0 0; }}
    .recipe {{ border-top: 1px solid #d8dee3; color: #64717b; font-family: Consolas, Courier New, monospace; font-size: 13px; margin: 26px 0 0; padding-top: 16px; overflow-wrap: anywhere; }}
    .brand {{ align-items: center; color: #172026; display: flex; font-weight: 900; gap: 10px; margin-bottom: 18px; }}
    .badge {{ background: #172026; border-radius: 10px; color: #fff; display: inline-grid; min-height: 38px; min-width: 38px; place-items: center; }}
    .mode {{ color: #64717b; font-size: 12px; font-weight: 900; margin-left: auto; text-transform: uppercase; }}
  </style>
</head>
<body>
  <main>
    <article>
      <div class="brand"><span class="badge">PM</span><span>ProMentum</span><span class="mode">{mode}</span></div>
      <p class="kicker">Shareable first move</p>
      <h1>{title}</h1>
      <p class="hook">{hook}</p>
      <p class="move"><strong>Next move:</strong> {next_move}</p>
      <p class="recipe">{recipe}</p>
    </article>
  </main>
</body>
</html>
"""


def project_card_to_text(project: dict[str, Any]) -> str:
    actions = project.get("actions") or []
    readiness_info = project.get("readiness") or {}
    lines = [
        f"ProMentum Project: {project.get('title') or 'Untitled Project'}",
        "",
        f"Traffic light: {readiness_info.get('label') or 'Not marked'}",
        f"Current stage: {project.get('stage') or 'Capture'}",
        "",
        f"Hook: {project.get('best_hook') or ''}",
        "",
        "Do Next:",
    ]
    if actions:
        for action in actions:
            marker = "x" if action.get("done") else " "
            lines.append(f"- [{marker}] {action.get('text') or ''}")
    else:
        lines.append("- [ ] Make one rough version.")
    notes = str(project.get("notes") or "").strip()
    if notes:
        lines.extend(["", "Notes:", notes])
    lines.extend(["", str(project.get("recipe") or "")])
    return "\n".join(lines).strip() + "\n"


def project_card_to_html(project: dict[str, Any]) -> str:
    title = html.escape(str(project.get("title") or "Untitled Project"))
    hook = html.escape(str(project.get("best_hook") or ""))
    stage = html.escape(str(project.get("stage") or "Capture"))
    recipe = html.escape(str(project.get("recipe") or ""))
    readiness_info = project.get("readiness") or {}
    readiness_label = html.escape(str(readiness_info.get("label") or "Not marked"))
    readiness_level = html.escape(str(readiness_info.get("level") or "amber"))
    notes = html.escape(str(project.get("notes") or "")).replace("\n", "<br>\n")
    action_items = []
    for action in project.get("actions") or []:
        done = "done" if action.get("done") else ""
        marker = "Done" if action.get("done") else "Next"
        action_items.append(
            f"<li class=\"{done}\"><span>{html.escape(marker)}</span>{html.escape(str(action.get('text') or ''))}</li>"
        )
    if not action_items:
        action_items.append("<li><span>Next</span>Make one rough version.</li>")
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} - ProMentum Project Card</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, Segoe UI, Arial, sans-serif; }}
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #eef2f1; color: #172026; }}
    main {{ width: min(860px, calc(100vw - 32px)); }}
    article {{ border: 1px solid #d8dee3; border-left: 8px solid #27a367; border-radius: 18px; background: #fff; box-shadow: 0 18px 44px rgba(23, 32, 38, 0.14); padding: clamp(22px, 5vw, 42px); }}
    .brand {{ align-items: center; color: #172026; display: flex; font-weight: 900; gap: 10px; margin-bottom: 18px; }}
    .badge {{ background: #172026; border-radius: 10px; color: #fff; display: inline-grid; min-height: 38px; min-width: 38px; place-items: center; }}
    .stage {{ color: #64717b; font-size: 12px; font-weight: 900; margin-left: auto; text-transform: uppercase; }}
    h1 {{ font-size: clamp(32px, 7vw, 58px); line-height: 1.02; margin: 0; }}
    .light {{ border: 1px solid #d8dee3; border-radius: 999px; display: inline-flex; align-items: center; gap: 9px; font-size: 13px; font-weight: 900; margin: 18px 0 0; padding: 8px 12px; }}
    .dot {{ width: 12px; height: 12px; border-radius: 999px; background: #d79b23; }}
    .dot.green {{ background: #27a367; }} .dot.red {{ background: #d94b4b; }} .dot.amber {{ background: #d79b23; }}
    .hook {{ background: #eefbfe; border-left: 5px solid #00a8c6; border-radius: 12px; font-size: clamp(18px, 3vw, 26px); font-weight: 850; line-height: 1.3; margin: 22px 0 0; padding: 18px; }}
    ul {{ display: grid; gap: 10px; list-style: none; margin: 22px 0 0; padding: 0; }}
    li {{ border: 1px solid #d8dee3; border-radius: 10px; display: grid; grid-template-columns: 74px minmax(0, 1fr); gap: 12px; padding: 12px; }}
    li span {{ color: #64717b; font-size: 11px; font-weight: 900; text-transform: uppercase; }}
    li.done {{ background: #f0fff6; border-color: #beebcd; }}
    .notes {{ color: #3f4b54; font-size: 15px; font-weight: 700; line-height: 1.5; margin: 20px 0 0; }}
    .recipe {{ border-top: 1px solid #d8dee3; color: #64717b; font-family: Consolas, Courier New, monospace; font-size: 13px; margin: 26px 0 0; padding-top: 16px; overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <main>
    <article>
      <div class="brand"><span class="badge">PM</span><span>ProMentum</span><span class="stage">{stage}</span></div>
      <h1>{title}</h1>
      <div class="light"><span class="dot {readiness_level}"></span>{readiness_label}</div>
      <p class="hook">{hook}</p>
      <ul>{"".join(action_items)}</ul>
      {f'<p class="notes">{notes}</p>' if notes else ''}
      <p class="recipe">{recipe}</p>
    </article>
  </main>
</body>
</html>
"""


def _bank_items(state: dict[str, Any]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for key in INGREDIENT_KEYS:
        for text in _clean_list(state.get(key)):
            items.append({"category": key, "text": text})
    if not items:
        items.append({"category": "ideas", "text": "an empty room trying to become a premise"})
    return items


def _select_ingredients(bank: list[dict[str, str]], rng: random.Random, count: int, options: dict[str, Any]) -> list[dict[str, str]]:
    locked = _locked_items(options, bank)
    selected: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in locked:
        key = (item["category"], item["text"])
        if key not in seen:
            selected.append(item)
            seen.add(key)
        if len(selected) >= count:
            return selected

    shuffled = list(bank)
    rng.shuffle(shuffled)
    while len(shuffled) < count * 2:
        shuffled.extend(bank)
    for item in shuffled:
        key = (item["category"], item["text"])
        if key in seen:
            continue
        selected.append(item)
        seen.add(key)
        if len(selected) >= count:
            break
    while len(selected) < count:
        selected.append(dict(bank[len(selected) % len(bank)]))
    return selected


def _locked_items(options: dict[str, Any], bank: list[dict[str, str]]) -> list[dict[str, str]]:
    locked: list[dict[str, str]] = []
    raw_items = options.get("locked_ingredients") or []
    if isinstance(raw_items, list):
        for raw in raw_items:
            if isinstance(raw, dict):
                text = str(raw.get("text") or "").strip()
                category = str(raw.get("category") or "ideas").strip()
            else:
                text = str(raw).strip()
                category = "ideas"
            if text:
                locked.append({"category": category if category in INGREDIENT_KEYS else "ideas", "text": text})
    locked_text = str(options.get("locked_text") or "").strip()
    if locked_text:
        match = next((item for item in bank if item["text"] == locked_text), None)
        locked.append(dict(match or {"category": "ideas", "text": locked_text}))
    return locked


def _trace_for(item: dict[str, str], index: int, seed: int, weirdness: int) -> dict[str, Any]:
    prime = PRIMES[(seed + index + len(item["text"])) % len(PRIMES)]
    current = (seed + len(item["category"]) + len(item["text"])) % prime
    steps = []
    for step in range(7):
        current = (current * (step + 3) + weirdness + len(item["text"]) + index) % prime
        steps.append(current)
    return {
        "prime": prime,
        "seed": current,
        "steps": steps,
        "midpoint": steps[3],
        "signature": f"Z{prime}:{steps[0]}->{steps[-1]}",
    }


def _drift_item(item: dict[str, str], trace: dict[str, Any], rng: random.Random, weirdness: int) -> dict[str, Any]:
    drift_index = (trace["steps"][-1] + weirdness + len(item["category"])) % len(DRIFTS)
    drift = DRIFTS[drift_index]
    return {
        **item,
        "drift": drift,
        "trace": trace,
        "angle": _angle_for(item["text"], drift, rng),
    }


def _resolve_collision(items: list[dict[str, Any]], traces: list[dict[str, Any]], rng: random.Random, weirdness: int, mode: str) -> dict[str, Any]:
    midpoint = sum(trace["midpoint"] for trace in traces) % 97
    collision_type = COLLISIONS[(midpoint + weirdness + len(mode)) % len(COLLISIONS)]
    first_item, second_item, _ = _narrative_items(items)
    first = _present(first_item)
    second = _present(second_item)
    summary = f"{collision_type}: {first} is forced to explain itself through {second}."
    if mode == "Title Storm":
        summary = f"{collision_type}: the spark becomes a naming problem with consequences."
    elif mode == "Personal Myth":
        summary = f"{collision_type}: a private thought gets promoted into folklore."
    elif mode == "Serious To Absurd":
        summary = f"{collision_type}: the sensible version is pushed until it starts wobbling."
    return {"type": collision_type, "midpoint": midpoint, "summary": summary, "turn": rng.choice(["quietly", "publicly", "by accident", "with paperwork"])}


def _make_title(items: list[dict[str, Any]], rng: random.Random, mode: str) -> str:
    lead, _, tail = _narrative_items(items)
    lead_piece = _short_title_piece(lead["text"])
    tail_piece = _short_title_piece(tail["text"])
    if mode == "Title Storm":
        return f"{rng.choice(['Seven Titles For', 'The Unauthorized Names Of', 'Working Titles For'])} {lead_piece.title()}"
    if mode == "Personal Myth":
        return f"The Small Myth Of {lead_piece.title()}"
    if mode == "Serious To Absurd":
        return f"The Very Official Case For {lead_piece.title()}"
    if mode == "Video Idea":
        return f"POV: {tail_piece.title()} Has Entered The Chat"
    return f"{lead_piece.title()} Meets {tail_piece.title()}"


def _make_hooks(items: list[dict[str, Any]], collision: dict[str, Any], rng: random.Random, mode: str, weirdness: int) -> list[str]:
    lead, hinge, tail = _narrative_items(items)
    a = _present(lead)
    b = _present(tail)
    c = _present(hinge)
    templates = {
        "Sketch Hook": [
            "A sketch where {a} only wants one normal minute, but {b} keeps making it official.",
            "{a} walks into {b}, and the room immediately pretends this was scheduled.",
            "The bit starts tiny: {c}. By the end, {a} has a committee."
        ],
        "Video Idea": [
            "Open on {a}. Smash cut to {b} being treated like breaking news.",
            "A 45-second escalation from {c} to {a}, ending with one very confident rule.",
            "POV: {b} has become the main character and {a} is taking minutes."
        ],
        "Title Storm": [
            "{a}: A Field Guide To Bad Decisions",
            "Please Stop Giving {b} Authority",
            "The {c} Incident, Explained By Nobody Qualified",
            "Minutes From The Day {a} Became Everyone's Problem"
        ],
        "Scene Seed": [
            "Scene starts with {a}; the interruption is {b}; the lie is that everyone expected this.",
            "Put {c} in the room first, then let {a} enter with the wrong emotional weather.",
            "The scene ends when {b} repeats the first line like a legal ruling."
        ],
        "Personal Myth": [
            "Treat {a} as a tiny household myth: it wants tribute, witnesses, and a bad drawing.",
            "{c} becomes the symbol. {b} becomes the rule nobody remembers agreeing to.",
            "A private annoyance turns into folklore when {a} refuses to remain practical."
        ],
        "Serious To Absurd": [
            "Start with the sensible case for {a}, then keep proving it until {b} becomes unavoidable.",
            "{c} is the reasonable version. The absurd version gives it a uniform.",
            "Explain {a} like a serious policy, then reveal the policy was written by {b}."
        ],
        "Concept Mashup": [
            "Combine {a} with {b}, but make {c} the emotional hinge.",
            "{a} supplies the premise, {b} supplies the trouble, and {c} supplies the first laugh.",
            "The spark works if {a} wants status and {b} wants snacks.",
            "Pitch it as {a} behaving like a tool, then reveal {b} is the real motive."
        ],
    }
    pool = templates.get(mode, templates["Concept Mashup"])
    hooks = [template.format(a=a, b=b, c=c) for template in rng.sample(pool, k=min(3, len(pool)))]
    if mode == "Title Storm":
        hooks.append(f"The Day {a.title()} Became Everyone's Problem")
    elif weirdness > 75:
        hooks.append(f"Escalate it until {collision['type']} feels like the only sane outcome.")
    else:
        hooks.append(f"Keep it grounded: one human wants something simple, and {b} gets in the way.")
    return hooks


def _choose_best_hook(hooks: list[str], mode: str, weirdness: int) -> str:
    def score(hook: str) -> int:
        length = len(hook)
        length_score = 50 - abs(135 - length)
        action_score = sum(10 for word in ["walks", "open", "combine", "treat", "explain", "starts", "pitch"] if word.lower() in hook.lower())
        penalty = 20 if hook.count("'") > 4 else 0
        if hook.startswith("Keep it grounded"):
            penalty += 35
        mode_bonus = 12 if mode.split()[0].lower() in hook.lower() else 0
        if mode == "Title Storm" and any(mark in hook for mark in [":", "Please Stop", "Field Guide", "Unauthorized", "Working Titles", "Everyone's Problem"]):
            mode_bonus += 30
        weird_bonus = 8 if weirdness > 70 and any(word in hook.lower() for word in ["official", "authority", "committee", "ritual"]) else 0
        return length_score + action_score + mode_bonus + weird_bonus - penalty

    return sorted(hooks, key=score, reverse=True)[0]


def _expand_concept(items: list[dict[str, Any]], collision: dict[str, Any], rng: random.Random, mode: str, best_hook: str) -> str:
    lead_item, hinge_item, tail_item = _narrative_items(items)
    lead = _present(lead_item)
    hinge = _present(hinge_item)
    tail = _present(tail_item)
    mode_openers = {
        "Sketch Hook": "This should play like a clean sketch premise: one person tries to keep the day ordinary while the room votes against them.",
        "Video Idea": "This wants to be fast: a visual opening, one caption-sized premise, then a turn before anyone can over-explain it.",
        "Title Storm": "This is mostly a naming engine: the title should sound like it belongs to a project that got out of hand.",
        "Scene Seed": "This is a scene starter: give the first character a practical need and let the second ingredient interrupt it.",
        "Personal Myth": "This works best when the feeling is tiny but the treatment is ceremonial.",
        "Serious To Absurd": "Start sensible and keep adding evidence until the sensible argument becomes the joke.",
        "Concept Mashup": "The strongest version keeps one emotional motive underneath the strange mechanics.",
    }
    return (
        f"{mode_openers.get(mode, mode_openers['Concept Mashup'])} {best_hook} "
        f"{_pressure_line(lead, hinge, tail, mode)} "
        f"The first beat should feel practical. The second beat should misread the first. "
        f"The final beat should callback the opening as if the whole spark was obvious from the start."
    )


def _make_sketch_seed(items: list[dict[str, Any]], collision: dict[str, Any], rng: random.Random, mode: str) -> str:
    lead, _, tail = _narrative_items(items)
    opening = rng.choice(["Cold open", "First line", "Thumbnail", "Opening image"])
    callback = _present(tail)
    return f"{opening}: {_present(lead)}. Turn: {collision['summary']} Callback: bring back {callback} as the last proof."


def _trace_lines(traces: list[dict[str, Any]], items: list[dict[str, Any]], collision: dict[str, Any]) -> list[str]:
    lines = []
    for item in items:
        trace = item["trace"]
        lines.append(
            f"{item['category']} drifted by {item['drift']} in Z{trace['prime']} with trace {trace['steps']} ({trace['signature']})"
        )
    lines.append(f"Spark resolved as {collision['type']} at midpoint {collision['midpoint']}.")
    return lines


def _make_next_steps(items: list[dict[str, Any]], mode: str, rng: random.Random) -> list[str]:
    steps = list(MODE_NEXT_STEPS.get(mode, MODE_NEXT_STEPS["Concept Mashup"]))
    anchor = _present(_choose_best_ingredient(items))
    insert_at = rng.randrange(0, len(steps) + 1)
    steps.insert(insert_at, f"Keep {anchor} visible; it is the strongest anchor.")
    return steps[:4]


def _choose_best_ingredient(items: list[dict[str, Any]]) -> dict[str, Any]:
    priority = {"ideas": 7, "people": 6, "phrases": 6, "places": 5, "questions": 4, "obsessions": 4, "rules": 3, "formats": 2}

    def score(item: dict[str, Any]) -> int:
        trace = item.get("trace") or {}
        steps = trace.get("steps") or [0]
        return priority.get(str(item.get("category")), 1) * 10 + int(steps[-1])

    return sorted(items, key=score, reverse=True)[0]


def _narrative_items(items: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if not items:
        fallback = {"category": "ideas", "text": "an empty room trying to become a premise"}
        return fallback, fallback, fallback
    lead_priority = {"ideas": 8, "people": 7, "places": 6, "phrases": 6, "questions": 5, "obsessions": 4, "rules": 2, "formats": 1}
    tail_priority = {"phrases": 8, "rules": 7, "questions": 6, "obsessions": 5, "ideas": 4, "places": 4, "people": 3, "formats": 2}

    lead = sorted(items, key=lambda item: (lead_priority.get(str(item.get("category")), 0), len(str(item.get("text") or ""))), reverse=True)[0]
    remaining = [item for item in items if item is not lead]
    if not remaining:
        return lead, lead, lead
    tail = sorted(remaining, key=lambda item: (tail_priority.get(str(item.get("category")), 0), len(str(item.get("text") or ""))), reverse=True)[0]
    middle_pool = [item for item in remaining if item is not tail] or remaining
    hinge = sorted(middle_pool, key=lambda item: abs(len(str(item.get("text") or "")) - 42))[0]
    return lead, hinge, tail


def _angle_for(text: str, drift: str, rng: random.Random) -> str:
    if drift == "invert":
        return f"What if the opposite of '{text}' was the useful part?"
    if drift == "literalize":
        return f"Treat '{text}' as physically present in the room."
    if drift == "make official":
        return f"Give '{text}' a form, a witness, and an unnecessary title."
    if drift == "misremember":
        return f"Remember '{text}' slightly wrong and defend the mistake."
    return f"Let '{text}' push the next ingredient {rng.choice(['sideways', 'uphill', 'into public view'])}."


def _present(item: dict[str, Any]) -> str:
    text = _strip_sentence(str(item.get("text") or "an idea"))
    category = str(item.get("category") or "")
    lowered = text[:1].lower() + text[1:]
    if category == "rules":
        return _rule_phrase(lowered)
    if category == "questions":
        return f"the question '{text}'"
    if category == "formats":
        return f"the {lowered} format"
    if category == "obsessions":
        return f"an obsession with {lowered}"
    if category == "phrases":
        return f"the phrase '{text}'"
    return lowered


def _strip_sentence(text: str) -> str:
    return text.strip().rstrip(".!?").strip()


def _pressure_line(lead: str, hinge: str, tail: str, mode: str) -> str:
    if mode == "Video Idea":
        return f"The first image is {lead}; {hinge} is the turn, and {tail} is the thing people remember."
    if mode == "Title Storm":
        return f"The title should make {lead} sound official, while {tail} keeps it from becoming too clean."
    if mode == "Personal Myth":
        return f"The feeling sits inside {lead}; {hinge} gives it a witness, and {tail} gives it a ritual shape."
    if mode == "Serious To Absurd":
        return f"The sensible argument starts with {lead}; {hinge} supplies evidence, then {tail} makes the logic wobble."
    if mode == "Scene Seed":
        return f"Let {lead} enter with a normal objective, then use {tail} to make the room misunderstand the objective."
    if mode == "Sketch Hook":
        return f"{lead} wants a normal beat, {hinge} gives the room a motive, and {tail} turns the beat into the problem."
    return f"The useful pressure is between {lead} and {tail}; {hinge} is the human reason it does not fall apart."


def _rule_phrase(text: str) -> str:
    mappings = [
        ("treat one ordinary object", "the ordinary-object authority rule"),
        ("make the sensible person", "the sensible-person-escalates rule"),
        ("give the smallest phrase", "the small-phrase big-consequence rule"),
        ("let one idea misunderstand", "the confident-misunderstanding rule"),
        ("end with a callback", "the inevitable-callback rule"),
        ("turn a private thought", "the public-ceremony rule"),
        ("make a practical task", "the practical-task-becomes-myth rule"),
        ("keep the first move", "the keep-it-human rule"),
    ]
    for prefix, label in mappings:
        if text.startswith(prefix):
            return label
    if text.startswith(("make ", "treat ", "give ", "let ", "end ", "turn ", "keep ")):
        return f"the rule to {text}"
    return f"a rule that {text}"


def _short_title_piece(text: str) -> str:
    stopwords = {
        "the", "and", "that", "with", "where", "into", "who", "every", "your", "from", "this", "only",
        "over", "under", "about", "like", "what", "when", "why", "how", "for", "has", "was", "were", "are",
        "make", "let", "give", "treat", "keep", "turn", "end",
    }
    words = [word.strip(".,:;!?()[]{}\"'").lower() for word in text.split()]
    words = [word for word in words if len(word) > 2 and word not in stopwords]
    return " ".join(words[:4]) or text[:32]


def _clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _coerce_seed(value: Any) -> int:
    if value in (None, ""):
        return int(time.time() * 1000) % 1_000_000_000
    try:
        return abs(int(str(value).strip())) % 1_000_000_000
    except ValueError:
        return abs(hash(str(value))) % 1_000_000_000


def _clamp_int(value: Any, low: int, high: int, fallback: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = fallback
    return max(low, min(high, number))
