# 建模期標註集建置計畫（Annotation Set Plan）

| 項目 | 內容 |
|------|------|
| 版本 | v0.1 |
| 文件日期 | 2026-06-14 |
| 狀態 | **前置 scaffolding**（影像就緒即可開標；數量目標待 Pilot 後微調）|
| 角色 | 銜接 [ADR-0006 葉片三階段](decisions/0006-image-sampling-design.md) 之「建模階段」與 [標註規範](annotation-guideline.md) |
| 相關 | [SPEC §伍 模型](SPEC.md)、[ADR-0004 指標](decisions/0004-experimental-response-metrics.md)、[annotations/](../annotations/)、[annotations/cvat-labels.json](../annotations/cvat-labels.json) |

> **定位**：本計畫回答「建模期要標多少張、標什麼類別、如何抽樣與品管」。它是 [ADR-0006 未解決問題 #5](decisions/0006-image-sampling-design.md)（建模標註集所需最小葉片數，依病徵類別平衡）的落地提案。**影像尚未到位前，先把工具設定、類別、數量目標、品管流程備妥。**

---

## 壹、四個模型的標註需求總覽

| 模型 | 影像類型 | 標註任務 | 類別 |
|------|---------|---------|------|
| LeafInst | `leaf_macro`（離體平鋪）+ `whole_plant` | 實例分割（每片葉）+ 尺度物偵測 | leaf、scale_object（4 型）|
| LeafDefect | `leaf_macro` 切出之單葉 ROI | 多標籤分割 | lesion／chlorosis／necrosis／hole |
| CanopySeg | `canopy`、`whole_plant` | 語義分割（5 類）| canopy_other／veg_green／veg_yellow／veg_brown |
| PlantStructure | `whole_plant` | 全株分割 + 株頂/株底/樹冠關鍵點 | whole／canopy／trunk + keypoints |

> 葉齡（嫩葉/成熟葉，對應 [ADR-0004](decisions/0004-experimental-response-metrics.md) A2/A3）以 LeafInst 之 `leaf_age` **屬性**標註，不另設類別。

---

## 貳、數量目標（建模期，一次性代表集）

依 [ADR-0006 §二(一)](decisions/0006-image-sampling-design.md)：跨樣區 × 處理 × 健康狀態抽代表集，總計數百片。

### 一、葉片離體集（LeafInst + LeafDefect 共用）

| 維度 | 配置 |
|------|------|
| 抽樣框 | 4 樣區 × 代表處理（C0／P1／F150／P1F150）× 健康範圍 |
| 每處理 | 約 5 株 × 每株 5–10 片 |
| 目標總量 | **400–600 片葉**（達初步泛化下限）|
| 病徵平衡（關鍵）| 每一病徵類別（lesion／chlorosis／necrosis／hole）**各 ≥ 100 個實例**；健康葉天然占多數，須**刻意過抽含病徵葉**補足 |
| 尺度物 | 每張 `leaf_macro` 必含 ≥ 1 個尺度物標註（否則不進訓練集，[標註規範 §參](annotation-guideline.md)）|

### 二、全株 / 樹冠集（CanopySeg + PlantStructure + 在體 LeafInst）

| 維度 | 配置 |
|------|------|
| 抽樣框 | 4 樣區 × 4 處理 × 多場次 × 核心攝點（北/東/俯拍）|
| 目標總量 | **300–500 張 `whole_plant`/`canopy`**（含幼齡林背板與成熟林兩情境）|
| 涵蓋 | 須含黃化/褐化/健康樹冠範圍，供 CanopySeg 三色分類學得起來 |

### 三、總量與工時粗估

| 項目 | 估計 |
|------|------|
| 標註總張數 | 約 700–1,100 張（葉片 + 全株），達 [roadmap](roadmap.md) Phase 1「≥ 1,000 張 baseline」 |
| 單張工時 | 葉片實例 + 病徵 ~8–15 min；全株分割 + keypoint ~5–10 min |
| 估計總工時 | 約 120–200 hr（含 5% 交叉複標）|

---

## 參、抽樣與防偏

一、**系統抽樣涵蓋大小範圍**（[ADR-0006 §一](decisions/0006-image-sampling-design.md)）：每處理依樣樹編號抽 1、5、10…，**嚴禁只挑長得漂亮的**（避免 selection bias 扭曲分佈與病徵頻度）。

二、**病徵刻意過抽**：健康葉易得、病徵葉稀少；為達 §貳-一各病徵 ≥ 100 實例，須主動到受害植株補採含病徵葉。

三、**健康/病徵雙端都要**：模型需見過「乾淨葉」與「各程度病徵葉」才學得出 ratio 的連續譜。

---

## 肆、工具與工作流

一、**主工具 CVAT**（[標註規範 §伍](annotation-guideline.md)）；label 設定檔 [annotations/cvat-labels.json](../annotations/cvat-labels.json) 可直接匯入（Project → Raw → 貼上）。

二、**匯出 COCO 1.0** → 經 `scripts/labelme_to_coco.py`／`import_coco.py` 匯入 TreeVision（[annotations/README](../annotations/README.md)）。

三、**二人交叉複標**：隨機 5% 樣本雙標，計 IoU 一致性。

```
原始影像 → 標註者 A → 隨機 5% 進 B 複標 → 計 IoU
                                         ↓ < 門檻
                                   討論 → 修訂規範 → 重標
```

---

## 伍、品質門檻（驗收標註集本身）

| 指標 | 目標 | 來源 |
|------|------|------|
| 跨標註者 IoU（病徵）| ≥ 0.55 | [標註規範 §肆-四](annotation-guideline.md) |
| 跨標註者 IoU（樹冠輪廓/葉片）| ≥ 0.85 | 同上 |
| 漏標率 | < 5% | 同上 |
| 誤標率 | < 5% | 同上 |
| 病徵類別最小實例數 | 各 ≥ 100 | 本計畫 §貳-一 |

> 標註集通過上述門檻後，方進模型訓練；訓練後模型再以 [SPEC §玖](SPEC.md) 驗收標準（mIoU/mAP/MAPE）評估。

---

## 陸、資料夾對應

| 標註目標 | 路徑（[annotations/](../annotations/)）|
|---------|------|
| 葉片實例 + 尺度物 | `annotations/leaf_closeup/leaf_instance/`、`scale_object/` |
| 病徵 | `annotations/leaf_closeup/{lesion,chlorosis,necrosis,hole}/` |
| 樹冠 5 類 | `annotations/canopy/` |
| 全株分割 + keypoint | `annotations/whole_plant/`（新增）|

> 標註 JSON 已 `.gitignore`（資料治理）；公開時改 `*.public.json` 並從 `.gitignore` 例外。

---

## 柒、與後續的銜接

一、建模集標完 → 訓練 LeafInst/LeafDefect/CanopySeg/PlantStructure baseline（[roadmap](roadmap.md) Phase 2）。

二、模型驗收（影像 vs 人工 r ≥ 0.7，[ADR-0004](decisions/0004-experimental-response-metrics.md)）通過後 → 切換 [ADR-0006](decisions/0006-image-sampling-design.md) 「例行階段」：拍全株、模型讀數、不再摘葉，僅每季每處理 2–3 株重驗。

---

## 捌、變更紀錄

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-06-14 | v0.1 | 初版：四模型標註需求、建模期數量目標（葉片 400–600 片/病徵各 ≥100、全株 300–500 張）、抽樣防偏、CVAT 工作流、標註集品質門檻、資料夾對應。落地 ADR-0006 未解決問題 #5 |
