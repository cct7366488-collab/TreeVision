# outputs/ — 推論結果

模型推論後的結構化輸出（不含 mask 影像，mask 直接放在對應的 `canopy/masks/` 與 `leaf_closeup/masks/`）。

## 子目錄

| 目錄 | 粒度 | 主鍵 |
|------|------|------|
| `per_image/` | 每張影像一筆 | `image_id` |
| `per_tree_daily/` | 每棵樹每日彙總 | `tree_id`, `date` |
| `per_site/` | 每場域時間序列 | `site_id`, `date` |

## 檔案格式

- 主格式：Parquet（保留型別、效率高）
- 並提供等價 CSV 版（人工檢視 / Excel 匯入）

## 欄位字典

詳見 [../docs/data-schema.md](../docs/data-schema.md) 第 4 章「分析輸出欄位」。

## 規範

- 每次重新推論產出新版本：`per_image/v20260501_run01.parquet`
- 維持「最新版」軟連結 / 副本：`per_image/latest.parquet`
- 已在 `.gitignore`，不推送至 GitHub
