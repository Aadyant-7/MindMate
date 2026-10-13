"""Portable resources and local files for the original desktop application."""

import json
import os
from pathlib import Path
import re
import sys
import tempfile
from datetime import datetime


def resource_root():
    # PyInstaller extracts the same Assets folder beside the bundled modules.
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def asset_path(relative_path):
    return (resource_root() / "Assets" / relative_path).as_posix()


def asset_stylesheet(stylesheet):
    """Resolve the original image styles, including paths containing spaces."""
    def resolve(match):
        relative = match.group(1).strip().strip("\"'")
        if not relative.startswith("Assets/"):
            return match.group(0)
        return 'url("' + asset_path(relative[len("Assets/"):]) + '")'

    return re.sub(r"url\((.*?)\)", resolve, stylesheet)


def data_dir():
    override = os.environ.get("MINDMATE_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "MindMate"


def journals_dir():
    directory = data_dir() / "Your Journals"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_journal(text, now=None):
    text = text.strip()
    if not text:
        raise ValueError("Write something before saving your journal.")
    now = now or datetime.now()
    timestamp = now.strftime("%A, %d %B %Y (%I:%M %p)")
    directory = journals_dir()
    index = 1
    while True:
        path = directory / f"journal{index}.txt"
        created = False
        try:
            with path.open("x", encoding="utf-8") as stream:
                created = True
                stream.write(f"{timestamp}\n\n{text}\n")
            return path
        except FileExistsError:
            index += 1
        except OSError:
            # A partial entry should not appear to have been saved successfully.
            if created and path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass
            raise


def load_settings():
    path = data_dir() / "settings.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as stream:
        settings = json.load(stream)
    if not isinstance(settings, dict):
        raise ValueError("The local settings file is invalid. Open Chat settings to replace it.")
    return {key: value for key, value in settings.items()
            if key in {"api_key", "model"} and isinstance(value, str)}


def save_settings(settings):
    directory = data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "settings.json"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                         prefix="settings-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(settings, stream, indent=2)
            stream.write("\n")
        temporary.replace(target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
