# Firebase 資料對應表與啟用 Runbook（treevision-data）

| 項目 | 內容 |
|------|------|
| 版本 | v0.1 |
| 文件日期 | 2026-06-14 |
| 狀態 | **`treevision-data` 尚未建立；暫不啟用 Blaze**（理由見 §壹） |
| 上位策略 | 全域 [Cloud.md](file:///C:/Users/cct/.claude/Cloud.md) 三軌分流（資料→Firebase／程式碼→GitHub／工作日誌→Obsidian） |
| 帳號 | `cct7366488@gmail.com`（CLI 已認證；現有專案 forestry-rs-monitor／forestry-teaching／pdf-scanner-tw）|

> 本文件即 Cloud.md〔陸、四〕要求「每專案 README 應包含的本機→雲端對應表」之 TreeVision 落地版，並附啟用 runbook。**先把對應規則與步驟備妥，待第一批試拍影像就緒時再執行不可逆的計費啟用。**

---

## 壹、為何現在不啟用 Blaze（審查判斷）

一、**目前無實質資料可上**：資料軌僅有野外速查卡 `.docx`/`.pdf`（約 0.37 MB，本機 `田野作業\`），尚無任何試拍影像、模型權重或推論輸出。

二、**Blaze 是計費啟用、對外且不易回退**：需在 Console 綁定信用卡、啟用 Billing Account；對一個空專案提早開計費只增帳務暴露面、無收益。

三、**容量門檻尚未觸發**：依 [ADR-0006 §Consequences](decisions/0006-image-sampling-design.md) 重估，例行 in-situ 約 **6,900 張/年**（每處理 12 株 × 16 處理格 × 3 攝點 × ~12 場次）。此量級終將破 Spark plan 5 GB，**故 Blaze 必要、但時機是「第一批 Pilot 影像就緒」而非現在**。

四、**結論**：本次完成可逆 groundwork（對應表＋命名規範＋啟用 runbook）；計費啟用列為觸發式待辦（§陸）。

---

## 貳、本機 → 雲端對應表

> 待 `treevision-data` 建立後生效。`H:\…\` 指 `H:\我的雲端硬碟\2026 tree_multiscale_data\`。

| 本地路徑 | Firebase 目的地 | 說明 |
|---------|----------------|------|
| `H:\…\raw\canopy\` | `gs://treevision-data/raw/canopy/` | 原始樹冠影像 |
| `H:\…\raw\leaf_closeup\` | `gs://treevision-data/raw/leaf_closeup/` | 原始葉片近拍 |
| `H:\…\raw\whole_plant\` | `gs://treevision-data/raw/whole_plant/` | 全株影像（v0.2 NEW） |
| `H:\…\processed\` | `gs://treevision-data/processed/` | 前處理後影像（校色／resize／裁切） |
| `H:\…\canopy\masks\`、`leaf_closeup\masks\` | `gs://treevision-data/masks/` | 模型輸出遮罩 |
| `H:\…\models\*.pt` | `gs://treevision-data/models/`（受權限保護） | 訓練後模型權重 |
| `H:\…\outputs\*.csv` / `*.parquet` | Firestore `image_metric` / `treatment_response_summary` collection | 結構化指標 |
| `metadata\image_metadata.csv` | Firestore `image` collection | 影像 metadata |
| `H:\…\reports\*.pdf` | `gs://treevision-data/reports/` | 正式報表 |
| `H:\…\田野作業\*.docx` / `*.pdf` | `gs://treevision-data/fieldwork/`（選用） | 田野卡片等小型交付物 |

### Firestore 命名空間（避免跨專案碰撞）

依 Cloud.md〔陸、二〕，集合以專案前綴隔離；treevision-data 為獨立專案，集合直接命名：`image`、`image_metric`、`leaf_instance`、`treatment_response_summary`、`experiment_anova_result` 等（對齊 [SPEC §陸 ER](SPEC.md)、[ADR-0003](decisions/0003-schema-alignment-with-xlsx.md)）。

---

## 參、不上傳清單（永不上雲，對齊 Cloud.md〔伍〕）

| 類別 | 範例 | 處置 |
|------|------|------|
| 認證／金鑰 | `serviceAccountKey.json`、`.env`、API keys | `.gitignore` + 不放 Storage |
| 未脫敏 GPS | 樣樹精確座標、保育類物種位置 | 依 [ADR-0001 議題 5](decisions/0001-open-questions.md) 三層遮蔽後始可進公開層 |
| 個資 | 拍攝者／地主姓名聯絡方式 | 脫敏後才上；目前僅 `device_id`/`user_id` |
| 第三方授權禁散布 | 商業圖資、購買訓練資料 | 僅本機 |

> Storage Rules 與 Firestore Rules 預設**全擋**，僅以白名單放行 `raw/`、`processed/`、`masks/`、`reports/`；`models/` 限管理員。建立專案時一併部署 rules（§伍-3）。

---

## 肆、容量與計費預估

| 項目 | 估計 |
|------|------|
| 例行影像量 | ~6,900 張/年（[ADR-0006](decisions/0006-image-sampling-design.md)）|
| 單張原圖 | 葉片近拍 ≥ 4000×3000、~8–15 MB；全株 ~5–10 MB |
| 年度原始影像 | 約 **50–90 GB/年**（遠破 Spark 5 GB）|
| 結論 | 需 Blaze；Storage 為主要成本（GB-month + 下載流量），Firestore 文件量小、成本可忽略 |

> 成本控管：原圖存 Storage、僅指標進 Firestore；遮罩／疊圖可選擇性上傳或僅留本機；設定生命週期規則將舊原圖轉 Nearline/Coldline 降費。

---

## 伍、Blaze 啟用 Runbook（第一批影像就緒時執行）

> 計費啟用步驟（1）（2）須在 **Firebase Console** 由你本人操作；其餘 CLI 步驟我可協助執行。

### 一、建立專案與計費

1. （Console）建立專案 `treevision-data`：<https://console.firebase.google.com> → 新增專案。
2. （Console）升級 **Blaze plan**：左下 ⚙ → 用量與帳單 → 修改方案 → Blaze，綁定 Billing Account（信用卡）。**此為不可逆對外步驟，由你執行。**
3. （CLI，可代為執行）綁定本地：

```powershell
firebase projects:list                       # 確認 treevision-data 已出現
firebase use --add                           # 選 treevision-data，alias 設 treevision
firebase use treevision                       # 切換
```

### 二、初始化服務

4. （Console 或 CLI）建立 Cloud Storage bucket（地區建議 `asia-east1`，與 forestry-rs-monitor 一致）。
5. （CLI）部署 Storage / Firestore Rules（預設全擋＋白名單）：

```powershell
# 於 repo 內準備 firebase.json / storage.rules / firestore.rules 後
firebase deploy --only storage,firestore:rules --project treevision-data
```

### 三、首批上傳（驗證流程）

6. 大量小檔用 `gsutil` 批次（分批 sleep 避免限流，Cloud.md〔陸、一〕）：

```powershell
gsutil -m rsync -r "H:\我的雲端硬碟\2026 tree_multiscale_data\raw\whole_plant" `
  gs://treevision-data/raw/whole_plant
```

7. 指標 CSV → Firestore：以 `firebase-admin`（Python）batch 寫入（每批 ≤ 500 doc，Cloud.md〔陸、二〕）。

### 四、收尾

8. 將實際 bucket／集合路徑回填本文件§貳，並更新 Cloud.md〔貳、三〕TreeVision 列（Firebase Project ID 由「待建立」改為 `treevision-data`）。

---

## 陸、觸發條件（何時執行 §伍）

**當下列任一成立即啟動 Blaze 建置**：

一、第一批 Pilot 試拍影像（依 [pilot-protocol](pilot-protocol.md)，每處理 5–10 株）下載就緒，需雲端備份／共享。

二、本機 `H:\…\raw\` 影像總量接近 4 GB（逼近 Spark 上限前預留緩衝）。

三、需多人／多裝置存取同一影像集（合作社團隊協作）。

> 在此之前，影像沿用 Google Drive（`H:\` 自動備份）作為唯一雲端備援，符合 Cloud.md 範圍界定。

---

## 柒、變更紀錄

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-06-14 | v0.1 | 初版：本機→雲端對應表、不上傳清單、容量估算、Blaze 啟用 runbook、觸發條件；確立「對應表先備、計費後啟」之審查立場 |
