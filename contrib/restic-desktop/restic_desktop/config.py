# SPDX-License-Identifier: BSD-2-Clause
"""Configuración persistente del repositorio."""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "restic-desktop"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    with CONFIG_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def save(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_repository() -> str | None:
    return load().get("repository") or None


def set_repository(repo: str) -> None:
    data = load()
    data["repository"] = repo
    save(data)


def get_backup_paths() -> list[str]:
    return load().get("backup_paths", [])


def set_backup_paths(paths: list[str]) -> None:
    data = load()
    data["backup_paths"] = paths
    save(data)
