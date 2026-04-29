# TreeVision

**林木多尺度 AI 影像健康監測平台**
**Multi-scale AI Tree Health Monitoring Platform**

> 用 AI 看懂每一棵樹，從樹冠到葉片，建立可量化、可追蹤、可決策的森林健康資料。

---

## 專案定位

TreeVision 是一個結合樹冠影像、葉片近拍、AI 分割模型與健康監測指標的森林／樹木影像分析平台，用於支援林木健康診斷、葉片量測、病斑辨識、樹冠覆蓋率分析與長期監測管理。

工作流：
**資料上傳 → AI 分析 → 指標輸出 → 報表管理 → 長期追蹤**

---

## 文件入口

| 文件 | 用途 |
|------|------|
| [docs/SPEC.md](docs/SPEC.md) | 工程開發規格（SRS/PRD），含資料模型、API、模型 I/O |
| [docs/architecture.md](docs/architecture.md) | 系統架構與技術選型 |
| [docs/data-schema.md](docs/data-schema.md) | 影像 metadata、分析輸出欄位字典 |
| [docs/annotation-guideline.md](docs/annotation-guideline.md) | 標註規範（樹冠／葉片／病斑） |
| [docs/api.md](docs/api.md) | REST API 介面定義 |
| [docs/roadmap.md](docs/roadmap.md) | 開發里程碑與模型訓練計畫 |
| [schemas/](schemas/) | JSON Schema 檔（image_metadata、analysis_result 等） |

---

## 目錄結構

```
tree_multiscale_data/
├── docs/                工程規格、架構、API、標註規範
├── schemas/             JSON Schema 定義
├── scripts/             輔助腳本（資料檢查、轉檔、批次推論）
├── raw/                 原始影像（gitignored）
│   ├── canopy/          樹冠影像
│   └── leaf_closeup/    葉片近拍影像
├── processed/           前處理後影像（裁切、校色、resize）
├── canopy/              CanopySeg 模型輸出
│   ├── masks/           各類 mask（canopy/veg/yellow/brown）
│   └── overlays/        可視化疊圖
├── leaf_closeup/        LeafInst + LeafDefect 模型輸出
│   ├── masks/           實例分割 + 病徵 mask
│   └── overlays/        可視化疊圖
├── annotations/         標註檔（COCO / labelme JSON）
├── models/              訓練後模型權重（gitignored）
├── outputs/             推論結果表（CSV / Parquet）
│   ├── per_image/
│   ├── per_tree_daily/
│   └── per_site/
├── reports/             PDF / Excel 報表
├── metadata/            影像 metadata 主表
├── logs/                執行紀錄
└── plots/               臨時繪圖輸出
```

> 所有實際影像、模型權重、推論輸出檔均已在 `.gitignore` 排除，不會推送至 GitHub。
> 公開 repo 僅包含程式碼、規格文件、資料 schema、空目錄結構（透過 `.gitkeep`）。

---

## 環境設置

### 工作平台
- **程式碼／規格 repo**：`C:\Users\cct\projects\TreeVision\`（本機，**不在 Google Drive 同步資料夾下**，避免 `.git/` 與 Drive 同步衝突）
- **影像資料工作區（推薦）**：`H:\我的雲端硬碟\2026 tree_multiscale_data\`（Google Drive 同步，做雲端備份）
- **Obsidian vault**：`G:\我的雲端硬碟\secondbrain\10-專案\TreeVision\`（專案筆記與決策紀錄）
- **GitHub remote**：待建立（建議名稱 `TreeVision`）

### 同步策略
| 內容 | 儲存位置 | 同步方式 |
|------|----------|----------|
| 程式碼、規格、schema | `C:\Users\cct\projects\TreeVision\` → GitHub | `git push` |
| 影像資料、模型權重 | `H:\我的雲端硬碟\2026 tree_multiscale_data\` | Google Drive 自動備份（已 gitignore，不會推上 GitHub） |
| 專案筆記、會議紀錄 | Obsidian vault（G:） | Obsidian Sync / Google Drive |
| 報表正式版 | `reports/` + Obsidian | 手動匯出 |

> 此 repo 內 `raw/`、`processed/`、`canopy/masks/` 等資料夾保留為**結構樣板**（含 README 與 `.gitkeep`），實際影像放在 H: 的對應目錄。可選擇以 Junction Link 串接：
>
> ```cmd
> rmdir C:\Users\cct\projects\TreeVision\raw
> mklink /J C:\Users\cct\projects\TreeVision\raw "H:\我的雲端硬碟\2026 tree_multiscale_data\raw"
> ```
>
> 或在程式碼／設定檔以 `DATA_ROOT` 環境變數指向 H: 路徑（推薦做法，不依賴 OS 連結）。

---

## 快速開始

```powershell
# 1. clone（建立 GitHub repo 後）
git clone https://github.com/<owner>/TreeVision.git C:\Users\cct\projects\TreeVision
cd C:\Users\cct\projects\TreeVision

# 2. 建立 Python 虛擬環境（規劃中）
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt   # 待建立

# 3. 設定資料根路徑（指向 Google Drive 上的影像資料夾）
$env:TREEVISION_DATA_ROOT = "H:\我的雲端硬碟\2026 tree_multiscale_data"

# 4. 讀規格
# 直接打開 docs/SPEC.md
```

---

## 授權

本專案（含程式碼、規格文件、JSON Schema）採用 [Apache License 2.0](LICENSE)。

簡述：
- ✅ 允許**自由使用**（個人、研究、商業、政府計畫皆可）
- ✅ 允許**修改與再散布**
- ✅ 含**專利保護條款**（貢獻者不得反告使用者侵犯其專利）
- ⚠️ 必須保留**原作者署名**與授權通知（見 [NOTICE](NOTICE)）
- ⚠️ 衍生作品如有修改，須**標示變更內容**

> 影像資料與訓練模型權重**不在此授權範圍**，依資料治理政策另行規範。

## 引用

```
TreeVision Contributors (2026). TreeVision: Multi-scale AI Tree Health
Monitoring Platform. https://github.com/cct7366488-collab/TreeVision
```
