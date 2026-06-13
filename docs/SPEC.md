# TreeVision 工程開發規格書（SRS / PRD）

| 項目 | 內容 |
|------|------|
| 專案代號 | TreeVision |
| 中文名稱 | 林木多尺度 AI 影像健康監測平台 |
| 英文名稱 | Multi-scale AI Tree Health Monitoring Platform |
| 文件版本 | **v0.2（草案）** |
| 文件日期 | 2026-05-04 |
| 文件狀態 | **草案** — 因場域定錨於 114-115 年臺中分署土肉桂試驗，相對 v0.1 進行第二輪改寫；待計畫主持人審查 [ADR-0002~0005](decisions/) |
| 適用對象 | 平台使用者（林業工作者、研究者、計畫主持人）、工程團隊（前後端、AI 模型）、資料管理員 |
| **場域定錨** | **大雪山林業合作社土肉桂試驗 4 樣區**（見 [ADR-0002](decisions/0002-site-species-application-scope.md) + [references/cinnamon-trial-context.md](../references/cinnamon-trial-context.md)） |

---

## 壹、產品定位與目標

### 一、產品定位

TreeVision 是一個結合**樹冠尺度**（canopy-level）與**葉片尺度**（leaf-level）影像的 AI 分析平台，將林木健康監測從「人工目視描述」轉為「可量化、可追蹤、可驗證」的數據工作流。

### 二、解決的問題

| 痛點 | TreeVision 回應方式 |
|------|--------------------|
| 樹木健康評估高度依賴主觀判斷 | 提供標準化的可量化指標（樹冠投影面積、葉片病斑佔比、健康分數） |
| 影像資料無法追蹤同一棵樹的時序變化 | 以 `tree_id` 為核心串接歷次影像 |
| 葉片量測曠日廢時 | 透過尺度物自動換算 mm/pixel，AI 直接輸出葉面積、長寬 |
| 巡檢報告格式不一 | 制式 PDF / Excel 報表自動產出 |
| 模型升級後舊資料無從比對 | 模型版號寫入每筆推論結果，支援追溯 |

### 三、設計原則

| 原則 | 描述 |
|------|------|
| **可量化** | 所有分析結果以結構化欄位儲存，可被統計、可被查詢 |
| **可追蹤** | 每筆推論紀錄包含模型版號、輸入影像 hash、執行時間 |
| **可驗證** | 提供標註與推論的差異報表（混淆矩陣、IoU、誤差直方圖） |
| **可解釋** | 健康分數由公開公式組合，避免黑箱 |
| **隱私保護** | 場域 GPS 預設遮蔽，僅授權使用者可見 |

### 四、非目標（Non-goals）

- 不取代專家現場勘查（提供決策支援，不下最終判斷）
- 不做物種辨識（v0.2 鎖定土肉桂單樹種，未來其他樹種以 [ADR-0002](decisions/0002-site-species-application-scope.md) 平台層擴展鉤子處理）
- 不做 LiDAR、衛星遙測（v1 僅處理地面與低空 UAV 可見光影像）
- 不取代化學分析（精油含量 / 成分 / 土壤養分仍由實驗室處理，TreeVision 僅補影像可推得指標）
- 不提供商業 SaaS 多租戶（v1 為單機構部署）

### 五、v0.2 場域定錨（NEW）

| 維度 | 定錨值 |
|------|-------|
| 場域 | 林業及自然保育署臺中分署 / 大雪山林業生產合作社 |
| 樣區 | 4 個官方林班：**115-12-1（成熟林）+ 117-28-1 / 1-2-3 / 8-1-10（幼齡林）** |
| 樹種 | 土肉桂（*Cinnamomum osmophloeum* Kanehira） |
| 林齡 | 1 個 15 年生 + 3 個 1~2 年生 |
| 樣樹規模 | 預估 300 株（120 + 60 × 3） |
| 應用主軸 | 林下經濟（NTFP）試驗對照監測 |
| 試驗設計 | CRBD 雙因子析因（修剪 × 施肥 150/200/250g） |
| 計畫年度 | 民國 114 年 8 月 1 日 ~ 115 年 8 月 31 日（兩年期，可延伸） |

> 詳見 [`references/cinnamon-trial-context.md`](../references/cinnamon-trial-context.md) — 場域、試驗設計、官方調查表 schema、修剪技術 SOP 完整彙整。

---

## 貳、使用者與情境

### 一、主要使用者角色（Persona）

| 角色 | 主要任務 | 技術背景 |
|------|----------|----------|
| **林業工作者 / 巡檢員** | 上傳影像、查看樹木健康履歷、下載巡檢報告 | 一般電腦操作 |
| **研究者 / 教師** | 建立監測專案、產生統計報表、匯出資料做後續分析 | 中等（會用 Excel、會看 CSV） |
| **資料管理員 / 工程師** | 模型升級、資料治理、API 整合 | 高（會 SQL、會 Python） |
| **審查委員 / 計畫主持人** | 查看儀表板、產生計畫進度報告 | 一般電腦操作 |

### 二、典型工作流程（User Journey）

#### 流程 A：田野調查當日上傳

```
巡檢員拍攝 → 回辦公室 → 開 TreeVision 上傳頁 → 拖曳照片
            → 系統自動讀 EXIF → 巡檢員填 tree_id 與 view
            → 送出後排程進入 AI 分析佇列
            → 隔日收到單棵樹健康摘要 email / 通知
```

#### 流程 B：研究者建立長期監測

```
研究者建立專案 → 註冊樹木 tree_id → 設定樣本（10~50 棵）
              → 月度上傳影像 → 系統自動彙整時間序列
              → 匯出年度報告（PDF + CSV）
```

#### 流程 C：審查委員快速複查

```
打開儀表板 → 看場域健康熱點地圖 → 點選異常樹
          → 看樹木履歷（多次影像對比） → 下載 PDF 帶到審查會議
```

#### 流程 D（NEW）：試驗對照監測（v0.2 主軸）

```
公會 / 合作社團隊到樣區 → 找固定攝點標樁 → 依 SOP 拍 3+ 攝點
                       → 平台自動計算 14 項響應指標
                       → 跨場次資料累積後 → 觸發 ANOVA 分析
                       → 計畫主持人下載「試驗對照分析報表」
                       → 比較處理組（修剪 ± × 施肥 ±）的響應差異
```

> 流程 D 是 v0.2 的核心 use case，由 [ADR-0004](decisions/0004-experimental-response-metrics.md) 與 [ADR-0005](decisions/0005-fixed-camera-station-sop.md) 支援。

---

## 參、系統範圍（Scope）

### 一、v1 MVP 範圍

| 模組 | 包含 | 不包含 |
|------|------|--------|
| 影像上傳 | 單張、批次（≤ 50 張）、metadata 表單 | 行動版 App、即時相機串流 |
| AI 分析 | CanopySeg、LeafInst、LeafDefect 三模型 | 物種辨識、病害分類 |
| 樹木資料庫 | tree_id 主檔、影像關聯、簡易 GPS | 完整 GIS 圖層套疊 |
| 儀表板 | 場域層級摘要、樹木層級時序 | 多租戶、組織管理 |
| 報表 | PDF（影像／樹／場域）+ CSV/Parquet | Word、客製樣板 |
| API | REST，內部使用 | 公開 API、OAuth、WebHook |
| 部署 | 單機構雲端（Cloud Run / VPS） | 多區域、SLA、災難恢復 |

### 二、後續版本路線

詳見 [roadmap.md](roadmap.md)。

---

## 肆、影像資料規格

### 一、影像類型（capture_type）

| 類型代碼 | 說明 | 典型距離 | 用途 | v0.2 變更 |
|----------|------|----------|------|---------|
| `canopy` | 樹冠影像（地面仰拍、UAV 俯拍、整棵樹側面） | 5~30 m | CanopySeg | 既有 |
| `leaf_closeup` | 葉片近拍（含尺度物 / 色卡） | 0.1~0.5 m | LeafInst + LeafDefect | 既有 |
| `whole_plant` | **整株影像**（幼齡林全株框入；成熟林限樹冠 + 主幹） | 2.5~10 m | PlantStructure + LeafInst + CanopySeg | **NEW v0.2** |
| `scale_ref` | **尺度物校正影像**（攝點地面置標準尺，每場次 ≥ 1 張） | 任意 | 量測校正 | **NEW v0.2** |
| `pruning_close_up` | 修剪部位特寫（含切口入鏡） | 0.3~0.5 m | wound_seg（v2+） | **NEW v0.2，v2 啟用** |

### 二、影像格式與品質要求

| 項目 | 要求 |
|------|------|
| 檔案格式 | JPEG（sRGB）、HEIC（系統自動轉 JPEG）、PNG（限標註用） |
| 最低解析度 | 樹冠 ≥ 3000×2000 px；葉片近拍 ≥ 4000×3000 px |
| 最大檔案大小 | 單檔 ≤ 30 MB |
| 色彩空間 | sRGB |
| EXIF | 須保留拍攝日期、相機型號、GPS（若有） |
| 葉片近拍尺度物 | 必須含已知尺寸的物件（A4 方格紙 / 5 元硬幣 / 標尺）並完全在畫面內 |

### 三、命名規則

#### v0.1 規則（保留向後相容，臨時拍攝可用）

```
{site_id}_{tree_id}_{capture_type}_{YYYYMMDD}_{HHMM}_{view}_{seq}.{ext}
```

#### v0.2 規則（試驗監測必用，含 station_id）

```
{station_id}_{YYYYMMDD}_{HHMM}_{seq}.{ext}
```

其中 `station_id = {site_id}.{tree_id}.{station_label}`，例：

```
115-12-1.T0001.north_side_20260601_1430_001.jpg
```

> 完整命名規則與固定攝點定義見 [ADR-0005](decisions/0005-fixed-camera-station-sop.md)、[`raw/README.md`](../raw/README.md)。

### 四、Metadata 必填欄位

| 欄位 | 類型 | 必填 | 範例 | v0.2 變更 |
|------|------|------|------|---------|
| `image_id` | string (UUID) | ✓（系統產生） | `img_01H...` | 既有 |
| `tree_id` | string | ✓ | `115-12-1.T0001` | 命名規範改 |
| `site_id` | string | ✓ | `115-12-1` | 對齊官方林班編號 |
| `plot_id` | string | ✓ | `115-12-1.P+F+` | **NEW** |
| `treatment_id` | string | ✓ | `P+F200` | **NEW** |
| `campaign_id` | string | ✓ | `115-12-1_20260601` | **NEW** |
| `station_id` | string | ✓ | `115-12-1.T0001.north_side` | **NEW** |
| `capture_type` | enum | ✓ | `whole_plant` / `leaf_closeup` / `scale_ref` / `canopy` | 擴充 |
| `capture_datetime` | ISO8601 | ✓ | `2026-05-01T14:30:00+08:00` | 既有 |
| `view` | enum | ✓ | `north`/`south`/`east`/`west`/`overhead`/`handheld`/`whole_north`/`whole_east` | 擴充 |
| `device_id` | string | ✓ | `iphone15pro_user01` | 既有 |
| `gps_lat` / `gps_lon` | float | △（隱私可遮罩） | 24.5234, 121.3456 | 既有 |
| `scale_object_type` | enum | ◎（葉片必填） | `a4_grid`/`coin_5twd`/`ruler` | 既有 |
| `scale_object_size_mm` | float | ◎（葉片必填） | 297（A4 長邊） | 既有 |
| `has_color_card` | bool | ◎（葉片建議） | true/false | 既有 |
| `weather` | enum | ○ | `sunny`/`cloudy`/`overcast`/`rain` | 既有 |
| `actual_distance_m` | float | ◎（whole_plant 必填） | 2.5 | **NEW**：實測攝距，用於指標校正 |
| `actual_camera_height_m` | float | ◎（whole_plant 必填） | 1.5 | **NEW**：相機鏡頭離地高 |
| `obstruction_flag` | bool | ○ | false | **NEW**：是否被周遭物體部分遮擋 |
| `note` | string | ○ | 自由文字 | 既有 |

完整欄位字典見 [data-schema.md](data-schema.md) 與 [ADR-0003](decisions/0003-schema-alignment-with-xlsx.md)（含 XLSX 中英對應字典）。

---

## 伍、AI 分析模組規格

### 一、CanopySeg（樹冠分析模型）

#### 任務類型
Multi-class semantic segmentation。

#### 輸入
單張 `canopy` 影像（resize 至 1024×1024 或 long-side 1536）。

#### 輸出 Mask（每像素一類）

| 類別 | ID | 說明 |
|------|----|----|
| background | 0 | 非樹冠 |
| canopy_other | 1 | 樹冠範圍內但無植生（枝幹、落葉縫） |
| veg_green | 2 | 綠色健康植生 |
| veg_yellow | 3 | 黃化植生 |
| veg_brown | 4 | 褐化／乾枯植生 |

#### 衍生指標

| 指標 | 計算 | 單位 |
|------|------|------|
| canopy_area_px | (canopy_other + veg_*) 像素數 | px² |
| canopy_ratio | canopy_area_px / 影像總像素 | 0~1 |
| veg_cover_ratio | veg_* 像素 / canopy_area_px | 0~1 |
| green_ratio | veg_green / (veg_green + veg_yellow + veg_brown) | 0~1 |
| yellow_ratio | veg_yellow / 同上 | 0~1 |
| brown_ratio | veg_brown / 同上 | 0~1 |
| abnormal_hotspot | yellow + brown 的連通域，面積 ≥ 影像 0.5% | bbox 列表 |

#### 模型選型建議
- baseline：U-Net / DeepLabV3+（ResNet-50 backbone）
- 進階：SegFormer（B2/B3）、Mask2Former
- 訓練資料：自有標註 + 公開資料集（PASCAL Context、ADE20K 中的 vegetation 類）作 pretrain

### 二、LeafInst（葉片實例分割 + 尺度物偵測）

#### 任務類型
Instance segmentation（葉片）+ Object detection（尺度物）。

#### 輸入
單張 `leaf_closeup` 影像（resize 至 long-side 2048）。

#### 輸出

```json
{
  "leaves": [
    {"instance_id": 1, "polygon": [...], "bbox": [x,y,w,h], "area_px": 12345}
  ],
  "scale_objects": [
    {"type": "a4_grid", "bbox": [x,y,w,h], "ref_size_mm": 297.0, "confidence": 0.96}
  ],
  "mm_per_pixel": 0.234
}
```

#### 衍生指標（每片葉）

| 指標 | 計算 |
|------|------|
| leaf_area_cm² | area_px × (mm_per_pixel/10)² |
| leaf_length_mm | bbox 旋轉後最長軸 × mm_per_pixel |
| leaf_width_mm | 最短軸 × mm_per_pixel |
| leaf_aspect | length / width |

#### 影像層級彙總

| 指標 | 說明 |
|------|------|
| leaf_count | 偵測到的葉片數 |
| leaf_area_mean / std / p25 / p50 / p75 | 葉面積分布 |

#### 模型選型建議
- baseline：Mask R-CNN（ResNet-50 FPN）
- 進階：Mask2Former、YOLOv8-Seg、SAM2 + 微調
- 尺度物偵測：YOLOv8 small（4 類：a4_grid / coin_5twd / coin_10twd / ruler）

### 三-A、PlantStructure（株型解析模型，v0.2 NEW）

#### 任務類型
Multi-task：(a) 全株分割（whole-plant segmentation）+ (b) 株高 / 冠幅 / 主幹偵測。

#### 輸入
單張 `whole_plant` 影像（同 station_id 系列，攝距與相機高度由 metadata 提供）。

#### 輸出

| 通道 | 說明 |
|------|------|
| segmentation_whole | 整株遮罩（樹冠 + 主幹 + 枝條） |
| segmentation_canopy | 樹冠子遮罩 |
| segmentation_trunk | 主幹子遮罩 |
| height_top_px / height_bottom_px | 株頂與根頸像素位置 |
| crown_top_px / crown_bottom_px | 樹冠範圍像素 |
| trunk_centerline_px | 主幹中心線像素點集 |

#### 衍生指標

| 指標 | 計算 | 對應 ADR-0004 |
|------|------|-------------|
| `plant_height_cm` | (height_top_px - height_bottom_px) × cm_per_pixel | C1 |
| `crown_height_ratio` | (crown_bottom_px - crown_top_px) / (height_top_px - height_bottom_px) | C3 |
| `crown_w1_px` (北側攝點) / `crown_w2_px` (東側攝點) | 樹冠水平最大寬度 | （與 XLSX 樹冠 W1/W2 對齊） |

#### 模型選型建議
- baseline：UPerNet + ResNet-50 backbone，多 head 同時輸出 segmentation + keypoint
- 進階：Mask2Former 多任務、HRNet（株高基準線細精度）
- 訓練資料：自有標註（土肉桂幼齡林為主）

> 詳細指標規格見 [ADR-0004](decisions/0004-experimental-response-metrics.md) §C 類株型生長類。

### 三、LeafDefect（葉片病徵分析）

#### 任務類型
Multi-label semantic segmentation（同一像素可同時有多種病徵）。

#### 輸入
單片葉的 ROI（由 LeafInst 切出）。

#### 輸出 Mask（多通道二元）

| 通道 | 說明 |
|------|------|
| lesion | 病斑 |
| chlorosis | 黃化 |
| necrosis | 壞死（黑褐色斑塊） |
| hole | 破洞、缺損 |

#### 衍生指標（每片葉）

| 指標 | 計算 | 單位 |
|------|------|------|
| lesion_ratio | lesion 像素 / 葉片像素 | 0~1 |
| chlorosis_ratio | chlorosis 像素 / 葉片像素 | 0~1 |
| necrosis_ratio | necrosis 像素 / 葉片像素 | 0~1 |
| hole_ratio | hole 像素 / 葉片像素 | 0~1 |
| total_defect_ratio | 任一病徵 / 葉片像素 | 0~1 |
| **health_score** | 公式如下 | 0~100 |

#### 健康分數公式（v1 版，全域權重）

```
health_score_global = 100
             - 100 × (
                 0.40 × lesion_ratio
               + 0.30 × necrosis_ratio
               + 0.20 × chlorosis_ratio
               + 0.10 × hole_ratio
               )
clamp 到 [0, 100]
```

> 依 [ADR-0001 議題 3](decisions/0001-open-questions.md) 決議採**兩階段**設計：
>
> - **v1**：所有樹種共用上述全域權重，輸出至 `health_score_global` 欄位（必填）。權重抽至 `models/LeafDefect/config.yaml` 的 `health_weights` 區塊，**不寫死於程式碼**。
> - **v1.5+**：對樣本量足夠（≥ 100 片標註葉 × 多時段）的樹種推導樹種特化權重，輸出至 `health_score_species` 欄位（v1 為 NULL，校正後填入）。
> - 兩欄位並存，保留跨版本可比性；分級表（A~E）目前以 `health_score_global` 為計算基準。

#### 健康等級分級

| 分數區間 | 等級 | 顏色 |
|----------|------|------|
| 90~100 | A 健康 | 綠 |
| 75~89 | B 輕微異常 | 黃綠 |
| 60~74 | C 明顯異常 | 黃 |
| 40~59 | D 中度受損 | 橙 |
| 0~39 | E 嚴重受損 | 紅 |

---

## 陸、資料模型（核心 ER）

### 一、實體與主鍵（v0.2 改寫）

依 [ADR-0003](decisions/0003-schema-alignment-with-xlsx.md) 採四層架構：

#### (一) 林地實體層（對齊 XLSX）

| 實體 | 主鍵 | 說明 |
|------|------|------|
| Site | `site_id` | 場域（事業區 + 林班，如 `115-12-1`） |
| Tree | `tree_id`（如 `115-12-1.T0001`） | 單棵樹個體 |
| TreeMeasurement | `tree_id` + `measure_date` | 人工 / 影像基準量測（樹高、DBH、健康等級） |
| RegenerationSubplot | `subplot_id` | 自然更新 / 幼苗 |
| SoilEnvironment | `site_id` + `measure_date` | 土壤理化 |
| Phenology | `tree_id` + `observe_date` | 物候觀察 |
| Disturbance | `disturbance_id` | 颱風 / 病蟲 / 人為干擾紀錄 |
| Sample | `sample_id` | 化學分析樣品庫 |

#### (二) 試驗設計層

| 實體 | 主鍵 | 說明 |
|------|------|------|
| Treatment | `treatment_id` | 處理組（如 `P+F200`） |
| Plot | `plot_id` | 試驗單元（site × treatment 交集） |
| Campaign | `campaign_id` | 採集場次 |
| FixedCameraStation | `station_id` | 固定攝點（如 `115-12-1.T0001.north_side`） |

#### (三) 影像 + 模型層

| 實體 | 主鍵 | 說明 |
|------|------|------|
| Device | `device_id` | 拍攝設備 |
| Image | `image_id`（UUID） | 單張影像 |
| AnalysisRun | `run_id`（UUID） | 一次模型推論 |
| ImageMetric | `image_id` + `model_id` | 單張影像指標彙總 |
| LeafInstance | `instance_id`（UUID） | 葉片實例 |
| TreeImageMetricDaily | `tree_id` + `date` | 單棵樹單日影像指標彙總（取代 v0.1 TreeDailySummary） |
| Annotation | `annotation_id` | 標註紀錄 |
| Model | `model_id` + `version` | 模型版本 |

#### (四) 試驗對照分析層（NEW v0.2）

| 實體 | 主鍵 | 說明 |
|------|------|------|
| TreatmentResponseSummary | `treatment_id` + `campaign_id` + `metric_id` | 每處理組 × 場次 × 響應指標 |
| ExperimentAnovaResult | `experiment_id` + `metric_id` | ANOVA 結果（F、p、effect size） |

### 二、關聯（v0.2 改寫）

```
Site 1 ── n Tree
Site 1 ── n Plot
Treatment 1 ── n Plot
Plot 1 ── n Tree

Tree 1 ── n FixedCameraStation
Tree 1 ── n TreeMeasurement
Tree 1 ── n Phenology

FixedCameraStation 1 ── n Image
Campaign 1 ── n Image
Device 1 ── n Image

Image 1 ── n AnalysisRun
AnalysisRun 1 ── 1 ImageMetric
AnalysisRun 1 ── n LeafInstance
AnalysisRun n ── 1 Model
Image 1 ── n Annotation

Tree + date 1 ── 1 TreeImageMetricDaily
Treatment + Campaign + Metric 1 ── 1 TreatmentResponseSummary
Experiment + Metric 1 ── 1 ExperimentAnovaResult
```

詳細欄位定義見 [data-schema.md](data-schema.md) 與 [ADR-0003](decisions/0003-schema-alignment-with-xlsx.md)。

---

## 柒、API 規格（REST）

### 一、設計原則

- 版本化：`/api/v1/...`
- 認證：JWT Bearer Token（v1）→ OAuth 2.0（v2）
- 內容類型：`application/json`，影像上傳 `multipart/form-data`
- 統一錯誤格式：`{"error": {"code": "...", "message": "...", "details": {...}}}`
- 分頁：`?page=1&page_size=20`

### 二、主要端點（節錄）

| Method | Path | 用途 |
|--------|------|------|
| POST | `/api/v1/images` | 上傳影像（multipart） |
| GET | `/api/v1/images/{image_id}` | 取得單張影像 metadata + 分析結果 |
| POST | `/api/v1/images/{image_id}/analyze` | 觸發推論（非同步） |
| GET | `/api/v1/runs/{run_id}` | 查推論進度 |
| GET | `/api/v1/trees/{tree_id}` | 樹木個體資料 + 歷史影像 |
| GET | `/api/v1/trees/{tree_id}/summary?date=...` | 單日彙總 |
| GET | `/api/v1/sites/{site_id}/dashboard` | 場域儀表板資料 |
| POST | `/api/v1/reports` | 產生報表（指定範圍與類型） |

完整 API 定義見 [api.md](api.md)（含請求／回應 schema）。

---

## 捌、技術選型（建議）

### 一、總體架構

```
[ Browser / Mobile Web ]
          ↓ HTTPS
[ Frontend (Next.js + Tailwind) ]
          ↓ REST
[ Backend API (FastAPI / Python) ]
          ↓
┌─────────┬─────────────┬───────────┐
│ PostgreSQL    Object Storage   Job Queue
│ (metadata,    (raw/processed   (Celery /
│  metrics)     images, masks)    Redis Queue)
└─────────┴─────────────┴───────────┘
                     ↓
            [ Inference Workers ]
            (PyTorch / ONNX Runtime)
                     ↓
            [ Trained Models ]
```

### 二、技術棧建議

| 層 | 建議 | 替代 |
|----|------|------|
| 前端 | Next.js 14 + Tailwind CSS + shadcn/ui | Vue / Svelte |
| 圖表 | Recharts / Plotly | ECharts |
| 後端 API | FastAPI（Python 3.11+） | Django REST、NestJS |
| 資料庫 | PostgreSQL 16 + PostGIS（GPS 用） | MySQL（無空間） |
| 物件儲存 | Google Cloud Storage / S3 | 本機磁碟 + 備份 |
| 任務佇列 | Celery + Redis | RQ、Dramatiq |
| 模型框架 | PyTorch 2.x，部署用 ONNX Runtime | TensorFlow |
| 容器化 | Docker + docker-compose | Podman |
| 部署 | Cloud Run（後端） + Cloud Storage（影像） + Vercel（前端） | GCE VPS、AWS Fargate |
| CI/CD | GitHub Actions | GitLab CI |

### 三、安全與資料治理

| 項目 | 措施 |
|------|------|
| 認證 | JWT，token 24h 有效；刷新 token 30d |
| 授權 | RBAC（admin / researcher / viewer） |
| 影像隱私 | DB 永遠儲存原始 GPS；遮蔽僅在 API serialization 時做（[ADR-0001 議題 5](decisions/0001-open-questions.md)）。三層粒度：admin → `exact`、認證研究者 → `town`（鄉鎮級）、公開/訪客 → `county`（縣市級）；API 回應一律附 `gps_precision` 欄位供前端決定顯示樣式 |
| 資料備份 | 每日增量、每週全量；保留 90 天 |
| 稽核 | API 存取記錄存 90 天；模型推論不可變更歷史紀錄 |
| 個資 | 不蒐集個人辨識資料；上傳者僅以 user_id 紀錄 |

---

## 玖、品質與驗收

### 一、模型驗收標準（v1）

| 模型 | 指標 | 目標值 |
|------|------|--------|
| CanopySeg | mIoU（5 類） | ≥ 0.70 |
| CanopySeg | canopy 類 IoU | ≥ 0.85 |
| LeafInst | mAP@50（葉片） | ≥ 0.75 |
| LeafInst | 尺度物偵測 mAP@50 | ≥ 0.95 |
| LeafInst | 葉面積誤差（與人工量測） | MAPE ≤ 8% |
| LeafDefect | 各病徵 IoU | ≥ 0.55 |
| LeafDefect | health_score 與專家評分相關 | Spearman ρ ≥ 0.75 |

### 二、平台驗收標準

| 項目 | 標準 |
|------|------|
| 上傳成功率 | ≥ 99%（< 30 MB 影像） |
| 推論延遲 | 單張 ≤ 30 秒（GPU）/ ≤ 90 秒（CPU） |
| 報表產生 | 單棵樹 PDF ≤ 10 秒 |
| 可用性 | 月可用率 ≥ 99%（不含計畫性維護） |
| 瀏覽器相容 | Chrome / Edge / Safari 最近 2 版 |
| 行動端 | 響應式，可在平板正常上傳與檢視 |

### 三、測試策略

- **單元測試**：模型預處理、指標計算、API handler
- **整合測試**：上傳 → 排程 → 推論 → 報表全流程
- **回歸測試**：每次模型升級重跑固定驗證集，存差異
- **使用者測試**：每階段邀 2~3 位實際使用者執行典型任務

---

## 拾、開發里程碑（總表）

詳見 [roadmap.md](roadmap.md)。摘要：

| 階段 | 期程 | 主要產出 |
|------|------|----------|
| **0. 規格定稿（v0.1）** | 2026-04 | ✅ SPEC.md、data-schema.md、annotation-guideline.md（已收尾於 2026-04-30） |
| **0.5 規格大改（v0.2，土肉桂試驗定錨）** | 2026-05 | 🔥 **進行中** — ADR-0002~0005 + SPEC v0.2 + schema v0.2 |
| **1. 資料收集 + 標註** | 2026-06 ~ 2026-09 | **≈ 12,720 張 / 年**（300 樣樹 × 月 / 季配 × 4-5 capture\_types）；標註 ≥ 1,000 張 baseline |
| **2. 模型 v0** | 2026-08 ~ 2026-10 | CanopySeg / LeafInst / LeafDefect / **PlantStructure (NEW)** baseline，達初步驗收 |
| **3. 平台 MVP** | 2026-09 ~ 2026-12 | 上傳、推論、試驗對照分析、PDF 報表 |
| **4. 內部試營運** | 2027-01 ~ 2027-03 | 4 樣區實際監測 + 計畫期中報告交付 |
| **5. 公測上線** | 2027-04 | 正式對外開放、計畫結案、文件齊全 |

---

## 拾壹、風險與假設

### 一、主要風險

| 風險 | 影響 | 緩解 |
|------|------|------|
| 標註資料量不足 → 模型泛化弱 | 高 | 用公開資料集 pretrain；採半監督學習；前期限定樹種 |
| 場域光照變化大 → 黃化判讀偏差 | 中 | 強制要求色卡、訓練時做色彩擾動增強 |
| Google Drive 同步衝突毀損 git | 中 | 排除 `.git/` 同步；每日推 GitHub |
| 個資 / 場域 GPS 外洩 | 中 | 預設遮蔽、權限分層 |
| 計算資源（GPU）不足 | 中 | 推論用 ONNX + CPU 推論優先；GPU 限訓練 |
| 病徵類別定義不統一 | 高 | 標註規範定義含視覺範例；交叉標註 IoU 監控 |

### 二、關鍵假設

- 場域可在合理光照條件（白天、非雨天）拍攝
- 葉片近拍可放置已知尺寸的尺度物
- 場域內樹木已預先編號（或可以系統自動編號）
- 使用者具基本電腦操作能力，不需要客製訓練

---

## 拾貳、決議與開放問題（v0.2 重組）

### 一、ADR-0001 已決議議題（2026-04-30，仍適用）

| # | 議題 | 決議 | 對應 ADR |
|---|------|------|----------|
| 1 | 樹種辨識（v1 vs v2） | **v1 不做**，schema 預留欄位（`species_zh` / `species_sci`），v2 再導入 `SpeciesId` 模型 | [§議題 1](decisions/0001-open-questions.md) |
| 2 | 葉片標註單位 | **只標全葉**（含葉柄一體），`leaf_instance` 表保留單一 `polygon_json`，不另設 `petiole_json` | [§議題 2](decisions/0001-open-questions.md) |
| 3 | 健康分數權重 | **兩階段**：v1 用全域固定權重（`health_score_global`，必填），v1.5 起對特定樹種推 `health_score_species`（v1 可空）；權重抽 config，從第一天就支援切換 | [§議題 3](decisions/0001-open-questions.md) |
| 4 | 報表格式 | **PDF + CSV/Excel** 並行，`POST /reports` 增加 `format: pdf \| csv \| xlsx \| all` 參數，預設 `all` | [§議題 4](decisions/0001-open-questions.md) |
| 5 | GPS 遮蔽粒度 | **三層雙軌制**：DB 永遠儲存原始 GPS，遮蔽僅在 API serialization 時做；admin → exact、認證研究者 → town、公開/訪客 → county；回應加 `gps_precision` 欄位 | [§議題 5](decisions/0001-open-questions.md) |
| 6 | License | **Apache License 2.0**（已落地，見 [LICENSE](../LICENSE) / [NOTICE](../NOTICE)） | [§議題 6](decisions/0001-open-questions.md) |
| 7 | 多語系 | **v1 繁中**，前端從第一天用 `next-intl` i18n 框架，預留英文 fallback；報表標題附英文括號注記（例如「健康分數 (Health Score)」） | [§議題 7](decisions/0001-open-questions.md) |

> 翻案規則：不直接修改 ADR-0001；改開新 ADR `superseded by NNNN`。

### 二、v0.2 新增 ADR（2026-05-04）

| ADR | 主題 | 狀態 | 摘要 |
|-----|------|------|------|
| [ADR-0002](decisions/0002-site-species-application-scope.md) | 場域、樹種、應用場景定向 | **accepted** | 鎖定大雪山合作社土肉桂試驗 4 樣區，平台層保留多樹種擴展鉤子 |
| [ADR-0003](decisions/0003-schema-alignment-with-xlsx.md) | 資料模型對齊既有 XLSX schema | proposed | 採四層架構（林地實體 + 試驗設計 + 影像模型 + 試驗對照分析） |
| [ADR-0004](decisions/0004-experimental-response-metrics.md) | 試驗響應指標體系 | proposed | 14 項影像可推得指標（葉片產量 5、葉色健康 5、株型生長 4）+ 衍生 health_score |
| [ADR-0005](decisions/0005-fixed-camera-station-sop.md) | 固定攝點 SOP | proposed | 每株 ≥ 3 攝點（北側全株 / 東側全株 / 葉片近拍）+ 加值攝點 |

### 三、待計畫主持人釐清的 22 個問題

詳見 [pi-consultation-questions.md](decisions/pi-consultation-questions.md)：

- **A 級（7 題）**：阻塞 Phase 1 啟動 — 樣區編號、樣樹編號、栽植日期、對照組設計、施肥日期、修剪量化標準、IP 政策
- **B 級（9 題）**：影響 ADR 落地細節 — 樣木代碼唯一性、site/plot 二分、面積定義、campaign 粒度、工作分工、攝點負擔、標樁保護、成熟林攝點、XLSX 升版
- **C 級（6 題）**：TreeVision 內部技術 — 葉片計數定義、新葉判定、health_score 權重、PlantStructure 優先級、葉綠素指標、葉片代表性

### 四、變更紀錄

| 日期 | 版本 | 主要變更 |
|------|------|---------|
| 2026-04-29 | v0.1 草案 | 初版 |
| 2026-04-30 | v0.1 定稿 | ADR-0001 7 題決議落地（議題 1~7 全採納） |
| 2026-05-04 | v0.2 草案 | 場域定錨於土肉桂試驗；新增 ADR-0002~0005；§伍 加 PlantStructure；§陸 ER 重組；§拾 路線異動 |

---

## 拾參、試驗設計支援（NEW v0.2）

### 一、試驗對照分析的工作流

```
Image (含 station_id, campaign_id, treatment_id)
   ↓ AI 推論（CanopySeg / LeafInst / LeafDefect / PlantStructure）
ImageMetric（每影像 14 指標）
   ↓ 按 tree_id × campaign 彙總
TreeImageMetricCampaign（每樹 × 每場次）
   ↓ 按 treatment × campaign 彙總
TreatmentResponseSummary（每處理組 × 每場次 × 14 指標）
   ↓ 跨場次 ANOVA（依 ADR-0004 §評估指標）
ExperimentAnovaResult（F、p、effect size）
   ↓ 視覺化
試驗對照分析報表（experiment_compare 模板，6 頁，依 ADR-0004 §三）
```

### 二、ANOVA 設計

| 樣區類型 | 設計 | 因子 |
|---------|------|------|
| 20 年生（115-12-1） | 2×2 ANOVA + 對照 | 修剪 (P+/P-) × 施肥 (F+/F-) |
| 幼齡林 ×3 樣區 | 雙因子析因 + 區集 | 修剪 (P+/P-) × 施肥量 (150g/200g/250g)，3 樣區為 block |

### 三、與官方試驗的對接

| 官方項目 | TreeVision 補強 |
|---------|---------------|
| 樹高 / DBH（人工，每季） | TreeMeasurement 表記錄；影像 PlantStructure 校正驗證 |
| 枝葉乾重 / 鮮重（採收時） | 不替代，但可從 leaf_count_visible × mean_leaf_area_cm² 估計 |
| 精油含量 / 成分 | 不替代（化學分析） |
| 土壤養分 / 逕流 | SoilEnvironment + Disturbance 表記錄 |
| **官方未列**：葉片計數、葉色、病斑率、冠幅、株高自動量測 | TreeVision 14 指標補上 |

### 四、預期交付物（試驗結束時）

1. 完整 14 指標兩年期時序資料（CSV / Parquet）
2. ANOVA 統計分析報表（PDF + 原始 R / SPSS 輸出檔）
3. 處理組響應曲線圖（matplotlib / Plotly）
4. 修剪 × 施肥交互作用熱力圖
5. 影像 vs 官方人工量測對照散點圖（驗證 TreeVision 量測精度）

### 五、相關 ADR

- [ADR-0002](decisions/0002-site-species-application-scope.md)：場域定錨
- [ADR-0003](decisions/0003-schema-alignment-with-xlsx.md)：schema 對齊
- [ADR-0004](decisions/0004-experimental-response-metrics.md)：響應指標細部規格
- [ADR-0005](decisions/0005-fixed-camera-station-sop.md)：固定攝點 SOP

---

## 拾肆、附錄

- A：[資料 schema 完整定義](data-schema.md)
- B：[REST API 完整定義](api.md)
- C：[標註規範](annotation-guideline.md)
- D：[系統架構](architecture.md)
- E：[路線圖](roadmap.md)
- F：[**場域脈絡與試驗設計彙整**（v0.2 NEW）](../references/cinnamon-trial-context.md)
- G：[**主持人諮詢問題清單**（v0.2 NEW）](decisions/pi-consultation-questions.md)
- H：[ADR 索引](decisions/README.md)

---

**文件結束**
