# -*- coding: utf-8 -*-
"""
DB loader：把 ETL 產出的 6 個正規化實體 CSV（outputs/entities/）載入關聯式資料庫。

本機開發/測試以 **SQLite** 為目標（stdlib、零安裝、檔案式），套用 `db/schema.sql`
（可攜式 DDL）。生產平台改用 **PostgreSQL** 時，同一份 schema.sql 直接適用，
僅需把連線層換成 psycopg（轉換/載入邏輯不變）。

驗證：載入後執行 FK 完整性檢查（PRAGMA foreign_key_check）與數筆健全性查詢，
確認 site→plot→tree→measurement 的關聯在真實資料上成立。

用法：
    python scripts/load_entities_to_db.py
    python scripts/load_entities_to_db.py --entities-dir outputs/entities --db outputs/treevision.db
"""
import argparse
import csv
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# CSV 檔名 → 資料表名（依 FK 相依排序）
LOAD_ORDER = [
    ("treatment.csv", "treatment"),
    ("site_registry.csv", "site"),
    ("plot.csv", "plot"),
    ("campaign.csv", "campaign"),
    ("tree_registry.csv", "tree"),
    ("tree_measurement.csv", "tree_measurement"),
]


def coerce(v):
    if v == "" or v is None:
        return None
    if v == "True":
        return 1
    if v == "False":
        return 0
    return v  # 數值字串交由 SQLite 欄位親和性轉換


def load_csv(con, path, table):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return 0
    cols = list(rows[0].keys())
    sql = "INSERT INTO {} ({}) VALUES ({})".format(
        table, ",".join(cols), ",".join("?" * len(cols)))
    con.executemany(sql, [[coerce(r[c]) for c in cols] for r in rows])
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description="載入 ETL 實體 CSV 至資料庫（SQLite 本機）")
    ap.add_argument("--entities-dir", default=os.path.join(REPO, "outputs", "entities"))
    ap.add_argument("--db", default=os.path.join(REPO, "outputs", "treevision.db"))
    ap.add_argument("--schema", default=os.path.join(REPO, "db", "schema.sql"))
    args = ap.parse_args()

    for fn, _ in LOAD_ORDER:
        p = os.path.join(args.entities_dir, fn)
        if not os.path.exists(p):
            ap.error("找不到實體檔 {}；請先跑 etl_longformat_to_entities.py".format(p))

    if os.path.exists(args.db):
        os.remove(args.db)  # 乾淨重建
    con = sqlite3.connect(args.db)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(open(args.schema, encoding="utf-8").read())

    print("=== 載入 ===")
    total = 0
    try:
        for fn, table in LOAD_ORDER:
            n = load_csv(con, os.path.join(args.entities_dir, fn), table)
            total += n
            print("OK  {:18s} ← {:24s} rows={}".format(table, fn, n))
        con.commit()
    except sqlite3.IntegrityError as e:
        con.rollback()
        print("ERR 載入失敗（完整性違規）:", e)
        sys.exit(1)

    # FK 完整性檢查
    viol = con.execute("PRAGMA foreign_key_check").fetchall()
    print("\n=== FK 完整性檢查 ===")
    print("違規列數:", len(viol))
    for v in viol[:10]:
        print("  ", v)

    # 健全性查詢
    print("\n=== 健全性查詢 ===")
    print("各處理組樹數:")
    for tid, n in con.execute(
            "SELECT treatment_id, COUNT(*) FROM tree GROUP BY treatment_id ORDER BY treatment_id"):
        print("  {:8s} {}".format(tid, n))
    print("各季別量測數:")
    for s, n in con.execute(
            "SELECT season, COUNT(*) FROM tree_measurement GROUP BY season ORDER BY season"):
        print("  {:8s} {}".format(s, n))
    print("JOIN 範例（site→tree→measurement，前 3 列）:")
    q = """SELECT s.name, t.tree_id, m.season, m.dbh_cm, m.height_m
           FROM tree_measurement m
           JOIN tree t ON t.tree_id = m.tree_id
           JOIN site s ON s.site_id = t.site_id
           WHERE m.dbh_cm IS NOT NULL
           ORDER BY t.tree_id, m.season LIMIT 3"""
    for row in con.execute(q):
        print("  ", row)

    con.close()
    print("\n資料庫:", args.db)
    print("RESULT:", "OK（FK 完整）" if not viol else "FK 違規={}".format(len(viol)))
    sys.exit(0 if not viol else 1)


if __name__ == "__main__":
    main()
