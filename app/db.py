# -*- coding: utf-8 -*-
"""DB 存取層（read-only 骨架）。

本機開發以 SQLite（`outputs/treevision.db`，由 load_entities_to_db.py 產生）為來源；
生產平台改 PostgreSQL 時，只需替換本模組的連線與 query 實作（介面 query/query_one 不變），
上層 API 路由不需更動。
"""
import os
import sqlite3

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(REPO, "outputs", "treevision.db")


def db_path():
    return os.environ.get("TREEVISION_DB", DEFAULT_DB)


def db_ready():
    return os.path.exists(db_path())


def _connect():
    con = sqlite3.connect(db_path())
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def query(sql, params=()):
    con = _connect()
    try:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally:
        con.close()


def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None
