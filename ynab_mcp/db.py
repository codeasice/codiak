"""Shared SQLite connection helper for the YNAB MCP server."""
import os
import sqlite3

DB_PATH = os.getenv("CODIAK_DB_PATH", "accounts.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
