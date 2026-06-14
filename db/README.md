# db/ — 資料庫結構

| 檔案 | 用途 |
|------|------|
| `schema.sql` | 核心試驗骨架 DDL（6 表：treatment/site/plot/campaign/tree/tree_measurement）|

## 可攜式 DDL（一份、兩用）

`schema.sql` 刻意使用 **TEXT / DOUBLE PRECISION / INTEGER / BOOLEAN / DATE + CHECK 約束**，
不用 PostgreSQL 原生 ENUM，因此**同一份 DDL 同時相容**：

- **PostgreSQL**（生產平台，Phase 3）
- **SQLite**（本機開發/測試，型別親和性自動套用）

## 載入

```powershell
# 1. 先由官方調查長表產生正規化實體（輸出 outputs/entities/，gitignored）
python scripts/etl_longformat_to_entities.py --longformat <長格式.xlsx>
# 2. 載入本機 SQLite 並驗證 FK 完整性 + 健全性查詢
python scripts/load_entities_to_db.py
```

生產改 PostgreSQL：套用同一 `schema.sql`，loader 連線層換 psycopg（轉換/載入邏輯不變）。

## 範圍

目前僅試驗骨架 6 表。影像/模型層、林地觀測層、試驗對照分析層俟有資料再補（見
[`../docs/data-schema.md`](../docs/data-schema.md) 四層架構與 [`../schemas/`](../schemas/) 18 個 JSON schema）。

> 載入後的 `outputs/treevision.db` 含客戶資料衍生，已被 `.gitignore` 排除、留本機。
