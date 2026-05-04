# References｜參考資料目錄

> TreeVision 系統設計所依據的外部資料來源彙整。
> 此目錄不存放原始二進位檔（依 [Cloud.md](file:///C:/Users/cct/.claude/Cloud.md) 三軌分流規則，二進位檔保留在 Google Drive），
> 僅存放「結構化彙整 markdown」+「來源索引」以利在 git 中追蹤上下文演進。

---

## 文件清單

| 檔案 | 內容 | 對 TreeVision 的影響範圍 |
|------|------|------------------------|
| [`cinnamon-trial-context.md`](./cinnamon-trial-context.md) | 大雪山 / 八仙山土肉桂試驗樣區的官方試驗設計、現有調查表結構、修剪技術 SOP 全面彙整 | SPEC、schema、SOP、模型架構、報表 — **全面性** |
| [`source-files-index.md`](./source-files-index.md) | 原始參考檔案的儲存路徑、版本、來源說明 | 可追溯性與引用 |

---

## 維護規則

1. 新增參考資料時，**先彙整成 markdown 放這裡**，不要直接把原始檔（DOCX / PPTX / XLSX / PDF）放進 repo。
2. 若需保留原始檔的本地副本，放在 `H:\我的雲端硬碟\2026 tree_multiscale_data\references\` 下（Drive 自動同步雲端），repo 內僅記錄路徑。
3. 引用原始檔時，在 markdown 中以「檔名 + 章節 + 段落」標記，方便回查。
4. 重大版本變動時，在 `source-files-index.md` 補一筆變更紀錄。
