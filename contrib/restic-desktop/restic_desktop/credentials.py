# SPDX-License-Identifier: BSD-2-Clause
"""Almacenamiento seguro de contraseñas con libsecret (GNOME Keyring)."""

from __future__ import annotations

SERVICE = "restic-desktop"

_connection = None


def _get_connection():
    global _connection
    import secretstorage

    if _connection is None:
        _connection = secretstorage.dbus_init()
    return _connection


def _collection():
    import secretstorage

    conn = _get_connection()
    return secretstorage.get_default_collection(conn)


def _attributes(repository: str) -> dict[str, str]:
    return {"application": SERVICE, "repository": repository}


def store_password(repository: str, password: str) -> None:
    coll = _collection()
    coll.create_item(
        f"Restic: {repository}",
        _attributes(repository),
        password.encode("utf-8"),
        replace=True,
    )


def is_available() -> bool:
    try:
        import secretstorage

        secretstorage.check_service_availability(_get_connection())
        return True
    except Exception:
        return False


def get_password(repository: str) -> str | None:
    try:
        import secretstorage

        conn = _get_connection()
        for item in secretstorage.search_items(conn, _attributes(repository)):
            secret = item.get_secret()
            if isinstance(secret, bytes):
                return secret.decode("utf-8")
            return str(secret)
    except Exception:
        return None
    return None


def delete_password(repository: str) -> None:
    import secretstorage

    conn = _get_connection()
    for item in secretstorage.search_items(conn, _attributes(repository)):
        item.delete()
