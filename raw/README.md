# raw/ — 原始影像

存放從相機 / 手機 / UAV 直接下載的原始影像，**不做任何修改**。

## 子目錄

- `canopy/` — 樹冠影像（仰拍、地面拍攝整棵樹冠輪廓、UAV 俯拍冠層）
- `leaf_closeup/` — 葉片近拍（手持單葉、含尺度物 / 色卡）

## 命名規則

```
{site_id}_{tree_id}_{capture_type}_{YYYYMMDD}_{HHMM}_{view}_{seq}.{ext}

範例：
NTU01_T0123_canopy_20260501_1430_north_001.jpg
NTU01_T0123_leafcloseup_20260501_1505_handheld_001.jpg
```

| 欄位 | 說明 | 範例 |
|------|------|------|
| site_id | 場域代碼 | NTU01、SHN02 |
| tree_id | 樹木編號（場域內唯一） | T0001~T9999 |
| capture_type | 影像類型 | `canopy` 或 `leafcloseup` |
| YYYYMMDD | 拍攝日期 | 20260501 |
| HHMM | 拍攝時間 | 1430 |
| view | 方位 / 視角 | north / south / east / west / overhead / handheld |
| seq | 同方位序號 | 001、002、… |

## 規範

- 不修改檔名以外的內容（不裁切、不壓縮、不去除 EXIF）
- 對應 metadata 進入 `metadata/image_metadata.csv`（或資料庫）
- 此目錄已在 `.gitignore`，**不會推送至 GitHub**
