from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any

from .engine import INGREDIENT_KEYS, collision_to_html, collision_to_text, readiness


APP_NAME = "ProMentum"


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


def export_result(result: dict[str, Any], export_format: str = "txt") -> dict[str, Any]:
    export_format = "html" if str(export_format).lower() == "html" else "txt"
    title = str(result.get("title") or "promentum-result")
    stem = _slugify(title)[:70] or "promentum-result"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = exports_dir() / f"{stamp}-{stem}.{export_format}"
    content = collision_to_html(result) if export_format == "html" else collision_to_text(result)
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
    return {
        "data_dir": str(app_data_dir()),
        "state_path": str(user_state_path()),
        "favourites_path": str(favourites_path()),
        "exports_dir": str(exports_dir()),
        "state_ok": bool(sum(len(state.get(key, [])) for key in INGREDIENT_KEYS)),
        "readiness": readiness(state),
        "favourite_count": len(list_favourites()),
        "portable_default": str(repo_root() / "promentum_data"),
    }


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
