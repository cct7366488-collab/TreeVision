# app/ — TreeVision 後端 API（骨架）

read-only 查詢 API，建在已載入的關聯式資料庫上（本機 SQLite / 生產 PostgreSQL）。
影像上傳、推論、寫入端點俟 Phase 3 平台 MVP 再補。

## 檔案

| 檔案 | 用途 |
|------|------|
| `main.py` | FastAPI app 與路由 |
| `db.py` | DB 存取層（SQLite；生產換 PostgreSQL 僅改本檔，路由不動）|

## 前置

```powershell
pip install -r app/requirements.txt
# 先備好資料庫（由官方調查長表 → 實體 → DB）
python scripts/etl_longformat_to_entities.py --longformat <長格式.xlsx>
python scripts/load_entities_to_db.py
```

## 啟動

```powershell
uvicorn app.main:app --reload
# 互動文件： http://127.0.0.1:8000/docs
```

## 端點（v0.1）

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/health` | 服務與 DB 就緒狀態 |
| GET | `/treatments` | 處理組清單（C0/P1/F150/P1F150）|
| GET | `/sites` | 場域清單 |
| GET | `/sites/{site_id}` | 單一場域 + 其 plots |
| GET | `/trees` | 樹列表（可篩 `site_id` / `treatment_id`，分頁）|
| GET | `/trees/{tree_id}` | 單樹 + 歷次量測 |
| GET | `/treatments/{treatment_id}/summary` | 各季別平均胸徑/樹高（試驗對照雛形）|

> DB 來源預設 `outputs/treevision.db`（gitignored）；可用環境變數 `TREEVISION_DB` 指定。
