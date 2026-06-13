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

## 範本檔（入 git，可參考欄位；v0.2 對齊 schemas/，範例採大雪山土肉桂試驗值）

### 林地實體層

| 檔名 | 用途 |
|------|------|
| [`site_registry.template.csv`](site_registry.template.csv) | 場域主檔（4 樣區範例）|
| [`tree_registry.template.csv`](tree_registry.template.csv) | 樣木個體（tree_id 既有碼）|
| [`tree_measurement.template.csv`](tree_measurement.template.csv) | 歷次量測（季配；含多幹莖序）|
| [`regeneration_subplot.template.csv`](regeneration_subplot.template.csv) | 再生小樣區 |
| [`soil_environment.template.csv`](soil_environment.template.csv) | 土壤與環境 |
| [`phenology.template.csv`](phenology.template.csv) | 物候 |
| [`disturbance.template.csv`](disturbance.template.csv) | 干擾事件 |
| [`sample.template.csv`](sample.template.csv) | 採集樣品 |

### 試驗設計層

| 檔名 | 用途 |
|------|------|
| [`treatment.template.csv`](treatment.template.csv) | 處理組（C0/P1/F150/P1F150）|
| [`plot.template.csv`](plot.template.csv) | 試驗單元（site × treatment）|
| [`campaign.template.csv`](campaign.template.csv) | 採集場次（按樣區分批，季別）|
| [`fixed_camera_station.template.csv`](fixed_camera_station.template.csv) | 固定攝點 |

### 影像層 + 其他

| 檔名 | 用途 |
|------|------|
| [`image_metadata.template.csv`](image_metadata.template.csv) | 影像 metadata（v0.2：試驗 FK + 整株/尺度物）|
| [`field-record-form.md`](field-record-form.md) | 田野紙本紀錄表（可列印） |

> 全部範本列以對應 `schemas/*.schema.json`（Draft 2020-12）驗證通過。GPS 一律用示意座標或留空（樣木精確位置不入公開檔，守 Cloud.md GPS 政策）。

## 規範

- 主檔以 UTF-8 編碼 CSV 為主，並提供等價 Parquet 版本（效能用）
- 主鍵不可變更，刪除以 `is_deleted=true` 軟刪除
- 修改紀錄寫入 `logs/metadata_changelog.csv`
- 詳細欄位定義見 [../docs/data-schema.md](../docs/data-schema.md) 與 [../schemas/](../schemas/)
