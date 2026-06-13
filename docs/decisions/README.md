# Architecture Decision Records（ADR）

採用 [ADR-style](https://adr.github.io/) 紀錄專案中**不可逆／長期影響**的決策。

## 規則

| 項目 | 規範 |
|------|------|
| 命名 | `NNNN-kebab-case-title.md`，編號連續不重用 |
| 必要章節 | Context、Options、Decision、Consequences |
| 狀態 | `proposed` → `accepted` / `superseded` / `rejected` |
| 變更 | 不直接修改舊 ADR；改用新 ADR `superseded by NNNN` |

## 何時要寫 ADR

- 技術選型（語言、框架、雲端供應商）
- 資料模型重大變更
- 演算法或評估指標調整
- 授權、隱私、合規相關決定
- 任何「未來新成員會問為什麼這樣做」的決策

## 索引

| # | 標題 | 狀態 | 決議日 |
|---|------|------|--------|
| [0001](0001-open-questions.md) | SPEC 開放問題的初版建議 | accepted | 2026-04-30 |
| [0002](0002-site-species-application-scope.md) | 場域、樹種與應用場景定向（鎖定大雪山土肉桂試驗） | **accepted** | 2026-05-04 |
| [0003](0003-schema-alignment-with-xlsx.md) | 資料模型對齊既有 XLSX 調查表 schema | proposed | — |
| [0004](0004-experimental-response-metrics.md) | 試驗響應指標體系（14 項影像可推得指標） | proposed | — |
| [0005](0005-fixed-camera-station-sop.md) | 固定攝點 SOP（試驗監測前提） | proposed | — |

## 附帶文件

| 檔案 | 用途 |
|------|------|
| [pi-consultation-questions.md](pi-consultation-questions.md) | 計畫主持人諮詢問題清單（22 題：A 級 7 + B 級 9 + C 級 6） |
