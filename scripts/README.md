# scripts/ — 輔助腳本

## 已實作

| 腳本 | 用途 |
|------|------|
| `_extract_refs.py` | 從 DOCX/XLSX/PPTX 萃取 `references/` 來源檔內容 |
| `etl_longformat_to_entities.py` | 土肉桂試驗「長格式」XLSX → v0.2 六實體（treatment/site/plot/tree/tree_measurement/campaign），逐筆 schema 驗證 + DQ 報告。輸入以 `--longformat`／env `TREEVISION_LONGFORMAT` 指定（不硬編客戶路徑）；輸出至 `outputs/entities/`（gitignored，客戶資料衍生不上雲）|
| `load_entities_to_db.py` | 把上述 6 實體 CSV 載入關聯式資料庫（本機 SQLite，套用 [`db/schema.sql`](../db/schema.sql)），驗 FK 完整性 + 健全性查詢。生產改 PostgreSQL 用同一 DDL。DB 輸出 `outputs/treevision.db`（gitignored）|
| `ingest_images.py` | 批次影像入庫：讀 metadata CSV + 影像資料夾，逐張 metadata 驗證＋FK 比對＋品質檢查（解析度/模糊/曝光）後寫入 DB `image` 表。核心邏輯於 [`app/ingest.py`](../app/ingest.py)|

## 預期腳本（待實作）

| 預期腳本 | 用途 |
|----------|------|
| `validate_metadata.py` | 檢查 `metadata/image_metadata.csv` 必填欄位、外鍵、命名規則 |
| `ingest_images.py` | 把 `raw/` 影像對應 metadata 寫入主表 |
| `image_quality_check.py` | 影像品質檢查（曝光、模糊、解析度） |
| `run_canopyseg.py` | 批次跑 CanopySeg 推論 |
| `run_leafinst.py` | 批次跑 LeafInst 推論 |
| `run_leafdefect.py` | 批次跑 LeafDefect 推論 |
| `aggregate_per_tree.py` | 彙整單張影像結果 → per_tree_daily |
| `make_image_report.py` | 產生單張影像 PDF 報告 |
| `make_tree_report.py` | 產生單棵樹健康履歷 PDF |
| `labelme_to_coco.py` | 標註格式轉換 |

> 此處只放輕量批次腳本。Web app（前後端、API server）建議分到獨立的 `app/` 目錄或獨立 repo。
