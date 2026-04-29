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

| # | 標題 | 狀態 |
|---|------|------|
| [0001](0001-open-questions.md) | SPEC 開放問題的初版建議 | proposed |
