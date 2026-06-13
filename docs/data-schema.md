# 資料 Schema 定義

| 文件版本 | v0.2 |
|----------|------|
| 適用模型 | CanopySeg v0、LeafInst v0、LeafDefect v0、（PlantStructure v1+）|
| 主資料庫 | PostgreSQL 16 |
| 物件儲存 | GCS / S3 |
| 場域定錨 | 大雪山土肉桂試驗（[ADR-0002](decisions/0002-site-species-application-scope.md)）|
| 對應 ADR | [ADR-0003](decisions/0003-schema-alignment-with-xlsx.md) 四層架構 + 對齊既有 XLSX 調查表 |

> v0.2 重點：對齊既有「土肉桂生長調查記錄表.xlsx」10 工作表，重構為四層架構（林地實體 / 試驗設計 / 影像模型 / 試驗對照），並採既有試驗碼。對應機器可讀 schema 見 [`../schemas/`](../schemas/)（18 檔，Draft 2020-12 驗證）。

---

## 壹、命名與型別約定

| 約定 | 說明 |
|------|------|
| 表名 | snake_case，單數（`tree`、`image`） |
| 欄位名 | snake_case |
| 時間 | `*_at` 用 TIMESTAMPTZ；`*_date` 用 DATE |
| Enum | 用 PostgreSQL ENUM 或 CHECK 限制 |
| 軟刪除 | `is_deleted BOOLEAN DEFAULT false` + `deleted_at TIMESTAMPTZ` |
| 稽核 | 主要實體表帶 `created_at`、`updated_at`、`created_by`、`updated_by` |

### 一、ID 規約（v0.2，沿用既有試驗碼）

| 鍵 | 格式 | 例 | Pattern |
|----|------|----|---------|
| `site_id` | 林班作業列區 dash 式 | `115-12-1`、`8-1-1` | `^[0-9]{1,3}-[0-9]{1,3}-[0-9]{1,3}$` |
| `treatment_id` | 列舉 | `C0`/`P1`/`F150`/`P1F150` | enum |
| `plot_id` | `<site_id>.<treatment_id>` | `115-12-1.C0` | — |
| `tree_id` | `<樣區短碼>-<處理>-<序號>` | `115121-C0-001` | `^[0-9]{3,6}-(C0\|P1\|F150\|P1F150)-[0-9]{3}$` |
| `campaign_id` | `<site_id>_<季別>` | `8-1-1_114Q3` | — |
| `station_id` | `<tree_id>.<攝點>` | `115121-C0-001.north_side` | — |

> 短碼別名：`115121`/`117218`/`811`/`8110`（資料檔用）；多幹個體以 `stem_seq` 表莖序（長格式 `-s2/-s3`），不混入 tree_id。

---

## 貳、四層架構總覽

```
┌─────────────────────────────────────────────────────────────┐
│ 林地實體層（對齊 XLSX 10 工作表）                              │
│   site / tree / tree_measurement / regeneration_subplot      │
│   soil_environment / phenology / disturbance / sample        │
├─────────────────────────────────────────────────────────────┤
│ 試驗設計層                                                     │
│   treatment / plot / campaign / fixed_camera_station         │
├─────────────────────────────────────────────────────────────┤
│ 影像 + 模型層                                                  │
│   image / analysis_run / image_metric / leaf_instance        │
│   tree_image_metric_daily / annotation / model               │
├─────────────────────────────────────────────────────────────┤
│ 試驗對照分析層                                                 │
│   treatment_response_summary / experiment_anova_result       │
└─────────────────────────────────────────────────────────────┘
```

---

## 參、林地實體層（對齊既有 XLSX）

### 一、site（場域）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `site_id` | TEXT PK | ✓ | 作業列區編號，例 `115-12-1` |
| `site_code_short` | TEXT | ○ | 資料檔短碼，例 `115121` |
| `plot_type` | ENUM | ○ | `永久樣區`/`臨時樣區` |
| `name` | TEXT | ✓ | 場域中文名 |
| `owner` | TEXT | ✓ | 主管機關（林業及自然保育署臺中分署）|
| `region` / `township` / `location` | TEXT | ◎ | 縣市 / 鄉鎮 / 地點 |
| `forest_district` / `compartment` / `sub_lot_no` | TEXT | ○ | 事業區 / 林班 / 假地號 |
| `gps_datum` | ENUM | ✓ | `WGS84`/`TWD97` |
| `centroid_lat` / `centroid_lon` | DOUBLE | ✓ | 場域中心（GPS 遮蔽見 §伍-一註）|
| `elevation_m` / `slope_deg` | DOUBLE | ○ | 海拔 / 坡度 |
| `aspect` / `slope_position` | ENUM | ○ | 坡向 / 坡位（XLSX 代碼表）|
| `area_ha` | DOUBLE | ○ | 作業列區總面積（0.2372~0.5）|
| `age_stage` / `age_class` | TEXT / ENUM | ○ | 林齡描述 / 粗分類（`mature`/`juvenile`）|
| `planted_date` | TEXT | ○ | 栽植年月（115-12-1=2010-10、八仙山=2024-03）|
| `established_date` / `surveyor` / `forest_type` | — | ○ | 建置日期 / 調查員 / 林型 |

### 二、tree（樣木個體，= tree_registry）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `tree_id` | TEXT PK | ✓ | `115121-C0-001` |
| `site_id` / `plot_id` / `treatment_id` | TEXT FK | ✓ | |
| `tree_no` | INT | ✓ | 處理格內編號（1~30）|
| `tree_tag` | TEXT | ○ | 現場標籤號 |
| `is_multistem` / `stem_count` | BOOL / INT | ○ | 是否多幹 / 莖數 |
| `species_zh` | TEXT | ✓ | 土肉桂 |
| `species_sci` | TEXT | ○ | *Cinnamomum osmophloeum* |
| `growth_stage` | ENUM | ○ | `幼樹`/`小徑木`/`成樹` |
| `status` | ENUM | ○ | `存活`/`枯立`/`倒伏`/`缺測` |
| `planted_date` | TEXT | ○ | |
| `lat` / `lon` / `x_m` / `y_m` | DOUBLE | ○ | GPS（遮蔽）/ 樣區內相對座標 |
| `is_protected` | BOOL | ○ | |

> 動態量測（胸徑、樹高、健康）移至 `tree_measurement`，與個體靜態身分分離。

### 三、tree_measurement（樣木歷次量測，NEW）

對齊 XLSX「樹木\_歷次」與「土肉桂試驗\_長格式」。以 `(tree_id, season, stem_seq)` 為事件。

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `tree_id` | TEXT FK | ✓ | |
| `campaign_id` | TEXT FK | ○ | |
| `season` | TEXT | ✓ | 季別 `114Q3`/`114Q4`/`115Q1` |
| `measure_date` | DATE | ○ | 量測或推定季末日 |
| `stem_seq` | INT | ○ | 莖序（多幹；主幹=1）|
| `measure_part` | ENUM | ○ | `胸徑`/`地徑`（幼齡林採地徑）|
| `dbh_cm` / `height_m` | DOUBLE | ○ | 直徑 / 樹高 |
| `crown_w1_m` / `crown_w2_m` | DOUBLE | ○ | 冠幅 NS / EW |
| `crown_class` | ENUM | ○ | `優勢`/`共優勢`/`次冠層`/`被壓` |
| `health_grade_subjective_1_5` | INT | ○ | 1~5 主觀評分 |
| `damage_1` / `damage_2` | ENUM | ○ | 危害跡象（XLSX 代碼表）|
| `liana_cover_pct` | DOUBLE | ○ | 纏繞藤本覆蓋 % |
| `basal_area_m2` / `volume_m3` / `growth_increment` | DOUBLE | ○ | 斷面積 / 材積 / 生長量 |
| `status` | ENUM | ○ | `存活`/`枯立`/`倒伏`/`缺測`/`死亡` |
| `measured_by` | TEXT | ○ | |

### 四、regeneration_subplot（再生，NEW）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `subplot_id` | TEXT PK | ✓ | 例 `Q001` |
| `site_id` | TEXT FK | ✓ | |
| `subplot_area_m2` | DOUBLE | ○ | |
| `species_zh` / `species_sci` | TEXT | ◎ | |
| `height_class` | TEXT | ✓ | 例 `30-100 cm` |
| `count` | INT | ✓ | 該級距株數 |
| `survey_date` / `surveyor` | — | ○ | |

### 五、soil_environment（土壤與環境，NEW）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `survey_date` / `site_id` | — | ✓ | |
| `soil_temp_c` / `soil_moisture_pct` / `ph` / `conductivity` | DOUBLE | ○ | pH 範圍 2.5~9.5 |
| `texture` | ENUM | ○ | 土壤質地（12 類，XLSX 代碼表）|
| `bulk_density_g_cm3` / `litter_depth_cm` | DOUBLE | ○ | 體積密度 / 枯落物層厚 |
| `ground_cover_type` | ENUM | ○ | `裸地`/`草本`/`灌木`/`枯落物`/`岩石`/`苔蘚/地衣` |
| `photo` | TEXT | ○ | |

### 六、phenology（物候，NEW）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `survey_date` / `site_id` | — | ✓ | |
| `tree_id` | TEXT FK | ○ | 可為樣區層級觀測 |
| `phenology_stage` | ENUM | ✓ | `嫩葉`/`新梢`/`花蕾`/`開花`/`幼果`/`成熟果`/`落葉`/`休眠` |
| `flowering_amount` / `fruiting_amount` | INT | ○ | 開花量 / 結實量 |

### 七、disturbance（干擾事件，NEW）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `survey_date` / `site_id` | — | ✓ | |
| `disturbance_type` | ENUM | ✓ | `颱風`/`豪雨/崩塌`/`落石`/`獸害`/`病蟲害`/`砍伐`/`人為踩踏`/`火災`/`其他` |
| `severity_1_5` | INT | ✓ | 1 非常輕微 ~ 5 極嚴重 |
| `affected_tree_count` / `area_m2` | INT / DOUBLE | ○ | |

### 八、sample（樣品，NEW）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `sample_id` | TEXT PK | ✓ | 例 `S001` |
| `site_id` | TEXT FK | ✓ | |
| `tree_id` | TEXT FK | ○ | 可為處理組混合樣 |
| `tissue_type` | ENUM | ✓ | `葉`/`枝`/`根`/`樹皮`/`果實`/`其他` |
| `purpose` | TEXT | ○ | 化學成分 / 精油產率 / 含水率 |
| `fresh_weight_g` / `dry_weight_g` | DOUBLE | ○ | 鮮重 / 乾重 |
| `preservation` | TEXT | ○ | 例 `-20°C 冷凍` |

---

## 肆、試驗設計層

### 一、treatment（處理組）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `treatment_id` | ENUM PK | ✓ | `C0`/`P1`/`F150`/`P1F150` |
| `label_zh` | ENUM | ✓ | `對照`/`修剪矮化`/`施肥150g`/`修剪+施肥150g` |
| `pruning` | INT | ✓ | 0/1 |
| `fertilizer_g` | INT | ✓ | 0/150（全場 2×2，無 200/250g，見 [ADR-0004](decisions/0004-experimental-response-metrics.md)）|

### 二、plot（試驗單元）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `plot_id` | TEXT PK | ✓ | `<site>.<treatment>`，例 `115-12-1.C0` |
| `site_id` / `treatment_id` | FK | ✓ | |
| `tree_count` | INT | ○ | 約 30 |
| `plot_area_m2` | DOUBLE | ○ | 現階段不設子樣區（NULL）；site 面積＝列區總面積 |

### 三、campaign（採集場次）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `campaign_id` | TEXT PK | ✓ | `<site>_<season>`，例 `8-1-1_114Q3` |
| `site_id` / `season` | — | ✓ | 按樣區分批（[ADR-0005](decisions/0005-fixed-camera-station-sop.md)）|
| `capture_date` / `date_estimated` | DATE | ○ | 實際 / 推定季末日 |
| `operator` | TEXT | ○ | 合作社兼任 |

### 四、fixed_camera_station（固定攝點）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `station_id` | TEXT PK | ✓ | `<tree_id>.<station_label>` |
| `tree_id` | TEXT FK | ✓ | |
| `station_label` | ENUM | ✓ | `north_side`/`east_side`/`leaf_macro`/`top_view`/`south_side`/`west_side`/`pruning_site_close_up` |
| `azimuth_deg` / `distance_to_trunk_m` / `camera_height_m` / `pitch_deg` | DOUBLE | ○ | 成熟林攝距 5~7、幼齡林 2.5 |
| `status` | ENUM | ○ | `active`/`restored`/`abandoned` |

---

## 伍、影像 + 模型層

### 一、image（影像）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `image_id` | UUID PK | ✓ | |
| `tree_id` / `site_id` | TEXT FK | ✓ | v0.2 採新碼 |
| `plot_id` / `treatment_id` / `campaign_id` / `station_id` | FK | ○ | v0.2 新增試驗 FK |
| `capture_type` | ENUM | ✓ | `canopy`/`leaf_closeup`/`whole_plant`/`scale_ref` |
| `capture_datetime` | TIMESTAMPTZ | ✓ | |
| `view` | ENUM | ✓ | 4 方位 + `overhead`/`handheld` + `whole_north/south/east/west` |
| `device_id` / `session_id` | FK | ◎ | |
| `storage_uri` / `width_px` / `height_px` / `file_size_bytes` / `sha256` | — | ✓ | |
| `gps_lat` / `gps_lon` | DOUBLE | ○ | DB 存原始；API 遮蔽（見下註）|
| `scale_object_type` / `scale_object_size_mm` | — | ◎ | 葉片必填 |
| `has_color_card` / `weather` / `quality_pass` / `quality_issues` | — | ○ | |

> **GPS 隱私政策（[ADR-0001 議題 5](decisions/0001-open-questions.md)）**：`gps_lat`/`gps_lon` 在 DB **永遠儲存原始值**，**不**在 DB 層遮蔽。API serialization 階段依角色裁切：admin→`exact`、認證研究者→`town`、公開/訪客→`county`，並附 `gps_precision`。同規則適用 `tree.lat/lon`、`site.centroid_lat/lon`。未脫敏精確位置與保育類位置不進公開層（Cloud.md 伍）。

### 二、analysis_run（推論執行）

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `run_id` | UUID PK | ✓ | |
| `image_id` / `model_id` / `model_version` | FK / TEXT | ✓ | |
| `started_at` / `finished_at` | TIMESTAMPTZ | ✓ | |
| `status` | ENUM | ✓ | `queued`/`running`/`succeeded`/`failed` |
| `mask_uri` / `metrics_json` / `inference_seconds` / `device` | — | ○ | |

### 三、image_metric（影像指標主表）

共用欄位：`image_id` FK、`model_id`、`run_id` FK。各模型欄位：

- **CanopySeg**：`canopy_area_px`、`canopy_ratio`、`veg_cover_ratio`、`green_ratio`、`yellow_ratio`、`brown_ratio`、`abnormal_hotspot_count`、`abnormal_hotspot_max_area_ratio`
- **LeafInst**：`leaf_count`、`mm_per_pixel`、`scale_object_detected`、`leaf_area_mean/std/p25/p50/p75_cm2`、`leaf_length_mean_mm`、`leaf_width_mean_mm`
- **LeafDefect**：`lesion_ratio_mean`、`chlorosis_ratio_mean`、`necrosis_ratio_mean`、`hole_ratio_mean`、`total_defect_ratio_mean`、`health_score_global_mean`、`health_score_species_mean`、`health_grade`、`weights_config_id`

> v0.2 響應指標（14 項 A/B/C 類 + health_score）定義見 [ADR-0004](decisions/0004-experimental-response-metrics.md)，彙總入 `treatment_response_summary`。

### 四、leaf_instance（葉片實例）

`instance_id` PK、`image_id` FK、`polygon_json`（葉柄併入，[ADR-0001 議題2](decisions/0001-open-questions.md)）、`bbox_json`、`area_px`、`area_cm2`、`length_mm`、`width_mm`、`lesion/chlorosis/necrosis/hole_ratio`、`health_score_global`、`health_score_species`、`health_grade`。

### 五、tree_image_metric_daily（單棵樹單日影像指標，改名自 tree_daily_summary）

> **v0.2 變更**：原 `tree_daily_summary` 改名 `tree_image_metric_daily`，明確為「影像衍生」並與人工量測 `tree_measurement` 分離。舊 API 路徑保留別名至 v0.3。

`tree_id`+`date` PK；`image_count_canopy/leaf`、`canopy_ratio_mean`、`green/yellow/brown_ratio_mean`、`leaf_count_total`、`leaf_area_mean_cm2`、`health_score_global_mean`、`health_score_species_mean`、`health_grade`、`risk_flag`、`risk_reasons`。

### 六、annotation（標註）

`annotation_id` PK、`image_id` FK、`annotator`、`category`、`geometry_json`、`area_px`、`version`、`is_gold`、`created_at`。

### 七、model（模型版本）

`model_id` PK、`task`（`canopy_seg`/`leaf_inst`/`leaf_defect`/`plant_structure`）、`version`、`framework`、`weights_uri`、`train_dataset_id`、`eval_metrics_json`、`released_at`、`is_active`、`model_card_uri`。

---

## 陸、試驗對照分析層（NEW）

### 一、treatment_response_summary

每處理組（plot）× 每場次（season）的 14 響應指標 + health_score 彙總，供 ANOVA。

| 欄位 | 型別 | 說明 |
|------|------|------|
| `summary_id` | TEXT | 建議 `<plot_id>_<season>` |
| `site_id` / `plot_id` / `treatment_id` / `campaign_id` / `season` | — | 範圍鍵 |
| `n_trees` | INT | 有效樣樹數 |
| `metrics` | JSONB | 15 指標，各為 `{mean, sd, n}`（A1~A5、B1~B5、C1~C4、health_score）|
| `manual_reference` | JSONB | 人工量測對照 `{dbh_cm, height_m, volume_m3}`，驗影像相關性 r≥0.7 |

### 二、experiment_anova_result

| 欄位 | 型別 | 說明 |
|------|------|------|
| `experiment_id` / `site_scope` / `season` | — | 分析範圍 |
| `metric` | TEXT | 受測指標 |
| `factor` | ENUM | `pruning`/`fertilizer`/`pruning_x_fertilizer` |
| `df_between` / `df_within` | INT | |
| `f_value` / `p_value` / `effect_size` | DOUBLE | partial η² |
| `significant` / `alpha` | BOOL / DOUBLE | α 預設 0.05 |
| `posthoc` | JSONB[] | LSD/Tukey 多重比較 |

---

## 柒、Enum 定義

```sql
-- 影像層（v0.2 擴充）
CREATE TYPE capture_type_t AS ENUM ('canopy', 'leaf_closeup', 'whole_plant', 'scale_ref');
CREATE TYPE view_t AS ENUM ('north','south','east','west','overhead','handheld',
                            'whole_north','whole_south','whole_east','whole_west');
CREATE TYPE scale_obj_t  AS ENUM ('a4_grid','coin_5twd','coin_10twd','ruler','other');
CREATE TYPE weather_t    AS ENUM ('sunny','cloudy','overcast','rain','fog');
CREATE TYPE run_status_t AS ENUM ('queued','running','succeeded','failed');
CREATE TYPE model_task_t AS ENUM ('canopy_seg','leaf_inst','leaf_defect','plant_structure');

-- 林地實體層（對齊 XLSX 代碼表）
CREATE TYPE tree_status_t   AS ENUM ('存活','枯立','倒伏','缺測','死亡');
CREATE TYPE growth_stage_t  AS ENUM ('幼樹','小徑木','成樹');
CREATE TYPE crown_class_t   AS ENUM ('優勢','共優勢','次冠層','被壓');
CREATE TYPE damage_t        AS ENUM ('無','折幹/倒伏','傷皮/刮傷','中心空洞','病蟲危害','土壤擾動','人為干擾','其他');
CREATE TYPE phenology_t     AS ENUM ('嫩葉','新梢','花蕾','開花','幼果','成熟果','落葉','休眠');
CREATE TYPE disturbance_t   AS ENUM ('颱風','豪雨/崩塌','落石','獸害','病蟲害','砍伐','人為踩踏','火災','其他');
CREATE TYPE aspect_t        AS ENUM ('N','NE','E','SE','S','SW','W','NW','平地');
CREATE TYPE slope_pos_t     AS ENUM ('谷','下坡','中坡','上坡','稜','平地');
CREATE TYPE soil_texture_t  AS ENUM ('Sand','Loamy sand','Sandy loam','Loam','Silt loam','Silt',
                                     'Sandy clay loam','Clay loam','Silty clay loam','Sandy clay','Silty clay','Clay');
CREATE TYPE gps_datum_t     AS ENUM ('WGS84','TWD97');
CREATE TYPE plot_type_t     AS ENUM ('永久樣區','臨時樣區');

-- 試驗設計層
CREATE TYPE treatment_id_t  AS ENUM ('C0','P1','F150','P1F150');
CREATE TYPE station_label_t AS ENUM ('north_side','east_side','leaf_macro','top_view',
                                     'south_side','west_side','pruning_site_close_up');
CREATE TYPE station_status_t AS ENUM ('active','restored','abandoned');
CREATE TYPE anova_factor_t  AS ENUM ('pruning','fertilizer','pruning_x_fertilizer');
```

> `crown_status_t`（v0.1 `healthy/stressed/damaged/dead`）由 `tree_status_t`（XLSX 對齊）取代，需 migration script（非向後相容）。

---

## 捌、中英欄名對應字典（XLSX → TreeVision）

| XLSX 中文欄名 | TreeVision 英文欄名 | 表 |
|--------------|--------------------|----|
| 樣區代碼 | site_id（場域）/ plot_id（試驗單元）| site / plot |
| 樣木代碼 | tree_id | tree |
| 樣木編號 | tree_no | tree |
| 莖序 | stem_seq | tree_measurement |
| 標籤號 | tree_tag | tree |
| 樹種 | species_zh / species_sci | tree |
| 生長階段 | growth_stage | tree |
| 狀態 | status | tree / tree_measurement |
| 胸徑\_cm / 直徑\_cm | dbh_cm | tree_measurement |
| 樹高\_m | height_m | tree_measurement |
| 冠幅 NS / EW\_m | crown_w1_m / crown_w2_m | tree_measurement |
| 樹冠級 | crown_class | tree_measurement |
| 健康等級\_1到5 | health_grade_subjective_1_5 | tree_measurement |
| 危害1 / 危害2 | damage_1 / damage_2 | tree_measurement |
| 纏繞藤本覆蓋% | liana_cover_pct | tree_measurement |
| 材積 / 生長量 | volume_m3 / growth_increment | tree_measurement |
| 量測日期 / 季別 | measure_date / season | tree_measurement |
| 處理代碼 / 處理中文 | treatment_id / label_zh | treatment |
| 修剪 / 施肥g | pruning / fertilizer_g | treatment |

---

## 玖、輸出檔案格式（offline）

| 檔案 | 結構 |
|------|------|
| `outputs/per_image/{date}_{run}.parquet` | 每張影像一筆＝`image_id` + §伍-三共用 + 各模型欄位 |
| `outputs/per_tree_daily/{date}_{run}.parquet` | 對應 §伍-五 `tree_image_metric_daily` |
| `outputs/per_site/{date}_{run}.parquet` | `site_id`+`date` PK、`tree_count`、`tree_count_high_risk`、`green/yellow_ratio_site_mean`、`health_score_site_mean` |
| `outputs/per_treatment/{exp}_{season}.parquet` | 對應 §陸-一 `treatment_response_summary`（試驗對照分析）|

---

## 拾、JSON Schema 檔（機器可讀，[`../schemas/`](../schemas/)）

| 層 | 檔案 |
|----|------|
| 林地實體 | `site_registry`、`tree_registry`、`tree_measurement`、`regeneration_subplot`、`soil_environment`、`phenology`、`disturbance`、`sample` |
| 試驗設計 | `treatment`、`plot`、`campaign`、`fixed_camera_station` |
| 影像模型 | `image_metadata`、`analysis_result.canopyseg`、`analysis_result.leafinst`、`analysis_result.leafdefect` |
| 試驗對照 | `treatment_response_summary`、`experiment_anova_result` |

> 共 18 檔，均以 `jsonschema` Draft 2020-12 驗證，並以「土肉桂試驗\_長格式」真實資料 round-trip 通過。對應 CSV 範本見 [`../metadata/`](../metadata/)。

---

## 拾壹、變更紀錄

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-04-29 | v0.1 | 初版：9 實體（site/tree/image/analysis_run/image_metric/leaf_instance/tree_daily_summary/annotation/model）|
| 2026-06-13 | v0.2 | 重構四層架構、對齊 XLSX 10 工作表；新增 14 實體；ID 改既有試驗碼；enum 對齊代碼表；`tree_daily_summary`→`tree_image_metric_daily`；補中英字典。對應 18 JSON schema + 13 CSV 模板（[ADR-0003](decisions/0003-schema-alignment-with-xlsx.md)）|
