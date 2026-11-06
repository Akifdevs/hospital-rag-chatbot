#!/usr/bin/env python3
"""Migrate the legacy SQLite RAG database into MySQL.

Runtime code does not use SQLite. This script is a one-time bridge for the
existing data/rag.db file and can be rerun safely because rows are inserted
with their original primary keys and duplicate rows are ignored.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, text

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import DATABASE_URL  # noqa: E402
from database.connection import engine, init_database  # noqa: E402

SOURCE_PATH = Path(
    os.getenv("SQLITE_SOURCE_PATH", str(BASE_DIR / "data" / "rag.db"))
)
TABLES = (
    "documents",
    "document_versions",
    "version_snapshots",
    "snapshot_documents",
    "chunks",
)


def source_columns(source: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in source.execute(f"PRAGMA table_info(`{table}`)")]


def target_columns(table: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table)}


def normalize_value(table: str, column: str, value: Any) -> Any:
    if table == "chunks" and column == "metadata":
        if value is None:
            return "{}"

        if isinstance(value, bytes):
            value = value.decode("utf-8")

        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass

        return json.dumps(value, ensure_ascii=False)

    return value


def migrate_table(source: sqlite3.Connection, target, table: str) -> int:
    available = [column for column in source_columns(source, table) if column in target_columns(table)]
    if not available:
        return 0

    columns_sql = ", ".join(f"`{column}`" for column in available)
    placeholders = ", ".join(f":{column}" for column in available)
    statement = text(
        f"INSERT IGNORE INTO `{table}` ({columns_sql}) VALUES ({placeholders})"
    )

    rows = source.execute(f"SELECT {columns_sql} FROM `{table}`").fetchall()
    for row in rows:
        values = {
            column: normalize_value(table, column, row[index])
            for index, column in enumerate(available)
        }
        target.execute(statement, values)
    return len(rows)


def main() -> None:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"SQLite source database not found: {SOURCE_PATH}")

    print(f"Source: {SOURCE_PATH}")
    print(f"Target: {DATABASE_URL.split('@')[-1]}")
    init_database()

    source = sqlite3.connect(str(SOURCE_PATH))
    source.row_factory = sqlite3.Row
    try:
        with engine.begin() as target:
            target.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            counts = {table: migrate_table(source, target, table) for table in TABLES}
            target.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    finally:
        source.close()

    for table, count in counts.items():
        print(f"{table}: {count} source rows processed")
    print("Migration complete.")


if __name__ == "__main__":
    main()
