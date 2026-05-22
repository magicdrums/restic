# SPDX-License-Identifier: BSD-2-Clause
"""Ejecución de restic vía subproceso y salida JSON."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any


class ResticError(Exception):
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


@dataclass
class BackupProgress:
    percent_done: float = 0.0
    files_done: int = 0
    total_files: int = 0
    bytes_done: int = 0
    total_bytes: int = 0
    current_files: list[str] | None = None


@dataclass
class BackupSummary:
    snapshot_id: str
    files_new: int = 0
    files_changed: int = 0
    data_added: int = 0
    total_duration: float = 0.0


def find_restic() -> str:
    path = shutil.which("restic")
    if path:
        return path
    raise ResticError(
        "No se encontró el comando 'restic'. Instálalo con: sudo dnf install restic",
        exit_code=127,
    )


def _env(repository: str, password: str) -> dict[str, str]:
    env = os.environ.copy()
    env["RESTIC_REPOSITORY"] = repository
    env["RESTIC_PASSWORD"] = password
    return env


def _run(
    repository: str,
    password: str,
    args: list[str],
    *,
    json_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    cmd = [find_restic()]
    if json_output:
        cmd.append("--json")
    cmd.extend(args)
    result = subprocess.run(
        cmd,
        env=_env(repository, password),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        msg = _parse_exit_error(result.stderr) or result.stderr.strip() or result.stdout.strip()
        raise ResticError(msg or f"restic falló (código {result.returncode})", result.returncode)
    return result


def _parse_exit_error(stderr: str) -> str | None:
    for line in stderr.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("message_type") == "exit_error":
            return obj.get("message", "Error desconocido")
    return None


def _parse_json_lines(text: str) -> Iterator[dict[str, Any]]:
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        yield json.loads(line)


def init_repo(repository: str, password: str) -> str:
    result = _run(repository, password, ["init"], json_output=True)
    obj = json.loads(result.stdout.strip())
    if obj.get("message_type") == "initialized":
        return obj.get("id", repository)
    return repository


def list_snapshots(repository: str, password: str) -> list[dict[str, Any]]:
    result = _run(repository, password, ["snapshots"], json_output=True)
    text = result.stdout.strip()
    if not text:
        return []
    data = json.loads(text)
    snapshots: list[dict[str, Any]] = []
    if isinstance(data, list):
        for item in data:
            if "snapshots" in item:
                snapshots.extend(item["snapshots"])
            elif "id" in item or "short_id" in item:
                snapshots.append(item)
    return sorted(snapshots, key=lambda s: s.get("time", ""), reverse=True)


def backup(
    repository: str,
    password: str,
    paths: list[str],
    on_progress: Callable[[BackupProgress], None] | None = None,
) -> BackupSummary:
    proc = subprocess.Popen(
        [find_restic(), "--json", "backup", *paths],
        env=_env(repository, password),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    summary: BackupSummary | None = None
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg_type = obj.get("message_type")
        if msg_type == "status" and on_progress:
            on_progress(
                BackupProgress(
                    percent_done=obj.get("percent_done", 0) * 100,
                    files_done=obj.get("files_done", 0),
                    total_files=obj.get("total_files", 0),
                    bytes_done=obj.get("bytes_done", 0),
                    total_bytes=obj.get("total_bytes", 0),
                    current_files=obj.get("current_files"),
                )
            )
        elif msg_type == "summary" and obj.get("snapshot_id"):
            summary = BackupSummary(
                snapshot_id=obj["snapshot_id"],
                files_new=obj.get("files_new", 0),
                files_changed=obj.get("files_changed", 0),
                data_added=obj.get("data_added", 0),
                total_duration=obj.get("total_duration", 0),
            )
    proc.wait()
    stderr = proc.stderr.read() if proc.stderr else ""
    if proc.returncode != 0:
        msg = _parse_exit_error(stderr) or stderr.strip() or "Copia de seguridad fallida"
        raise ResticError(msg, proc.returncode)
    if summary is None:
        raise ResticError("La copia terminó sin crear snapshot")
    return summary


def restore(
    repository: str,
    password: str,
    snapshot_id: str,
    target: str,
    *,
    include: list[str] | None = None,
) -> None:
    args = ["restore", snapshot_id, "--target", target]
    if include:
        for path in include:
            args.extend(["--include", path])
    _run(repository, password, args, json_output=True)


def check_repo(repository: str, password: str) -> dict[str, Any]:
    result = _run(repository, password, ["check"], json_output=True)
    for obj in _parse_json_lines(result.stdout):
        if obj.get("message_type") == "summary":
            return obj
    return {"message_type": "summary", "num_errors": 0}


def forget_prune(
    repository: str,
    password: str,
    *,
    keep_last: int = 5,
    prune: bool = True,
) -> None:
    _run(
        repository,
        password,
        ["forget", "--keep-last", str(keep_last), "--prune"] if prune else ["forget", "--keep-last", str(keep_last)],
        json_output=True,
    )
