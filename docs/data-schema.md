# 資料 Schema 定義

| 文件版本 | v0.1 |
|----------|------|
| 適用模型 | CanopySeg v0、LeafInst v0、LeafDefect v0 |
| 主資料庫 | PostgreSQL 16 |
| 物件儲存 | GCS / S3 |

---

## 壹、命名與型別約定

| 約定 | 說明 |
|------|------|
| 表名 | snake_case，單數（`tree`、`image`） |
| 欄位名 | snake_case |
| 主鍵 | `id`（UUID v7）或業務鍵（`tree_id` 等） |
| 時間 | `*_at` 用 TIMESTAMPTZ；`*_date` 用 DATE |
| Enum | 用 PostgreSQL ENUM 或 CHECK 限制 |
| 軟刪除 | `is_deleted BOOLEAN DEFAULT false` + `deleted_at TIMESTAMPTZ` |
| 稽核 | 所有表帶 `created_at`、`updated_at`、`created_by`、`updated_by` |

---

## 貳、實體欄位定義

### 一、site（場域）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `site_id` | TEXT PK | ✓ | 例：`NTU01` |
| `name` | TEXT | ✓ | 場域中文名 |
| `owner` | TEXT | ✓ | 主管機關 |
| `region` | TEXT | ✓ | 縣市 |
| `centroid_lat` / `centroid_lon` | DOUBLE | ✓ | 場域中心 |
| `bbox_geojson` | JSONB | ○ | 場域邊界（GeoJSON Polygon） |
| `area_ha` | DOUBLE | ○ | 面積（公頃） |
| `forest_type` | TEXT | ○ | 林型 |
| `note` | TEXT | ○ | 備註 |

### 二、tree（樹木個體）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `tree_id` | TEXT | ✓ | 場域內唯一 |
| `site_id` | TEXT FK | ✓ | |
| `species_zh` | TEXT | ○ | 中文種名 |
| `species_sci` | TEXT | ○ | 學名 |
| `lat` / `lon` | DOUBLE | ○ | GPS（可遮蔽顯示） |
| `dbh_cm` | DOUBLE | ○ | 胸徑 |
| `height_m` | DOUBLE | ○ | 樹高 |
| `crown_status` | ENUM | ○ | `healthy`/`stressed`/`damaged`/`dead` |
| `planted_year` | INT | ○ | 種植年（人工林） |
| `is_protected` | BOOL | ○ | 是否為保護樹 |
| `note` | TEXT | ○ | |
| `created_at`/`updated_at` | TIMESTAMPTZ | ✓ | |

### 三、image（影像）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `image_id` | UUID PK | ✓ | |
| `tree_id` | TEXT FK | ✓ | |
| `site_id` | TEXT FK | ✓ | |
| `capture_type` | ENUM | ✓ | `canopy` / `leaf_closeup` |
| `capture_datetime` | TIMESTAMPTZ | ✓ | |
| `view` | ENUM | ✓ | `north`/`south`/`east`/`west`/`overhead`/`handheld` |
| `device_id` | TEXT FK | ✓ | |
| `session_id` | TEXT FK | ○ | |
| `storage_uri` | TEXT | ✓ | `gs://.../raw/...jpg` |
| `width_px` / `height_px` | INT | ✓ | |
| `file_size_bytes` | BIGINT | ✓ | |
| `sha256` | TEXT | ✓ | 內容雜湊 |
| `gps_lat` / `gps_lon` | DOUBLE | ○ | DB 永遠儲存原始值；遮蔽在 API serialization 時做（見下方註） |
| `exif_json` | JSONB | ○ | 完整 EXIF |
| `scale_object_type` | ENUM | ◎ | 葉片必填 |
| `scale_object_size_mm` | DOUBLE | ◎ | 葉片必填 |
| `has_color_card` | BOOL | ◎ | 葉片建議 |
| `weather` | ENUM | ○ | |
| `quality_pass` | BOOL | ○ | 自動品質檢查結果 |
| `quality_issues` | TEXT[] | ○ | `blurry`/`overexposed`/`dark`/`low_res` |
| `note` | TEXT | ○ | |
| `created_at` | TIMESTAMPTZ | ✓ | |

> **GPS 隱私政策（[ADR-0001 議題 5](decisions/0001-open-questions.md)）**：`gps_lat` / `gps_lon` 欄位在 DB 中**永遠儲存原始值**，**不**在 DB 層遮蔽。API serialization 階段依呼叫者角色動態裁切：admin → `exact`、認證研究者 → `town`、公開/訪客 → `county`，並於回應中附 `gps_precision` 欄位。同樣規則適用於 `tree.lat` / `tree.lon`、`site.centroid_lat` / `site.centroid_lon`。

### 四、analysis_run（推論執行）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `run_id` | UUID PK | ✓ | |
| `image_id` | UUID FK | ✓ | |
| `model_id` | TEXT FK | ✓ | |
| `model_version` | TEXT | ✓ | |
| `started_at` / `finished_at` | TIMESTAMPTZ | ✓ | |
| `status` | ENUM | ✓ | `queued`/`running`/`succeeded`/`failed` |
| `error_message` | TEXT | ○ | |
| `mask_uri` | TEXT | ○ | mask 影像位置 |
| `metrics_json` | JSONB | ○ | 結果指標 |
| `inference_seconds` | DOUBLE | ○ | |
| `device` | TEXT | ✓ | `cpu`/`cuda:0` |

### 五、image_metric（影像指標主表，由 analysis_run 整理而來）

#### 共用欄位

| 欄位 | 型別 | 說明 |
|------|------|------|
| `image_id` | UUID FK | |
| `model_id` | TEXT | 標示來源模型 |
| `run_id` | UUID FK | |

#### CanopySeg 欄位

| 欄位 | 型別 | 範圍 |
|------|------|------|
| `canopy_area_px` | BIGINT | ≥ 0 |
| `canopy_ratio` | DOUBLE | 0~1 |
| `veg_cover_ratio` | DOUBLE | 0~1 |
| `green_ratio` | DOUBLE | 0~1 |
| `yellow_ratio` | DOUBLE | 0~1 |
| `brown_ratio` | DOUBLE | 0~1 |
| `abnormal_hotspot_count` | INT | ≥ 0 |
| `abnormal_hotspot_max_area_ratio` | DOUBLE | 0~1 |

#### LeafInst 欄位

| 欄位 | 型別 |
|------|------|
| `leaf_count` | INT |
| `mm_per_pixel` | DOUBLE |
| `scale_object_detected` | BOOL |
| `scale_object_type` | TEXT |
| `leaf_area_mean_cm2` | DOUBLE |
| `leaf_area_std_cm2` | DOUBLE |
| `leaf_area_p25_cm2` | DOUBLE |
| `leaf_area_p50_cm2` | DOUBLE |
| `leaf_area_p75_cm2` | DOUBLE |
| `leaf_length_mean_mm` | DOUBLE |
| `leaf_width_mean_mm` | DOUBLE |

#### LeafDefect 欄位（影像層級平均）

| 欄位 | 型別 | 必填 | 範圍 | 說明 |
|------|------|------|------|------|
| `lesion_ratio_mean` | DOUBLE | ✓ | 0~1 | |
| `chlorosis_ratio_mean` | DOUBLE | ✓ | 0~1 | |
| `necrosis_ratio_mean` | DOUBLE | ✓ | 0~1 | |
| `hole_ratio_mean` | DOUBLE | ✓ | 0~1 | |
| `total_defect_ratio_mean` | DOUBLE | ✓ | 0~1 | |
| `health_score_global_mean` | DOUBLE | ✓ | 0~100 | 全域權重健康分數的影像平均，公式見 SPEC §伍-三 |
| `health_score_species_mean` | DOUBLE | ○ | 0~100 | 樹種特化權重健康分數（v1 為 NULL，待校正後填入） |
| `health_grade` | CHAR(1) | ✓ | A~E | 由 `health_score_global_mean` 計算 |
| `weights_config_id` | TEXT | ✓ | | 對應 `models/LeafDefect/config.yaml` 的 `health_weights` 版本識別，供推論結果可追溯到使用的權重 |

### 六、leaf_instance（葉片實例）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `instance_id` | UUID PK | ✓ | |
| `image_id` | UUID FK | ✓ | |
| `polygon_json` | JSONB | ✓ | 多邊形座標（葉柄併入葉片實例，邊界沿葉柄外緣，[ADR-0001 議題 2](decisions/0001-open-questions.md)） |
| `bbox_json` | JSONB | ✓ | `[x,y,w,h]` |
| `area_px` | BIGINT | ✓ | |
| `area_cm2` | DOUBLE | ✓ | |
| `length_mm` | DOUBLE | ○ | |
| `width_mm` | DOUBLE | ○ | |
| `lesion_ratio` | DOUBLE | ○ | |
| `chlorosis_ratio` | DOUBLE | ○ | |
| `necrosis_ratio` | DOUBLE | ○ | |
| `hole_ratio` | DOUBLE | ○ | |
| `health_score_global` | DOUBLE | ✓（有 LeafDefect 推論時）| 全域權重健康分數，0~100 |
| `health_score_species` | DOUBLE | ○ | 樹種特化權重健康分數（v1 為 NULL） |
| `health_grade` | CHAR(1) | ○ | 由 `health_score_global` 計算 |

### 七、tree_daily_summary（單棵樹單日彙總）

| 欄位 | 型別 | 說明 |
|------|------|------|
| `tree_id` | TEXT FK | PK 1 |
| `date` | DATE | PK 2 |
| `image_count_canopy` | INT | |
| `image_count_leaf` | INT | |
| `canopy_ratio_mean` | DOUBLE | |
| `green_ratio_mean` | DOUBLE | |
| `yellow_ratio_mean` | DOUBLE | |
| `brown_ratio_mean` | DOUBLE | |
| `leaf_count_total` | INT | |
| `leaf_area_mean_cm2` | DOUBLE | |
| `health_score_global_mean` | DOUBLE | 全域權重健康分數的當日平均（v1 必填） |
| `health_score_species_mean` | DOUBLE | 樹種特化權重的當日平均（v1 為 NULL） |
| `health_grade` | CHAR(1) | 由 `health_score_global_mean` 計算（v1.5 起若 `health_score_species_mean` 已填入，則改用 species 版本） |
| `risk_flag` | BOOL | 是否進入高風險清單 |
| `risk_reasons` | TEXT[] | 例：`['high_yellow','low_health']` |

### 八、annotation（標註）

| 欄位 | 型別 |
|------|------|
| `annotation_id` | UUID PK |
| `image_id` | UUID FK |
| `annotator` | TEXT |
| `category` | TEXT |
| `geometry_json` | JSONB |
| `area_px` | BIGINT |
| `version` | INT |
| `is_gold` | BOOL |
| `created_at` | TIMESTAMPTZ |

### 九、model（模型版本）

| 欄位 | 型別 |
|------|------|
| `model_id` | TEXT PK |
| `task` | ENUM | `canopy_seg`/`leaf_inst`/`leaf_defect` |
| `version` | TEXT |
| `framework` | TEXT |
| `weights_uri` | TEXT |
| `train_dataset_id` | TEXT |
| `eval_metrics_json` | JSONB |
| `released_at` | TIMESTAMPTZ |
| `is_active` | BOOL |
| `model_card_uri` | TEXT |

---

## 參、Enum 定義

```sql
CREATE TYPE capture_type_t AS ENUM ('canopy', 'leaf_closeup');
CREATE TYPE view_t AS ENUM ('north', 'south', 'east', 'west', 'overhead', 'handheld');
CREATE TYPE crown_status_t AS ENUM ('healthy', 'stressed', 'damaged', 'dead');
CREATE TYPE scale_obj_t AS ENUM ('a4_grid', 'coin_5twd', 'coin_10twd', 'ruler', 'other');
CREATE TYPE weather_t AS ENUM ('sunny', 'cloudy', 'overcast', 'rain', 'fog');
CREATE TYPE run_status_t AS ENUM ('queued', 'running', 'succeeded', 'failed');
CREATE TYPE model_task_t AS ENUM ('canopy_seg', 'leaf_inst', 'leaf_defect');
```

---

## 肆、輸出檔案格式（offline）

### 一、`outputs/per_image/{date}_{run}.parquet`

每張影像一筆，欄位 = `image_id` + 「貳-五」共用 + 各模型欄位（缺者為 NULL）。

### 二、`outputs/per_tree_daily/{date}_{run}.parquet`

對應「貳-七 tree_daily_summary」結構。

### 三、`outputs/per_site/{date}_{run}.parquet`

| 欄位 | 說明 |
|------|------|
| `site_id`, `date` | PK |
| `tree_count` | 該日有資料的樹木數 |
| `tree_count_high_risk` | risk_flag 為 true 的數量 |
| `green_ratio_site_mean` | |
| `yellow_ratio_site_mean` | |
| `health_score_site_mean` | |

---

## 伍、JSON Schema 檔（機器可讀）

對應檔案放在 `../schemas/`：

- `image_metadata.schema.json`
- `analysis_result.canopyseg.schema.json`
- `analysis_result.leafinst.schema.json`
- `analysis_result.leafdefect.schema.json`
- `tree_daily_summary.schema.json`
