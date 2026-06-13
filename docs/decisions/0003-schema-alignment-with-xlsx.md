# ADR-0003：資料模型對齊既有 XLSX 調查表 schema

| 屬性 | 值 |
|------|----|
| 編號 | 0003 |
| 標題 | 資料模型對齊既有 XLSX 調查表 schema |
| 狀態 | **proposed** |
| 草擬日期 | 2026-05-04 |
| 決議日期 | （待主持人決議） |
| 提案人 | TreeVision Contributors |
| 對應 SPEC 章節 | [docs/SPEC.md 第柒章 資料 schema](../SPEC.md)、[docs/data-schema.md](../data-schema.md) |
| 對應 JSON Schema | `schemas/*.schema.json` 整體版本升至 v0.2 |
| 前置 ADR | [ADR-0002](0002-site-species-application-scope.md) |
| 相關 ADR | ADR-0004（響應指標）、ADR-0005（固定攝點） |
| 對應參考資料 | [references/cinnamon-trial-context.md §伍](../../references/cinnamon-trial-context.md) |

---

## Context

### 一、既有 XLSX 是場域官方標準

「土肉桂生長調查記錄表.xlsx」（v1.0，2025-07-26 建立）含 10 個工作表，是大雪山土肉桂試驗的**現行調查標準**：

| Sheet | 用途 |
|-------|------|
| 說明、代碼表、資料字典、QAQC | 元規範 |
| 樣區、樹木、樹木\_歷次、再生 | 林地實體 |
| 土壤&環境、物候、干擾、樣品 | 觀測資料 |

> 此 schema 已被合作社、調查員、計畫主持人接受並使用。**TreeVision 若另設一套，會造成「兩套資料」並存**，違反 [Cloud.md](file:///C:/Users/cct/.claude/Cloud.md) 三軌分流的「**單一事實來源**」原則。

### 二、TreeVision v0.1 schema 與 XLSX 的對應差距

| TreeVision v0.1 實體 | XLSX 對應 | 差距 |
|--------------------|----------|------|
| `site` | 樣區 | 欄位差 8 個（坡度、坡向、坡位、樣區大小、建置日期、調查員、樣區型態、海拔高） |
| `tree` | 樹木 | 欄位差 7 個（標籤號、生長階段、狀態、樹冠 W1/W2、樹冠級、健康等級 1-5、危害 1/2、纏繞藤本 %） |
| `image` | 無對應 | TreeVision 獨有（XLSX 不收影像） |
| `analysis_run` / `image_metric` / `leaf_instance` | 無對應 | TreeVision 獨有 |
| `tree_daily_summary` | 樹木\_歷次（部分） | 不一致：歷次以「量測日期」為事件粒度（多日彙總），TreeVision 是「每日」 |
| 無對應 | 再生、土壤&環境、物候、干擾、樣品 | **全部缺漏** |

### 三、試驗對照分析必須的新實體

[ADR-0002](0002-site-species-application-scope.md) 鎖定試驗監測為主軸後，下列實體即使在 XLSX 中也未直接列出，但是試驗對照所必需：

- **treatment**（處理組定義）— XLSX 隱含於樣區 / 個體說明，未顯式建模
- **plot**（樣區內的試驗單元）— XLSX 的「樣區」較像 site，沒到 plot 粒度
- **campaign**（採集場次）— XLSX 用「量測日期」隱含
- **fixed\_camera\_station**（固定攝點）— XLSX 未涵蓋（屬影像專有）

---

## Options

### 選項 A：完全保留 TreeVision v0.1 schema，XLSX 用 ETL 匯入

| 屬性 | 內容 |
|------|------|
| 開發成本 | 高（持續維護 ETL） |
| 與場域對接成熟度 | 低（每次 XLSX 變更都要改 ETL） |
| 雙寫風險 | **高**（兩套資料不一致） |

### 選項 B：完全採用 XLSX schema，捨棄 TreeVision 影像專屬部分

| 屬性 | 內容 |
|------|------|
| 影像 / 模型工作流 | **無法承載**（XLSX 不收 image_id、polygon 等） |
| 對齊度 | 100% |
| 可行性 | ✗（功能殘缺） |

### 選項 C：以 XLSX 為「**林地實體與觀測**」基準，TreeVision 補「**影像 + 模型推論 + 試驗對照**」三層

```
┌─────────────────────────────────────────────────────────────┐
│ 林地實體層（對齊 XLSX）                                       │
│   site / tree / tree_measurement / regeneration_subplot      │
│   soil_environment / phenology / disturbance / sample        │
├─────────────────────────────────────────────────────────────┤
│ 試驗設計層（XLSX 隱含、TreeVision 顯式建模）                  │
│   treatment / plot / campaign / fixed_camera_station         │
├─────────────────────────────────────────────────────────────┤
│ 影像 + 模型層（TreeVision 獨有）                              │
│   image / annotation / analysis_run / image_metric           │
│   leaf_instance / model / tree_daily_summary（重命名）        │
├─────────────────────────────────────────────────────────────┤
│ 試驗對照分析層（NEW）                                          │
│   treatment_response_summary / experiment_anova_result       │
└─────────────────────────────────────────────────────────────┘
```

| 屬性 | 內容 |
|------|------|
| 開發成本 | 中（一次性 schema 重構，後續低維護） |
| 與場域對接成熟度 | 高（XLSX 直接 import） |
| 雙寫風險 | 低（同 schema 來源） |
| 風險 | XLSX 後續若版本升，TreeVision 須跟進 |

---

## Decision

### 一、選擇 **選項 C**（四層架構，林地實體層對齊 XLSX）

### 二、欄位命名雙語政策

XLSX 用中文欄名，TreeVision schema 用 snake_case 英文欄名。建立**對應字典**：

| XLSX 中文欄名 | TreeVision 英文欄名 | 表 |
|--------------|--------------------|----|
| 樣區代碼 | site_id（**改為 plot_id**，見下節） | site / plot |
| 樣木代碼 | tree_id | tree |
| 標籤號 | tree_tag | tree |
| 樹種 | species_sci, species_zh | tree |
| 生長階段 | growth_stage | tree |
| 狀態 | status | tree |
| 胸徑\_cm | dbh_cm | tree / tree_measurement |
| 樹高\_m | height_m | tree / tree_measurement |
| 樹冠 W1\_m / W2\_m | crown_w1_m / crown_w2_m | tree / tree_measurement |
| 樹冠級 | crown_class | tree / tree_measurement |
| 健康等級\_1to5 | health_grade_subjective_1_5 | tree / tree_measurement |
| 危害 1 / 2 | damage_1 / damage_2 | tree / tree_measurement |
| 纏繞藤本覆蓋% | liana_cover_pct | tree / tree_measurement |
| 量測日期 | measure_date | tree_measurement |
| 量測者 | measured_by | tree_measurement |
| 胸高段面積\_m² | basal_area_m2 | tree_measurement（公式欄位） |

> **完整對應字典維護於 `docs/data-schema.md` 附錄一**。

### 三、site / plot 的概念釐清（重要差異）

XLSX 中「樣區」實際扮演兩種角色：
- 在大尺度上是「**地理場域**」（如：大雪山 115-12-1）
- 在試驗設計上是「**試驗區集 / 單元**」（CRBD 中的 block）

TreeVision 拆為兩個實體：

| 實體 | 對應內容 |
|------|---------|
| `site` | 場域層級（事業區 + 林班 + 作業列區），如 `115-12-1`、`117-28-1`、`1-2-3`、`8-1-10` |
| `plot` | 試驗單元（在 site 內，依 treatment 切分），如 `115-12-1.P+F+`（修剪 + 施肥組） |

`plot_id` 命名規則：`<site_id>.<treatment_id>`，例 `115-12-1.P+F+`

### 四、實體最終清單（v0.2）

#### (一) 林地實體層（對齊 XLSX）

| TreeVision 實體 | XLSX Sheet | 變更類型 |
|----------------|-----------|---------|
| `site` | 樣區（場域角色） | 擴充 |
| `tree` | 樹木 | 擴充 |
| `tree_measurement` | 樹木\_歷次 | **新增**（取代原 `tree_daily_summary` 中與量測重疊的部分） |
| `regeneration_subplot` | 再生 | 新增 |
| `soil_environment` | 土壤&環境 | 新增 |
| `phenology` | 物候 | 新增 |
| `disturbance` | 干擾 | 新增 |
| `sample` | 樣品 | 新增 |

#### (二) 試驗設計層（XLSX 未顯式建模，TreeVision 補）

| TreeVision 實體 | 用途 |
|----------------|------|
| `treatment` | 處理組定義（修剪 / 施肥水準） |
| `plot` | 試驗單元（site × treatment 的交集） |
| `campaign` | 採集場次（一次出場活動，可跨多 site / plot） |
| `fixed_camera_station` | 固定攝點（每樹一至多個，見 ADR-0005） |

#### (三) 影像 + 模型層（v0.1 既有，需擴充 FK）

| TreeVision 實體 | 變更 |
|----------------|------|
| `image` | 加 FK：`plot_id`、`campaign_id`、`station_id`、`treatment_id` |
| `annotation`、`analysis_run`、`image_metric`、`leaf_instance`、`model` | 不變（內部結構） |
| ~~`tree_daily_summary`~~ | **改名為 `tree_image_metric_daily`**（明確「影像衍生」），與 `tree_measurement` 分離 |

#### (四) 試驗對照分析層（NEW）

| TreeVision 實體 | 用途 |
|----------------|------|
| `treatment_response_summary` | 每處理組 × 時點 × 響應變數（14 指標）的彙總 |
| `experiment_anova_result` | ANOVA 結果（F 值、p 值、effect size） |

### 五、Enum 對齊（強制）

XLSX 代碼表的 enum 為標準。TreeVision 既有 enum 需調整：

| 欄位 | v0.1 enum | v0.2 enum（對齊 XLSX） |
|------|----------|---------------------|
| `crown_status` | healthy / stressed / damaged / dead | **改名為 `status`**：存活 / 枯立 / 倒伏 / 缺測 |
| 新增 `crown_class` | （無） | 優勢 / 共優勢 / 次冠層 / 被壓 |
| 新增 `growth_stage` | （無） | 幼樹 / 小徑木 / 成樹 |
| 新增 `damage` | （無） | 無 / 折幹倒伏 / 傷皮刮傷 / 中心空洞 / 病蟲危害 / 土壤擾動 / 人為干擾 / 其他 |
| 新增 `phenology_stage` | （無） | 嫩葉 / 新梢 / 花蕾 / 開花 / 幼果 / 成熟果 / 落葉 / 休眠 |
| 新增 `soil_texture` | （無） | Sand / Loamy sand / Sandy loam / Loam / Silt loam / Silt / Sandy clay loam / Clay loam / Silty clay loam / Sandy clay / Silty clay / Clay |
| 新增 `disturbance_type` | （無） | 颱風 / 豪雨崩塌 / 落石 / 獸害 / 病蟲害 / 砍伐 / 人為踩踏 / 火災 / 其他 |
| 新增 `damage_severity_1_5` | （無） | 1 非常輕微 / 2 輕微 / 3 中等 / 4 嚴重 / 5 極嚴重 |
| `view`（影像視角） | north/south/east/west/overhead/handheld | **保留並擴充**：新增 `whole_north / whole_south / whole_east / whole_west` |
| `capture_type` | canopy / leaf_closeup | **擴充**：新增 `whole_plant`、`scale_ref` |

### 六、量測模型：時序粒度對齊

| 場景 | TreeVision v0.2 表 | 粒度 |
|------|------------------|------|
| 人工 / 影像基準量測（樹高、DBH、健康等級） | `tree_measurement` | **以 measure_date 為事件**（不限頻率，依官方季配） |
| 影像衍生指標（葉計數、葉色、病斑率） | `tree_image_metric_daily` | **每日彙總**（多張影像的當日平均） |
| 處理組層級彙總（試驗對照分析） | `treatment_response_summary` | **每處理組 × 採集場次** |

### 七、ETL：XLSX → TreeVision DB 雙向同步

提供 `scripts/sync_xlsx_to_db.py`（待開發）：
- **Inbound**：XLSX → DB（每月一次同步）
- **Outbound**：DB → XLSX（按計畫主持人需求出報表）

---

## Consequences

### 一、SPEC 異動

- 第柒章 全章重寫
- `docs/data-schema.md` 升 v0.2，新增 8 個實體章節 + 對應字典附錄

### 二、JSON Schema 異動（`schemas/`）

需新增 / 修改：

| 檔案 | 動作 |
|------|------|
| `image_metadata.schema.json` | 修：加 `plot_id`, `campaign_id`, `station_id`, `treatment_id` 欄位 |
| `tree_registry.schema.json` | **新增** |
| `site_registry.schema.json` | **新增** |
| `tree_measurement.schema.json` | **新增** |
| `treatment.schema.json` | **新增** |
| `plot.schema.json` | **新增** |
| `campaign.schema.json` | **新增** |
| `fixed_camera_station.schema.json` | **新增** |
| `regeneration_subplot.schema.json` | **新增** |
| `soil_environment.schema.json` | **新增** |
| `phenology.schema.json` | **新增** |
| `disturbance.schema.json` | **新增** |
| `sample.schema.json` | **新增** |
| `treatment_response_summary.schema.json` | **新增** |
| `experiment_anova_result.schema.json` | **新增** |
| `analysis_result.canopyseg.schema.json` | 修：v0.2 元欄位 |
| `analysis_result.leafinst.schema.json` | 修：v0.2 元欄位 |
| `analysis_result.leafdefect.schema.json` | 修：v0.2 元欄位 |

### 三、metadata 模板（`metadata/`）

| 檔案 | 動作 |
|------|------|
| `image_metadata.template.csv` | 修：加 4 個 FK 欄位 |
| `tree_registry.template.csv` | 修：對齊新欄位 |
| `site_registry.template.csv` | 修：對齊 XLSX 樣區欄位 |
| `treatment.template.csv` | **新增** |
| `plot.template.csv` | **新增** |
| `campaign.template.csv` | **新增** |
| `fixed_camera_station.template.csv` | **新增** |
| 其他 5 個（再生 / 土壤環境 / 物候 / 干擾 / 樣品） | **新增** |

### 四、API 異動（`docs/api.md`）

新增端點：

```
GET  /api/v1/treatments
GET  /api/v1/plots
POST /api/v1/campaigns
GET  /api/v1/stations/{station_id}/images
GET  /api/v1/treatments/{treatment_id}/response_summary?metric=leaf_count&from=...
GET  /api/v1/experiments/{exp_id}/anova
```

### 五、向後相容

- v0.1 的 `tree_daily_summary` 改名為 `tree_image_metric_daily`；舊 API 路徑保留別名 1 個版本（v0.2 期間）後 v0.3 移除
- `crown_status` enum 升級非向後相容（值列表改變），需要 migration script

### 六、營運面影響

| 項目 | 影響 |
|------|------|
| 既有 XLSX 持續使用 | ✓（為主要資料輸入手段） |
| ETL 排程 | 每月一次 XLSX → DB sync |
| 訓練資料標註 | 不受 schema 影響，僅 metadata 對齊 |
| 報表 | 試驗對照分析報表為新交付物 |

---

## 未解決問題

| # | 問題 | 影響 |
|---|------|------|
| 1 | XLSX v1.0 是否會升版？升版頻率？ | ETL 維護負擔 |
| 2 | XLSX 中的 `樣區大小_m2 = 400` 與報告書「面積 0.5 ha (= 5,000 m²)」不一致，何者為實際試驗單元面積？ | plot 粒度設計 |
| 3 | 計畫主持人是否接受「TreeVision 將樣區拆為 site + plot 兩層」？ | schema 接受度 |
| 4 | XLSX 中沒有「採集場次（campaign）」概念，TreeVision 引入是否會造成混淆？ | 概念對齊 |
| 5 | XLSX 樹木代碼 T001 在不同 site 是否唯一？跨 site 的 T001 / T002 如何處理？ | tree_id 命名規則 |

---

## 附錄：Decision Log

| 日期 | 變更 |
|------|------|
| 2026-05-04 | 初版起草，狀態 proposed |
