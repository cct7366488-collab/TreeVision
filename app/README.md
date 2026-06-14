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
| GET | `/images` | 入庫影像列表（可篩 `tree_id` / `quality_pass`，分頁）|
| GET | `/images/quality-summary` | 影像品質彙總（合格/待補拍/各問題計數）|
| POST | `/images/validate-metadata` | 拍攝前預驗 metadata（schema + tree/campaign FK）|

## 影像入庫管線

現場影像進系統的第一站：[`app/ingest.py`](ingest.py)（核心）＋ [`scripts/ingest_images.py`](../scripts/ingest_images.py)（批次 CLI）。
流程：metadata schema 驗證 → DB 參照比對 → 品質檢查（解析度/模糊/曝光）→ 入庫。
metadata/FK 錯誤即拒收；品質問題仍入庫但標記 `quality_pass=False` 待補拍。

```powershell
python scripts/ingest_images.py --metadata <meta.csv> --images-dir <影像資料夾>
```

> DB 來源預設 `outputs/treevision.db`（gitignored）；可用環境變數 `TREEVISION_DB` 指定。
