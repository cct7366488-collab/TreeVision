# 葉片影像判釋鏈之方法學與驗證框架——科學性佐證報告

| 項目 | 內容 |
|------|------|
| 版本 | v0.2（方法學與驗證協定；關鍵公式與書目經原文核對）|
| 文件日期 | 2026-06-14 |
| 對象樹種 | 土肉桂 *Cinnamomum osmophloeum* Kanehira（林下經濟採葉經營）|
| 場域 | 林業及自然保育署臺中分署／大雪山林業生產合作社 土肉桂試驗 4 樣區 |
| 性質 | **前瞻性（a‑priori）方法學與驗證框架**——於真實資料導入前先界定流程、方程與驗收統計，使方法可被後續實證檢驗 |
| 配套文件 | [leaf-analysis-math.md](leaf-analysis-math.md)（判釋鏈數學）、[field-imaging-sop.md](field-imaging-sop.md)、[annotation-plan.md](annotation-plan.md)、[ADR-0004](decisions/0004-experimental-response-metrics.md)、[ADR-0006](decisions/0006-image-sampling-design.md) |

---

## 摘要

本報告將 TreeVision 之葉片影像判釋鏈（影像 → 指標 → 推估）逐一對應到既有同儕審查文獻，論證每一處理步驟皆有方法學依據，並提出一套**可被真實資料檢驗的驗證協定**。判釋鏈涵蓋四個層次：(一) 影像前置處理（尺度校正、單應透視校正、色彩再現、品質閘）；(二) 深度學習分割（葉片實例、病徵、樹冠、株型）；(三) 幾何與比值指標計算（葉面積、病斑率、葉色指數）；(四) 經營量推估與試驗統計（採收量、分佈、重複量測混合模型）。文獻顯示上述各環節在植物表型（plant phenotyping）、精準農業與遙測領域均有成熟方法與驗收先例。我們據此訂定驗收門檻：影像指標與人工量測之一致性以 **Lin 一致性相關係數（CCC）、Bland–Altman 一致界限、MAPE** 評估（非僅 Pearson r），並要求關鍵指標 CCC／r ≥ 0.7。真實資料導入後即可依本協定驗證方法可行性，形成可發表之學術成果。

---

## 壹、前言與研究目的

### 一、問題背景

土肉桂 *Cinnamomum osmophloeum* 為臺灣特有、分布於海拔 400–1500 m 天然闊葉林之樹種，其**葉片精油**為主要經濟產物，且葉與枝之精油產率約為樹皮之五倍，**僅採葉即可逐年收穫、無須剝皮或伐木**[19]，屬典型非木材林產物（NTFP）林下經濟。葉精油產率因化學型差異甚大（文獻報導 0.1–2.9%，linalool 化學型可達 3.7%）[19]，故**葉量、葉片健康與生長之量化監測**對採收經營與試驗對照具直接價值。

傳統葉量／葉面積量測仰賴破壞性採收與人工卡尺，曠日廢時且不可逆。本案試驗為修剪 × 施肥之 2×2 析因設計（[ADR-0004](decisions/0004-experimental-response-metrics.md)），需多季、多株、多指標之重複量測，人工量測難以負荷。**影像式非破壞性表型分析**遂成為合理替代途徑。

### 二、研究目的

一、將 TreeVision 葉片判釋鏈之每一處理步驟對應到既有文獻，論證其科學性。

二、把判釋流程與運算方程整理為可重現之方法學描述。

三、提出 a‑priori 驗證框架（含驗收統計與門檻），使真實資料導入後可實證檢驗方法可行性。

### 三、本報告的「前瞻驗證」立場

撰寫本報告時，本案尚未取得試拍影像。因此本文不報告實測結果，而是**先界定方法與驗收準則**（類似預先註冊 pre‑registration 的精神），避免事後挑選有利指標（防 data dredging）。此立場本身即提升後續驗證的科學嚴謹度。

---

## 貳、文獻回顧（依判釋鏈環節）

### 一、影像尺度校正與葉面積量測

以畫面中已知面積之參考物作為尺度，將葉片像素數換算為實際面積，是植物表型的標準做法。Easlon 與 Bloom（2014）之 *Easy Leaf Area* 以一塊已知面積的紅色校正區估計葉面積，公式為 `葉面積 = 綠色像素數 × (校正區面積 / 校正區像素數)`，免去測量相機距離與焦長；其手機影像估計甚至優於平台掃描器之 ImageJ 結果[1]。該文同時明確指出兩個誤差來源——**參考物須與葉片共平面以避免透視變形、且兩者應位於影像相近區域以減少鏡頭畸變**[1]，與本案 SOP「尺度物與葉共面、垂直俯視」之要求完全一致。

### 二、透視變形與單應（homography）校正

當量測平面與成像平面不平行時，會產生透視變形，嚴重影響像素當量（pixel equivalent）與量測精度。Wang 等（2025）提出以**單應映射**將原始影像轉換至校正成像平面，可同時校正非線性與透視畸變，於設計圖樣上達面積 RMSE 0.68 mm² 之精度[2]。此類方法之理論基礎為 Zhang（2000）之平面單應相機標定[3]。本案以 A4 方格紙四角為控制點解算單應矩陣，即屬同一框架。

### 三、葉片實例分割與計數

以深度學習做葉片**實例分割**（instance segmentation）並計數，已是表型領域常規。Mask R‑CNN[4] 在 CVPPP 葉片分割挑戰與多種植物上之分割精度 > 70%，可同時導出葉片數與葉片大小[5]。雜亂背景（cluttered background）為主要挑戰，文獻以局部精化機制或背景控制改善之[6]——此即本案於幼齡林採用**單色背板**、成熟林選背景單純方位之依據（[ADR-0006](decisions/0006-image-sampling-design.md)）。

### 四、葉片病徵嚴重度量化

病害嚴重度以**病斑像素面積 / 葉片像素面積之比值**估計，是跨作物廣泛採用的定義[7][8]。如 StripeRustNet 於葉片分割達 MIoU 98.65%、病斑分割 86.08%[7]；蘋果葉病害分級研究以像素級分割結合嚴重度迴歸達 R² ≈ 0.96[8]。本案 LeafDefect 之 `lesion_ratio / chlorosis_ratio / necrosis_ratio / hole_ratio`（[ADR-0004](decisions/0004-experimental-response-metrics.md) B4/B5）即採此比值定義。

### 五、RGB 葉色指數與葉綠素代理

可見光波段指數可代理葉綠素含量。三角綠度指數 TGI 由 Hunt 等（2011）以葉綠素吸收特徵在 R670、R550、R480 三點所圍三角面積定義[9]，波段差分原式為：

```
TGI = −0.5 × [(λr − λb)(R_r − R_g) − (λr − λg)(R_r − R_b)]
代入 λr=670、λg=550、λb=480 nm（寬波段 RGB）：
TGI = −0.5 × [190·(R − G) − 120·(R − B)]   （正規化後近似 G − 0.39R − 0.61B）
```

綠葉指數 GLI 由 Louhaichi 等（2001）提出，`GLI = (2G − R − B)/(2G + R + B)`[10]（本報告已以開放文獻表 2 核對公式一致）。多項研究顯示 RGB 植被指數與 SPAD（葉綠素計）值有顯著相關，並可用機器學習提升解釋力[11]。本案以 GLI、TGI 作為葉色／葉綠素代理（[ADR-0004](decisions/0004-experimental-response-metrics.md) B1/B2），屬文獻支持之做法；其有效性高度依賴**白平衡與色彩再現一致性**（見§二‑七）。

### 六、葉面積→生物量之異速生長（allometry）

非破壞性葉量推估常用葉長 × 葉寬或葉面積之異速模型。文獻顯示葉長 L × 葉寬 W 與葉面積、葉生物量高度相關，線性式如 `A = 0.60 × L × W`，於 *Coffea arabica*、*Tectona grandis*、*Jatropha curcas* 等可解釋 > 95% 葉面積變異[12]。本案以 `總葉面積估計 = 葉片數 × 平均葉面積`、再以迴歸對接破壞性乾重（[ADR-0004](decisions/0004-experimental-response-metrics.md) A5、[SPEC §拾參](SPEC.md)），與此文獻脈絡一致。

### 七、色彩再現與白平衡再現性

影像式表型之色彩特徵高度依賴色彩恆常性（color constancy）。文獻指出，同一相機於不同時間、日照、角度拍攝，縱使物體未變，色彩仍會漂移；故須標準化白平衡並**於畫面置入色彩校正卡**以確保可重現性[15]。此正是本案 SOP 要求「白平衡鎖日光、每場次拍色卡」之文獻依據。

### 八、影像品質（清晰度）客觀評估

無參考影像品質評估中，**Laplacian 響應變異數**（variance of Laplacian）為經典對焦／模糊度量：清晰影像邊緣豐富、變異數高，模糊影像反之；低於門檻即判為模糊[13]。本案入庫管線（`ingest_images.py`）以此作清晰度閘，與文獻一致。

### 九、株型／株高之影像量測

影像式株高量測在表型領域已達高精度。地面立體影像之冠層高度估計與人工量測 R² ≈ 0.92[14]；UAV RGB 株高 R² 0.35–0.88、RMSE 數 cm 級[14]。本案 PlantStructure 以全株分割 + 尺度校正推株高（C1）、冠幅（C2），屬同一方法族。

### 十、重複量測之統計分析與檢力

固定攝點逐期追蹤同一批株屬重複量測（repeated measures）設計，宜以線性混合模型分析；其檢力與樣本數可由專用工具（如 GLIMMPSE）估計[18]。**以個體內生長量為反應變數可消除個體間天生差異、提升檢力**——此為本案 [ADR-0006](decisions/0006-image-sampling-design.md) 之核心設計依據。

### 十一、方法一致性之驗收統計

比較「影像量測」與「人工標準量測」屬方法比較研究。文獻明確指出 **Pearson r 衡量線性關聯而非一致性**，不足以證明可互換；應改用 **Bland–Altman 一致界限**[16] 與 **Lin 一致性相關係數（CCC）**[17]，並輔以 MAE／MAPE、Deming 迴歸。Lin（1989）之 CCC 定義為（本報告已核對原式）：

```
ρc = 2·ρ·σx·σy / (σx² + σy² + (μx − μy)²)
ρ：兩變數之 Pearson 相關；σx,σy：標準差；μx,μy：平均
ρc = 1 為完全一致、0 為無相關、−1 為完全負一致
```

CCC 同時懲罰「相關不足」與「偏離 1:1 線（系統性偏差）」，故較 Pearson r 嚴格。本報告據此設計驗收（§肆）。

---

## 參、材料與處理分析流程（方法）

### 一、試驗與取樣設計

依 [ADR-0004](decisions/0004-experimental-response-metrics.md)、[ADR-0006](decisions/0006-image-sampling-design.md)：全場 2×2 析因（修剪 ± × 施肥 150g ±），4 樣區、約 480 株；固定追蹤每處理 10–15 株、系統抽樣涵蓋大小範圍、防選擇偏差。葉片離體精確量測僅於建模期抽代表集（數百片，[annotation-plan.md](annotation-plan.md)）。

### 二、判釋鏈總流程

```
原始影像
  │ 前置處理：尺度校正(§三)、單應校正(§四)、色彩校正(§五)、品質閘(§六)
  ▼
深度學習分割：LeafInst / LeafDefect / CanopySeg / PlantStructure
  │
  ├ 幾何指標：葉面積、葉長寬(PCA)、株高、冠幅
  ├ 比值指標：病斑率、黃化率、葉色 GLI/TGI
  ▼
彙總（每株×每場次）→ 推估（採收量、葉面積分佈、新老葉比）
  ▼
重複量測混合模型（處理組對照）→ 與人工量測一致性驗證
```

### 三、尺度校正（mm/pixel）

```
s = ref_size_mm / ref_size_px
leaf_area_cm² = area_px × (s/10)²
```

文獻依據 [1]；`s` 為平方項，誤差於面積加倍傳遞（§肆‑三）。

### 四、單應透視校正

以 A4 方格紙四個已知直角頂點解單應矩陣 H，將斜拍平面投影回正射視角，使全幅單一比例尺[2][3]：

```
[x' y' w']ᵀ ≈ H · [x y 1]ᵀ ,  校正座標 = (x'/w', y'/w')
傾斜角 θ 之面積偏差 ≈ (1/cosθ) − 1
```

### 五、色彩校正

固定日光白平衡 + 色卡，事後反解通道增益 `(g_R,g_G,g_B)` 還原至共同輻射基準[15]。葉色指數：

```
GLI = (2G − R − B) / (2G + R + B)
TGI = G − 0.39R − 0.61B        （可見光近似式）
```

依據 [9][10][11]。

### 六、品質閘

```
清晰度  clarity = Var(∇²I)，  < 門檻 → 退件        [13]
過曝率  overexp = #{max(R,G,B) ≥ 250} / #leaf_px，  > τ → 退件
```

### 七、分割與幾何量化

LeafInst（Mask R‑CNN 族[4][5]）輸出每片葉 polygon：

```
area_px = ½ |Σ(xᵢyᵢ₊₁ − xᵢ₊₁yᵢ)|        （shoelace）
葉長/葉寬 = polygon 之 PCA 主/次軸跨距 × s
```

LeafDefect（多標籤分割[7][8]）輸出病徵比值；CanopySeg 輸出三色植生比；PlantStructure 推株高／冠幅[14]。

### 八、經營量推估

```
總葉面積估計 A_total = 葉片數 × 平均葉面積                 [12]
估計乾重     Ŵ = β₀ + β₁·A_total   （等價 Ŵ = A_total/SLA）  [12]
分佈統計     mean, p25, p50, p75, CV = std/mean
```

### 九、試驗統計

```
反應變數 ~ 修剪 × 施肥 × 季別 + (1|樣木) + (1|樣區)        [18]
```

以個體內生長量為主反應變數提升檢力（[ADR-0006](decisions/0006-image-sampling-design.md)）。

---

## 肆、驗證框架（真實資料導入後執行）

### 一、驗證原則

一、**金標準對照**：影像指標 vs 官方人工量測（DBH、樹高、枝葉乾重，[SPEC §拾參](SPEC.md)）與離體精確量測。

二、**一致性而非僅相關**：採 Bland–Altman + Lin CCC + MAPE，不以 Pearson r 單獨判定[16][17]。

三、**a‑priori 門檻**：先訂門檻再驗，防事後挑選。

### 二、各指標驗收門檻

| 指標群 | 金標準 | 主驗收統計 | 門檻 |
|--------|--------|-----------|------|
| 葉面積（A4） | 離體掃描/方格紙人工 | CCC、MAPE | MAPE ≤ 8%、CCC ≥ 0.8 |
| 葉片計數（A1） | 人工點數 | MAPE、Bland–Altman | MAPE ≤ 15% |
| 病斑率（B4/B5） | 專家像素標註 | per‑class IoU、ratio MAE | IoU ≥ 0.50、MAE ≤ 0.05 |
| 葉色 GLI/TGI（B1/B2） | SPAD 葉綠素計 | Pearson r + CCC | r ≥ 0.7 |
| 株高（C1） | 捲尺人工 | MAPE、CCC | MAPE ≤ 10% |
| 採收量估計 | 採收乾重天秤 | CCC、Bland–Altman | CCC ≥ 0.7 |
| 模型分割品質 | 標註 ground truth | mIoU / mAP@50 | 依 [SPEC §玖](SPEC.md) |

> 各模型分割本身另以 mIoU（CanopySeg ≥ 0.70）、mAP@50（LeafInst ≥ 0.75）、葉計數 MAPE ≤ 15% 等驗收（[SPEC §玖](SPEC.md)、[ADR-0004](decisions/0004-experimental-response-metrics.md)）。

### 三、誤差傳遞之量化驗證

```
面積誤差：σ_A/A = √[(σ_N/N)² + (2·σ_s/s)²]   ← 尺度誤差係數為 2（平方放大）
```

驗證時實測 `σ_s`（尺度物重複量測變異）並回推 A 之理論誤差，與實際 MAPE 對照，檢驗誤差模型是否成立。

### 四、迴歸校正與外推

影像估計值對金標準做 Deming／OLS 迴歸求 β₀、β₁（或 SLA），通過門檻後方可外推至未拍攝株（[ADR-0006](decisions/0006-image-sampling-design.md) §五）；並以 Bland–Altman 檢查是否存在比例性偏差（proportional bias）。

### 五、標註可靠度（前置驗證）

建模集須先過跨標註者一致性（病徵 IoU ≥ 0.55、葉片/樹冠 ≥ 0.85，[annotation-guideline.md](annotation-guideline.md)、[annotation-plan.md](annotation-plan.md)），確保 ground truth 本身可靠，再進模型訓練與上述指標驗證。

### 六、驗證協定之程式實作（可執行）

本章驗收統計已操作化為 [`scripts/validate_metrics.py`](../scripts/validate_metrics.py)：實作 Lin CCC、Bland–Altman（含比例偏差檢定）、MAPE/MAE、Deming 迴歸，並依§二門檻自動判 pass/fail。該程式以 `--selftest` 之合成資料於 2026-06-14 驗證可正常運作（理想案例 CCC 0.997 → 通過；含 30% 系統偏差之劣化案例 Pearson r 仍達 0.927 但 CCC 0.748 → 正確判未通過，印證「r 高不等於一致」）。真實資料導入後以 `--csv` 餵入即產出相同格式之一致性報告，無須改寫分析流程。

---

## 伍、統計分析計畫

一、**主分析**：對 14 核心指標各跑重複量測線性混合模型[18]，報 F、p、效果量與交互作用；多重比較用 Tukey/LSD。

二、**檢力**：以 Pilot 取得各指標變異數後行正式 power analysis（GLIMMPSE 類工具[18]），定 final n（暫定每處理 12 株，[ADR-0006](decisions/0006-image-sampling-design.md)）。

三、**一致性分析**：每指標出 Bland–Altman 圖、CCC、MAPE，附影像 vs 人工散點與 1:1 線。

四、**穩健性**：分樣區、分林型（幼齡／成熟）、分健康狀態做敏感度分析。

---

## 陸、討論

### 一、方法的科學性佐證

判釋鏈各環節——尺度校正[1]、單應校正[2][3]、實例分割[4][5]、病徵比值[7][8]、葉色指數[9][10][11]、葉量異速[12]、色彩再現[15]、清晰度量測[13]、株高量測[14]、重複量測統計[18]、一致性驗收[16][17]——均有同儕審查文獻支持，且本案之 SOP 要求（共面尺度物、垂直俯視、白平衡鎖定、不過曝、固定攝點）恰對應文獻所列之關鍵誤差來源，顯示流程設計具方法學自洽性。

### 二、與既有文獻的差異與貢獻

一、**整合性**：多數文獻聚焦單一環節（僅葉面積、或僅病害）；本案將葉量、葉色、病徵、株型整合為單一試驗對照管線，並對接破壞性金標準。

二、**經營場景**：針對土肉桂採葉 NTFP 與修剪 × 施肥試驗，文獻罕見；葉量直接關聯精油採收，量測有明確經營意義[19]。

三、**前瞻驗證**：先訂方法與門檻再驗，提升結論可信度。

### 三、限制與風險

一、遮擋使在體葉片計數低估（為偏差非隨機誤差）；以固定攝點令偏差恆定、改用生長量為反應變數緩解[ADR-0006]。

二、RGB 葉色指數非葉綠素直接量測，受光照與品種影響；必要時以 SPAD 校正或升級多光譜[11]。

三、成熟林無背板下之分割品質、極端光照、樣本不平衡（病徵稀少）為已知風險，列入驗證敏感度分析。

四、本報告引用之應用型文獻部分為檢索摘要，正式投稿前須補齊完整書目（作者、年份、卷期頁）。

---

## 柒、結論

本報告論證 TreeVision 葉片影像判釋鏈之每一處理步驟均有文獻方法學依據，並提出可被真實資料檢驗之 a‑priori 驗證框架（以 CCC／Bland–Altman／MAPE 為核心、關鍵指標門檻 r/CCC ≥ 0.7）。真實試拍影像導入後，依本協定執行即可實證方法可行性，並可據以形成方法學與驗證之學術論文。建議下一步：完成第一批 Pilot 影像與離體量測 → 跑一致性分析 → 視結果迭代模型與門檻 → 撰寫實證版報告。

---

## 參考文獻

> 註：標註 ★ 者為該方法之經典文獻（作者年份明確）；其餘為本案檢索所得之應用型佐證，正式投稿前應補齊完整書目。

1. ★ Easlon, H. M., & Bloom, A. J. (2014). *Easy Leaf Area: Automated digital image analysis for rapid and accurate measurement of leaf area.* Applications in Plant Sciences, 2(7), apps.1400033. DOI: 10.3732/apps.1400033. 〔書目經 PubMed (PMID 25202639) 核對〕
2. Wang, C., et al. (2025). *A Perspective Distortion Correction Method for Planar Imaging Based on Homography Mapping.* Sensors, 25(6), 1891. <https://www.mdpi.com/1424-8220/25/6/1891>
3. ★ Zhang, Z. (2000). *A flexible new technique for camera calibration.* IEEE TPAMI, 22(11), 1330–1334.
4. ★ He, K., Gkioxari, G., Dollár, P., & Girshick, R. (2017). *Mask R‑CNN.* ICCV.
5. *Leaf Instance Segmentation and Counting Based on Deep Object Detection and Segmentation Networks.* IEEE. <https://ieeexplore.ieee.org/document/8716176/>
6. *Local refinement mechanism for improved plant leaf segmentation in cluttered backgrounds.* Frontiers in Plant Science (2023). <https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2023.1211075/full>
7. *StripeRust‑Pocket / StripeRustNet: deep learning disease severity (lesion/leaf ratio).* <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11265802/>
8. *Apple leaf disease severity grading based on deep learning and the DRL‑Watershed algorithm.* Scientific Reports (2025). <https://www.nature.com/articles/s41598-025-15246-8>
9. ★ Hunt, E. R., Jr., Daughtry, C. S. T., Eitel, J. U. H., & Long, D. S. (2011). *Remote Sensing Leaf Chlorophyll Content Using a Visible Band Index (TGI).* Agronomy Journal, 103(4), 1090–1099. DOI: 10.2134/agronj2010.0395.〔冠層尺度延伸：Hunt et al. (2013), Int. J. Appl. Earth Obs. Geoinf., 21, 103–112〕
10. ★ Louhaichi, M., Borman, M. M., & Johnson, D. E. (2001). *Spatially located platform and aerial photography for documentation of grazing impacts on wheat (GLI).* Geocarto International, 16(1), 65–70. DOI: 10.1080/10106040108542184.〔GLI 公式 (2G−R−B)/(2G+R+B) 經開放文獻 PMC10857024 表 2 核對一致〕
11. *A Robust Vegetation Index Based on UAV RGB Images to Estimate SPAD Values of Naked Barley Leaves.* Remote Sensing, 13(4), 686 (2021). <https://www.mdpi.com/2072-4292/13/4/686> ；*Performance comparison of RGB and multispectral VIs for SPAD (Hopea hainanensis).* Front. Plant Sci. (2022). <https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2022.928953/full>
12. *Non‑destructive leaf area / dry biomass allometry (A ≈ 0.60·L·W, >95% variance).* Trees – Springer（Tectona grandis）<https://link.springer.com/article/10.1007/s00468-015-1227-y> ；Jatropha curcas、Coffea arabica 同類模型。
13. ★ Pech‑Pacheco, J. L., et al. (2000). *Diatom autofocusing in brightfield microscopy: a comparative study (variance of Laplacian focus measure).* ICPR；另見 Pertuz, S., et al. (2013). *Analysis of focus measure operators for shape‑from‑focus.* Pattern Recognition, 46(5).
14. *Land‑based crop phenotyping: canopy height from stereo images (R² ≈ 0.92).* PLOS One. <https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0196671> ；*High‑throughput plant height by UAV RGB.* Front. Plant Sci. (2021). <https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.591587/full>
15. *ColorBayes: color correction of high‑throughput plant phenotyping images.* bioRxiv (2022). <https://www.biorxiv.org/content/10.1101/2022.03.01.482532v1.full>
16. ★ Bland, J. M., & Altman, D. G. (1986). *Statistical methods for assessing agreement between two methods of clinical measurement.* The Lancet, 327(8476), 307–310.
17. ★ Lin, L. I-K. (1989). *A concordance correlation coefficient to evaluate reproducibility.* Biometrics, 45(1), 255–268. DOI: 10.2307/2532051.〔CCC 公式經核對〕
18. *Power and sample size for repeated‑measures linear mixed models (GLIMMPSE).* <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12407473/>
19. *Cinnamomum osmophloeum leaf essential oil yield & chemotypes（葉採收、五倍於樹皮、可逐年收穫）.* Major chemotypes and antioxidative activity of the leaf essential oils of *C. osmophloeum* from a clonal orchard. Food Chemistry. <https://www.sciencedirect.com/science/article/abs/pii/S0308814607003019> ；綜述 <https://www.gavinpublishers.com/article/view/a-comprehensive-review-on-phytochemical-pharmacological-and-future-prospective-of-dietary-medicinal-plant-cinnamomum-osmophloeum-kanehira>

---

## 捌、變更紀錄

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-06-14 | v0.1 | 初版：文獻回顧（11 環節）、處理流程方法、a‑priori 驗證框架（CCC/Bland–Altman/MAPE 門檻）、統計分析計畫、討論與限制、19 筆參考文獻。對接 leaf-analysis-math、ADR-0004/0006、field-imaging-sop、annotation-plan |
| 2026-06-14 | v0.2 | 關鍵公式與書目經原文／權威源核對升級：TGI 補波段差分原式 + Hunt (2011) Agronomy J. 103(4):1090–1099 精確書目；GLI 公式經 PMC 表 2 核對 + Louhaichi (2001) DOI；Lin's CCC 補完整公式（經 Wikipedia/Biometrics 核對）+ DOI 10.2307/2532051；Easy Leaf Area 書目經 PubMed PMID 25202639 核對。引用標註核對來源 |
