# schemas/ — JSON Schema 定義

機器可讀的資料結構定義，用於：

- 上傳時 metadata 驗證
- 推論結果格式校驗
- 自動產生 TypeScript / Pydantic 型別
- 文件互通

## 檔案（v0.2，四層架構，對齊 ADR-0003）

### 林地實體層（對齊既有 XLSX 調查表）

| 檔名 | 用途 |
|------|------|
| `site_registry.schema.json` | 場域（作業列區）|
| `tree_registry.schema.json` | 樣木個體（tree_id＝`<樣區短碼>-<處理>-<序號>`）|
| `tree_measurement.schema.json` | 樣木歷次量測（季配）|
| `regeneration_subplot.schema.json` | 再生小樣區 |
| `soil_environment.schema.json` | 土壤與環境 |
| `phenology.schema.json` | 物候 |
| `disturbance.schema.json` | 干擾事件 |
| `sample.schema.json` | 採集樣品 |

### 試驗設計層

| 檔名 | 用途 |
|------|------|
| `treatment.schema.json` | 處理組（C0/P1/F150/P1F150，全場 2×2）|
| `plot.schema.json` | 試驗單元（site × treatment）|
| `campaign.schema.json` | 採集場次（按樣區分批，季別）|
| `fixed_camera_station.schema.json` | 固定攝點（ADR-0005）|

### 影像 + 模型層

| 檔名 | 用途 |
|------|------|
| `image_metadata.schema.json` | 影像上傳 metadata（v0.2：新試驗 FK + enum 擴充）|
| `analysis_result.canopyseg.schema.json` | CanopySeg 推論結果 |
| `analysis_result.leafinst.schema.json` | LeafInst 推論結果 |
| `analysis_result.leafdefect.schema.json` | LeafDefect 推論結果 |

### 試驗對照分析層

| 檔名 | 用途 |
|------|------|
| `treatment_response_summary.schema.json` | 14 響應指標 × 處理組 × 場次（供 ANOVA）|
| `experiment_anova_result.schema.json` | ANOVA 結果（修剪 × 施肥 2×2）|

> **ID 規約**：site_id `115-12-1`／treatment_id `C0/P1/F150/P1F150`／plot_id `<site>.<treatment>`／tree_id `115121-C0-001`（多幹莖序另欄）／campaign_id `<site>_<季別>`／station_id `<tree_id>.<攝點>`。全 18 檔以 `jsonschema` Draft 2020-12 驗證，並以「土肉桂試驗_長格式」真實資料 round-trip 通過。

## 驗證範例（Python）

```python
import json, jsonschema
from pathlib import Path

schema = json.loads(Path("schemas/image_metadata.schema.json").read_text(encoding="utf-8"))
data = {
    "tree_id": "115121-C0-001",
    "site_id": "115-12-1",
    "capture_type": "leaf_closeup",
    "capture_datetime": "2026-05-01T14:30:00+08:00",
    "view": "handheld",
    "device_id": "iphone15pro_user01",
    "scale_object_type": "a4_grid",
    "scale_object_size_mm": 297.0
}
jsonschema.validate(data, schema)
```

## 自動產生型別

### TypeScript（前端用）

```bash
npx json-schema-to-typescript schemas/image_metadata.schema.json > app/types/imageMetadata.ts
```

### Pydantic（後端用）

```bash
datamodel-codegen --input schemas/image_metadata.schema.json --output backend/models/image_metadata.py
```
