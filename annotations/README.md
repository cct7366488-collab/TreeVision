# annotations/ — 訓練資料標註

## 子目錄

- `canopy/` — 樹冠影像標註
  - `canopy_mask`（樹冠多邊形）
  - `veg_mask`（綠色健康植生）
  - `yellow_mask`（黃化）
  - `brown_mask`（褐化 / 乾枯）
- `leaf_closeup/` — 葉片影像標註
  - `leaf_instance`（每片葉的實例分割）
  - `scale_object`（比例尺物件 bbox + 類型）
  - `lesion` / `chlorosis` / `necrosis` / `hole`（病徵分割）

## 格式

主格式採 [COCO format](https://cocodataset.org/#format-data) JSON：

```json
{
  "info": {...},
  "licenses": [...],
  "images": [
    {"id": 1, "file_name": "NTU01_T0123_canopy_20260501_1430_north_001.jpg", ...}
  ],
  "annotations": [
    {"id": 1, "image_id": 1, "category_id": 1, "segmentation": [...], "area": 12345, "bbox": [...]}
  ],
  "categories": [
    {"id": 1, "name": "canopy"},
    {"id": 2, "name": "veg"},
    ...
  ]
}
```

備援可接受 [labelme](https://github.com/wkentaro/labelme) JSON 格式（每影像一檔），透過 `scripts/labelme_to_coco.py` 轉換。

## 規範

- 標註者 ID 寫入 `metadata.annotator`
- 二人交叉標註隨機 5% 樣本以計算 IoU 一致性（目標 ≥ 0.85）
- 詳細規範見 [../docs/annotation-guideline.md](../docs/annotation-guideline.md)
- JSON 標註檔已在 `.gitignore`（資料治理用），需要公開時改為 `*.public.json` 並從 `.gitignore` 例外列出
