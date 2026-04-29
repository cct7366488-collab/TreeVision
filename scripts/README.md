# scripts/ — 輔助腳本

| 預期腳本 | 用途 |
|----------|------|
| `validate_metadata.py` | 檢查 `metadata/image_metadata.csv` 必填欄位、外鍵、命名規則 |
| `ingest_images.py` | 把 `raw/` 影像對應 metadata 寫入主表 |
| `image_quality_check.py` | 影像品質檢查（曝光、模糊、解析度） |
| `run_canopyseg.py` | 批次跑 CanopySeg 推論 |
| `run_leafinst.py` | 批次跑 LeafInst 推論 |
| `run_leafdefect.py` | 批次跑 LeafDefect 推論 |
| `aggregate_per_tree.py` | 彙整單張影像結果 → per_tree_daily |
| `make_image_report.py` | 產生單張影像 PDF 報告 |
| `make_tree_report.py` | 產生單棵樹健康履歷 PDF |
| `labelme_to_coco.py` | 標註格式轉換 |

> 此處只放輕量批次腳本。Web app（前後端、API server）建議分到獨立的 `app/` 目錄或獨立 repo。
