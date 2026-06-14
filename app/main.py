# -*- coding: utf-8 -*-
"""
TreeVision API 骨架（read-only，v0.1）。

在已載入的關聯式資料庫（本機 SQLite / 生產 PostgreSQL）上開放查詢端點，
讓「採集 → 入庫 → 查詢」後端鏈成形。影像上傳、推論、寫入端點俟 Phase 3 平台再補。

啟動：
    uvicorn app.main:app --reload
    # 文件 UI： http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, HTTPException, Query

from . import db

app = FastAPI(
    title="TreeVision API（骨架）",
    version="0.1.0",
    description="大雪山土肉桂試驗資料查詢 API（read-only 骨架）。資料層可 SQLite/PostgreSQL 互換。",
)


def _require_db():
    if not db.db_ready():
        raise HTTPException(
            status_code=503,
            detail="資料庫尚未建立。請先跑 scripts/etl_longformat_to_entities.py 與 scripts/load_entities_to_db.py。",
        )


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "db_ready": db.db_ready(), "db_path": db.db_path()}


@app.get("/treatments", tags=["試驗設計"])
def list_treatments():
    _require_db()
    return db.query("SELECT * FROM treatment ORDER BY treatment_id")


@app.get("/sites", tags=["林地"])
def list_sites():
    _require_db()
    return db.query(
        "SELECT site_id, name, age_class, area_ha, planted_date FROM site ORDER BY site_id")


@app.get("/sites/{site_id}", tags=["林地"])
def get_site(site_id: str):
    _require_db()
    row = db.query_one("SELECT * FROM site WHERE site_id = ?", (site_id,))
    if not row:
        raise HTTPException(404, "查無此 site_id")
    row["plots"] = db.query(
        "SELECT plot_id, treatment_id, tree_count FROM plot WHERE site_id = ? ORDER BY treatment_id",
        (site_id,))
    return row


@app.get("/trees", tags=["林地"])
def list_trees(
    site_id: str | None = None,
    treatment_id: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    _require_db()
    where, params = [], []
    if site_id:
        where.append("site_id = ?"); params.append(site_id)
    if treatment_id:
        where.append("treatment_id = ?"); params.append(treatment_id)
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    params += [limit, offset]
    return db.query(
        "SELECT tree_id, site_id, treatment_id, tree_no, is_multistem, stem_count, status "
        "FROM tree {} ORDER BY tree_id LIMIT ? OFFSET ?".format(clause), tuple(params))


@app.get("/trees/{tree_id}", tags=["林地"])
def get_tree(tree_id: str):
    _require_db()
    tree = db.query_one("SELECT * FROM tree WHERE tree_id = ?", (tree_id,))
    if not tree:
        raise HTTPException(404, "查無此 tree_id")
    tree["measurements"] = db.query(
        "SELECT season, stem_seq, measure_part, dbh_cm, height_m, volume_m3, status "
        "FROM tree_measurement WHERE tree_id = ? ORDER BY season, stem_seq", (tree_id,))
    return tree


@app.get("/treatments/{treatment_id}/summary", tags=["試驗對照"])
def treatment_summary(treatment_id: str):
    """各季別該處理組的平均胸徑/樹高（試驗對照分析的雛形）。"""
    _require_db()
    if not db.query_one("SELECT 1 FROM treatment WHERE treatment_id = ?", (treatment_id,)):
        raise HTTPException(404, "查無此 treatment_id")
    return db.query(
        "SELECT m.season, COUNT(*) AS n, "
        "ROUND(AVG(m.dbh_cm), 2) AS dbh_mean, ROUND(AVG(m.height_m), 2) AS height_mean "
        "FROM tree_measurement m JOIN tree t ON t.tree_id = m.tree_id "
        "WHERE t.treatment_id = ? AND m.dbh_cm IS NOT NULL "
        "GROUP BY m.season ORDER BY m.season", (treatment_id,))
