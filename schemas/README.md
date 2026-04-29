# schemas/ — JSON Schema 定義

機器可讀的資料結構定義，用於：

- 上傳時 metadata 驗證
- 推論結果格式校驗
- 自動產生 TypeScript / Pydantic 型別
- 文件互通

## 檔案

| 檔名 | 用途 |
|------|------|
| `image_metadata.schema.json` | 影像上傳 metadata 驗證 |
| `analysis_result.canopyseg.schema.json` | CanopySeg 推論結果 |
| `analysis_result.leafinst.schema.json` | LeafInst 推論結果 |
| `analysis_result.leafdefect.schema.json` | LeafDefect 推論結果 |

## 驗證範例（Python）

```python
import json, jsonschema
from pathlib import Path

schema = json.loads(Path("schemas/image_metadata.schema.json").read_text(encoding="utf-8"))
data = {
    "tree_id": "T0123",
    "site_id": "NTU01",
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
