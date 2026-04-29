# metadata/ — 影像與樹木 metadata 主表

存放跨影像的對應表與主檔。

## 主檔（不入 git）

| 檔名 | 內容 | 主鍵 |
|------|------|------|
| `image_metadata.csv` | 每張影像的拍攝參數 | `image_id` |
| `tree_registry.csv` | 樹木個體基本資料 | `tree_id` |
| `site_registry.csv` | 場域資料 | `site_id` |
| `device_registry.csv` | 拍攝設備資料 | `device_id` |
| `capture_session.csv` | 巡檢場次紀錄 | `session_id` |

> 主檔含實際場域 GPS 與樹木資訊，已在 `.gitignore` 排除。

## 範本檔（入 git，可參考欄位）

| 檔名 | 用途 |
|------|------|
| [`image_metadata.template.csv`](image_metadata.template.csv) | 影像 metadata 範本，6 筆試拍範例 |
| [`tree_registry.template.csv`](tree_registry.template.csv) | 樹木主檔範本 |
| [`site_registry.template.csv`](site_registry.template.csv) | 場域主檔範本 |
| [`field-record-form.md`](field-record-form.md) | 田野紙本紀錄表（可列印） |

## 規範

- 主檔以 UTF-8 編碼 CSV 為主，並提供等價 Parquet 版本（效能用）
- 主鍵不可變更，刪除以 `is_deleted=true` 軟刪除
- 修改紀錄寫入 `logs/metadata_changelog.csv`
- 詳細欄位定義見 [../docs/data-schema.md](../docs/data-schema.md) 與 [../schemas/](../schemas/)
