from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any

from .engine import (
    INGREDIENT_KEYS,
    collision_to_html,
    collision_to_text,
    project_card_to_html,
    project_card_to_text,
    progress_log_to_text,
    readiness,
    share_card_to_html,
    today_plan_to_text,
)


APP_NAME = "ProMentum"
PROJECT_STAGES = ["Spark", "Shaping", "First Step", "In Progress", "Parked", "Done"]
LEGACY_STAGE_MAP = {
    "capture": "Spark",
    "generate": "Spark",
    "choose": "Spark",
    "shape": "Shaping",
    "do next": "First Step",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def app_data_dir() -> Path:
    override = os.getenv("PROMENTUM_HOME") or os.getenv("IDEA_COLLIDER_HOME")
    if override:
        root = Path(override).expanduser()
    else:
        root = _default_data_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _default_data_root() -> Path:
    if os.name == "nt":
        preferred = [
            Path("D:/ProMentumData"),
            Path("D:/ProMentumDataLocal"),
            repo_root() / "promentum_data",
            repo_root() / "idea_collider_data",
        ]
    else:
        preferred = [repo_root() / "promentum_data", repo_root() / "idea_collider_data"]
    for candidate in preferred:
        if _ensure_path(candidate):
            return candidate
    return repo_root() / "idea_collider_data"


def _ensure_path(candidate: Path) -> bool:
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def exports_dir() -> Path:
    path = app_data_dir() / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_state_path() -> Path:
    return repo_root() / "idea_collider_app" / "seeds" / "default_idea_bank.json"


def user_state_path() -> Path:
    return app_data_dir() / "idea_bank.json"


def favourites_path() -> Path:
    return app_data_dir() / "favourites.json"


def projects_path() -> Path:
    return app_data_dir() / "projects.json"


def load_default_state() -> dict[str, Any]:
    return _read_json(default_state_path(), fallback={})


def load_state() -> dict[str, Any]:
    path = user_state_path()
    if not path.exists():
        state = load_default_state()
        save_state(state)
        return state
    state = _read_json(path, fallback=None)
    if not isinstance(state, dict):
        _backup_broken(path)
        state = load_default_state()
        save_state(state)
    return _normalize_state(state)


def save_state(state: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_state(state)
    _write_json(user_state_path(), normalized)
    return normalized


def reset_state() -> dict[str, Any]:
    state = load_default_state()
    save_state(state)
    return state


def blank_state() -> dict[str, Any]:
    return {"version": 1, "bank_name": "Blank Spark Bank", **{key: [] for key in INGREDIENT_KEYS}}


def reset_blank_state() -> dict[str, Any]:
    state = blank_state()
    save_state(state)
    return state


def state_payload() -> dict[str, Any]:
    state = load_state()
    return {"state": state, "readiness": readiness(state)}


def list_favourites() -> list[dict[str, Any]]:
    data = _read_json(favourites_path(), fallback=[])
    return data if isinstance(data, list) else []


def save_favourite(result: dict[str, Any]) -> dict[str, Any]:
    favourites = list_favourites()
    item = {
        "id": f"fav-{int(time.time() * 1000)}",
        "title": str(result.get("title") or "Untitled Spark"),
        "best_hook": str(result.get("best_hook") or ""),
        "seed": result.get("seed"),
        "mode": result.get("mode"),
        "created_at": result.get("created_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "result": result,
    }
    favourites.insert(0, item)
    _write_json(favourites_path(), favourites[:100])
    return item


def delete_favourite(favourite_id: str) -> bool:
    favourites = list_favourites()
    original = len(favourites)
    filtered = [item for item in favourites if str(item.get("id")) != str(favourite_id)]
    if len(filtered) == original:
        return False
    _write_json(favourites_path(), filtered)
    return True


def clear_favourites() -> None:
    _write_json(favourites_path(), [])


def list_projects() -> list[dict[str, Any]]:
    data = _read_json(projects_path(), fallback=[])
    if not isinstance(data, list):
        return []
    return [_normalize_project(item) for item in data if isinstance(item, dict)]


def today_plan(projects: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    project_list = projects if projects is not None else list_projects()
    candidates = []
    for project in project_list:
        if project.get("stage") == "Done":
            continue
        open_action = next((action for action in project.get("actions", []) if not action.get("done")), None)
        if not open_action:
            continue
        readiness_info = project.get("readiness") or project_readiness(project)
        stage = str(project.get("stage") or "Spark")
        level = str(readiness_info.get("level") or "amber")
        candidates.append(
            {
                "score": _today_score(stage, level, project),
                "project": project,
                "action": open_action,
                "readiness": readiness_info,
            }
        )
    if not candidates:
        return {
            "has_action": False,
            "project_count": len(project_list),
            "message": _today_empty_message(project_list),
            "recommendation": _today_empty_recommendation(project_list),
        }
    chosen = sorted(candidates, key=lambda item: item["score"], reverse=True)[0]
    project = chosen["project"]
    action = chosen["action"]
    readiness_info = chosen["readiness"]
    return {
        "has_action": True,
        "project_count": len(project_list),
        "project_id": project.get("id"),
        "project_title": project.get("title"),
        "project_stage": project.get("stage"),
        "readiness": readiness_info,
        "action": action,
        "steps": [
            "Open only what this action needs.",
            "Work for ten honest minutes.",
            "Log one win or one blocker before moving on.",
        ],
        "message": f"Do this next: {action.get('text')}",
    }


def save_project_from_result(result: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    project = {
        "id": f"project-{int(time.time() * 1000)}",
        "title": str(payload.get("title") or result.get("title") or "Untitled Project"),
        "best_hook": str(result.get("best_hook") or ""),
        "mode": result.get("mode"),
        "seed": result.get("seed"),
        "weirdness": result.get("weirdness"),
        "stage": str(payload.get("stage") or "Spark"),
        "readiness_level": str(payload.get("readiness_level") or "amber"),
        "notes": str(payload.get("notes") or ""),
        "blockers": _normalize_text_items(payload.get("blockers") or []),
        "wins": _normalize_text_items(payload.get("wins") or []),
        "history": [
            {
                "id": f"history-{int(time.time() * 1000)}",
                "kind": "created",
                "text": "Project saved from a generated spark.",
                "created_at": now,
            }
        ],
        "recipe": str(result.get("recipe") or ""),
        "actions": _actions_from_result(result, payload.get("actions")),
        "source_result": result,
        "created_at": now,
        "updated_at": now,
    }
    projects = list_projects()
    normalized = _normalize_project(project)
    projects.insert(0, normalized)
    _write_json(projects_path(), projects[:100])
    return normalized


def save_project(project: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_project(project)
    normalized["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    projects = list_projects()
    replaced = False
    for index, existing in enumerate(projects):
        if str(existing.get("id")) == str(normalized.get("id")):
            projects[index] = normalized
            replaced = True
            break
    if not replaced:
        projects.insert(0, normalized)
    _write_json(projects_path(), projects[:100])
    return normalized


def delete_project(project_id: str) -> bool:
    projects = list_projects()
    filtered = [item for item in projects if str(item.get("id")) != str(project_id)]
    if len(filtered) == len(projects):
        return False
    _write_json(projects_path(), filtered)
    return True


def clear_projects() -> None:
    _write_json(projects_path(), [])


def export_project(project: dict[str, Any], export_format: str = "project-card") -> dict[str, Any]:
    normalized = _normalize_project(project)
    requested = str(export_format or "project-card").lower()
    if requested in {"today", "today-plan", "plan"}:
        content = today_plan_to_text(normalized)
        extension = "txt"
        export_format = "today-plan"
        suffix = "-today-plan"
    elif requested in {"progress", "progress-log", "log"}:
        content = progress_log_to_text(normalized)
        extension = "txt"
        export_format = "progress-log"
        suffix = "-progress-log"
    elif requested in {"txt", "text", "brief", "project-brief"}:
        content = project_card_to_text(normalized)
        extension = "txt"
        export_format = "project-brief"
        suffix = "-project-brief"
    else:
        content = project_card_to_html(normalized)
        extension = "html"
        export_format = "project-card"
        suffix = "-project-card"
    stem = _slugify(str(normalized.get("title") or "promentum-project"))[:70] or "promentum-project"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = exports_dir() / f"{stamp}-{stem}{suffix}.{extension}"
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "format": export_format, "title": normalized.get("title")}


def export_result(result: dict[str, Any], export_format: str = "txt") -> dict[str, Any]:
    requested_format = str(export_format).lower()
    if requested_format in {"share", "share-card", "card"}:
        export_format = "share"
        extension = "html"
    elif requested_format == "html":
        export_format = "html"
        extension = "html"
    else:
        export_format = "txt"
        extension = "txt"
    title = str(result.get("title") or "promentum-result")
    stem = _slugify(title)[:70] or "promentum-result"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    suffix = "-share-card" if export_format == "share" else ""
    path = exports_dir() / f"{stamp}-{stem}{suffix}.{extension}"
    if export_format == "share":
        content = share_card_to_html(result)
    elif export_format == "html":
        content = collision_to_html(result)
    else:
        content = collision_to_text(result)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "format": export_format, "title": title}


def open_data_folder(opener: Any | None = None) -> dict[str, Any]:
    path = app_data_dir().resolve()
    try:
        if os.getenv("IDEA_COLLIDER_DISABLE_OPEN") == "1":
            return {"opened": False, "path": str(path), "error": "Opening folders is disabled for this run."}
        if opener:
            opener(path)
        elif os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return {"opened": True, "path": str(path)}
    except (OSError, RuntimeError) as exc:
        return {"opened": False, "path": str(path), "error": str(exc)}


def open_exports_folder(opener: Any | None = None) -> dict[str, Any]:
    path = exports_dir().resolve()
    try:
        if os.getenv("IDEA_COLLIDER_DISABLE_OPEN") == "1":
            return {"opened": False, "path": str(path), "error": "Opening folders is disabled for this run."}
        if opener:
            opener(path)
        elif os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return {"opened": True, "path": str(path)}
    except (OSError, RuntimeError) as exc:
        return {"opened": False, "path": str(path), "error": str(exc)}


def doctor() -> dict[str, Any]:
    state = load_state()
    projects = list_projects()
    return {
        "data_dir": str(app_data_dir()),
        "state_path": str(user_state_path()),
        "favourites_path": str(favourites_path()),
        "projects_path": str(projects_path()),
        "exports_dir": str(exports_dir()),
        "state_ok": bool(sum(len(state.get(key, [])) for key in INGREDIENT_KEYS)),
        "readiness": readiness(state),
        "favourite_count": len(list_favourites()),
        "project_count": len(projects),
        "project_stage_counts": _stage_counts(projects),
        "today": today_plan(projects),
        "portable_default": str(repo_root() / "promentum_data"),
    }


def _stage_counts(projects: list[dict[str, Any]]) -> dict[str, int]:
    counts = {stage: 0 for stage in PROJECT_STAGES}
    for project in projects:
        stage = _normalize_stage(project.get("stage"))
        counts[stage] = counts.get(stage, 0) + 1
    return counts


def _normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    default = load_default_state()
    normalized = dict(default)
    if isinstance(state, dict):
        normalized.update(state)
    for key in INGREDIENT_KEYS:
        normalized[key] = _normalize_lines(normalized.get(key), [])
    normalized["version"] = int(normalized.get("version") or 1)
    normalized["bank_name"] = str(normalized.get("bank_name") or "Spark Bank")
    return normalized


def _normalize_lines(value: Any, fallback: Any) -> list[str]:
    source = value if isinstance(value, list) else fallback
    return [str(item).strip() for item in source if str(item).strip()]


def _actions_from_result(result: dict[str, Any], override: Any = None) -> list[dict[str, Any]]:
    if isinstance(override, list) and override:
        return _normalize_actions(override)
    raw_steps = result.get("next_steps") or []
    steps = [str(step).strip() for step in raw_steps if str(step).strip()]
    if not steps:
        steps = ["Make one rough version.", "Show it to one person.", "Decide the next tiny move."]
    if len(steps) < 3:
        steps.append("Make one rough version.")
    return _normalize_actions([{"text": step, "done": False} for step in steps[:5]])


def _normalize_project(project: dict[str, Any]) -> dict[str, Any]:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    source_result = project.get("source_result") if isinstance(project.get("source_result"), dict) else {}
    title = str(project.get("title") or source_result.get("title") or "Untitled Project").strip()
    raw_readiness = project.get("readiness") if isinstance(project.get("readiness"), dict) else {}
    readiness_level = str(project.get("readiness_level") or raw_readiness.get("level") or "amber").lower()
    if readiness_level not in {"red", "amber", "green"}:
        readiness_level = "amber"
    actions = _normalize_actions(project.get("actions") or [])
    normalized = {
        "id": str(project.get("id") or f"project-{int(time.time() * 1000)}"),
        "title": title or "Untitled Project",
        "best_hook": str(project.get("best_hook") or source_result.get("best_hook") or ""),
        "mode": project.get("mode") or source_result.get("mode"),
        "seed": project.get("seed") if project.get("seed") is not None else source_result.get("seed"),
        "weirdness": project.get("weirdness") if project.get("weirdness") is not None else source_result.get("weirdness"),
        "stage": _normalize_stage(project.get("stage")),
        "readiness_level": readiness_level,
        "notes": str(project.get("notes") or ""),
        "blockers": _normalize_text_items(project.get("blockers") or []),
        "wins": _normalize_text_items(project.get("wins") or []),
        "history": _normalize_history(project.get("history") or []),
        "recipe": str(project.get("recipe") or source_result.get("recipe") or ""),
        "actions": actions,
        "source_result": source_result,
        "created_at": str(project.get("created_at") or now),
        "updated_at": str(project.get("updated_at") or now),
    }
    normalized["readiness"] = project_readiness(normalized)
    return normalized


def _normalize_actions(actions: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    source = actions if isinstance(actions, list) else []
    for index, action in enumerate(source):
        if isinstance(action, dict):
            text = str(action.get("text") or "").strip()
            done = bool(action.get("done"))
            action_id = str(action.get("id") or f"action-{index + 1}")
        else:
            text = str(action).strip()
            done = False
            action_id = f"action-{index + 1}"
        if text:
            normalized.append({"id": action_id, "text": text, "done": done})
    return normalized[:12]


def _normalize_text_items(items: Any) -> list[str]:
    source = items if isinstance(items, list) else []
    normalized = []
    seen = set()
    for item in source:
        text = str(item.get("text") if isinstance(item, dict) else item).strip()
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        normalized.append(text)
    return normalized[:20]


def _normalize_history(items: Any) -> list[dict[str, str]]:
    source = items if isinstance(items, list) else []
    normalized: list[dict[str, str]] = []
    for index, item in enumerate(source):
        if isinstance(item, dict):
            text = str(item.get("text") or "").strip()
            kind = str(item.get("kind") or "note").strip().lower()
            created_at = str(item.get("created_at") or "").strip()
            history_id = str(item.get("id") or f"history-{index + 1}")
        else:
            text = str(item).strip()
            kind = "note"
            created_at = ""
            history_id = f"history-{index + 1}"
        if not text:
            continue
        if kind not in {"created", "done", "win", "blocker", "note", "parked", "stage"}:
            kind = "note"
        normalized.append({"id": history_id, "kind": kind, "text": text, "created_at": created_at})
    return normalized[:80]


def _normalize_stage(value: Any) -> str:
    text = str(value or "Spark").strip().lower()
    if text in LEGACY_STAGE_MAP:
        return LEGACY_STAGE_MAP[text]
    allowed = PROJECT_STAGES
    for stage in allowed:
        if text == stage.lower():
            return stage
    return "Spark"


def project_readiness(project: dict[str, Any]) -> dict[str, Any]:
    actions = project.get("actions") or []
    blockers = _normalize_text_items(project.get("blockers") or [])
    total = len(actions)
    done = sum(1 for action in actions if action.get("done"))
    level = str(project.get("readiness_level") or "amber").lower()
    if level not in {"red", "amber", "green"}:
        level = "amber"
    labels = {"red": "Blocked", "amber": "Needs shaping", "green": "Ready to do"}
    stage = str(project.get("stage") or "Spark")
    next_action = "Add one small action."
    if stage == "Done":
        next_action = "Project is done. Pick another saved project when you want to move again."
    elif stage == "Parked":
        next_action = blockers[0] if blockers else "Parked. Write the blocker before restarting."
    elif blockers and level == "red":
        next_action = f"Resolve blocker: {blockers[0]}"
    elif total:
        next_open = next((action.get("text") for action in actions if not action.get("done")), "")
        if next_open:
            next_action = str(next_open)
        else:
            next_action = "All listed actions are ticked. Choose the next project move."
    return {
        "level": level,
        "label": labels[level],
        "done": done,
        "total": total,
        "next_action": next_action,
    }


def _today_score(stage: str, level: str, project: dict[str, Any]) -> int:
    stage_score = {"First Step": 70, "In Progress": 65, "Shaping": 45, "Spark": 35, "Parked": 10, "Done": -100}
    level_score = {"green": 25, "amber": 12, "red": -8}
    open_actions = sum(1 for action in project.get("actions", []) if not action.get("done"))
    return stage_score.get(stage, 25) + level_score.get(level, 0) + min(open_actions, 5)


def _today_empty_message(projects: list[dict[str, Any]]) -> str:
    if not projects:
        return "No project yet. Generate a first move, then save it as a Momentum project."
    if all(project.get("stage") == "Done" for project in projects):
        return "All saved projects are done. Start a fresh spark when you want the next thing."
    return "No open action found. Add one tiny action to a project."


def _today_empty_recommendation(projects: list[dict[str, Any]]) -> str:
    if not projects:
        return "Generate First Move"
    return "Open Momentum"


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _backup_broken(path: Path) -> None:
    try:
        shutil.copy2(path, path.with_suffix(f".broken-{int(time.time())}.json"))
    except OSError:
        pass


def _slugify(value: str) -> str:
    value = value.lower()
    value = "".join(ch if ch.isalnum() else "-" for ch in value)
    while "--" in value:
        value = value.replace("--", "-")
    return value.strip("-")
