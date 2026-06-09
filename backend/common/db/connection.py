from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
SCHEMA_PATH = BACKEND_DIR / "db" / "schema.sql"

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")


class DatabaseUnavailable(RuntimeError):
    """Raised when the configured MySQL database cannot be reached."""


def _import_pymysql():
    try:
        import pymysql
    except ImportError as exc:
        raise DatabaseUnavailable(
            "PyMySQL is required for DB mode. Install backend/requirements.txt first."
        ) from exc
    return pymysql


def _db_name() -> str:
    name = os.getenv("DB_NAME", "alpled_db")
    if not name.replace("_", "").isalnum():
        raise DatabaseUnavailable(f"Unsafe DB_NAME value: {name!r}")
    return name


def _connect(database: str | None = None):
    pymysql = _import_pymysql()
    kwargs = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "charset": os.getenv("DB_CHARSET", "utf8mb4"),
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
    }
    if database:
        kwargs["database"] = database
    return pymysql.connect(**kwargs)


def _schema_statements() -> list[str]:
    if not SCHEMA_PATH.exists():
        raise DatabaseUnavailable(f"Schema file is missing: {SCHEMA_PATH}")

    statements: list[str] = []
    current: list[str] = []
    for line in SCHEMA_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current).rstrip(";"))
            current = []
    if current:
        statements.append("\n".join(current))
    return statements


def ensure_database() -> None:
    db_name = _db_name()
    try:
        with _connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            conn.commit()

        with _connect(db_name) as conn:
            with conn.cursor() as cursor:
                for statement in _schema_statements():
                    cursor.execute(statement)
            conn.commit()
    except Exception as exc:
        raise DatabaseUnavailable(str(exc)) from exc


@contextmanager
def db_connection() -> Iterator:
    try:
        conn = _connect(_db_name())
    except Exception as exc:
        raise DatabaseUnavailable(str(exc)) from exc
    try:
        yield conn
    finally:
        conn.close()
