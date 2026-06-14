# examples/ — 驗證工具示範

本目錄以**合成資料**示範 [`scripts/validate_metrics.py`](../scripts/validate_metrics.py) 的一致性驗證流程，
讓團隊在真實資料到位前即可看懂輸出格式與判定邏輯。資料為純合成（非真實客戶資料），可公開。

## 內容

| 檔案 | 用途 |
|------|------|
| `make_synthetic_demo.py` | 產生固定種子之合成示範資料（可重現） |
| `synthetic_validation_data.csv` | 示範資料：3 組「影像估計 vs 人工金標準」 |
| `plots/`（gitignored） | 執行後產生的散點 + Bland-Altman 圖 |

## 快速執行

```powershell
# 1. （可選）重新產生示範資料
python examples/make_synthetic_demo.py

# 2. 跑一致性驗證並輸出圖
python scripts/validate_metrics.py `
  --csv examples/synthetic_validation_data.csv `
  --pair leaf_area_img:leaf_area_manual:leaf_area `
  --pair plant_height_img:plant_height_manual:plant_height `
  --pair leaf_count_img:leaf_count_manual:leaf_count `
  --outdir examples/plots
```

## 預期輸出（重點）

- **leaf_area**：近 1:1、低雜訊 → CCC ≈ 0.99、MAPE ≈ 4.5% → 通過。
- **plant_height**：略有雜訊 → MAPE ≈ 5.4% → 通過。
- **leaf_count**：示範**遮擋低估**——Bland-Altman 偏差約 −9、Deming 斜率 ≈ 0.93（影像系統性少算），但 MAPE ≈ 9% 仍在門檻內 → 通過。此例說明：即使 Pearson r ≈ 0.99，仍須看 CCC 與 Bland-Altman 才能揭露系統性偏差。

> 真實資料導入後，把 `--csv` 換成實測檔、欄位換成你的影像/人工欄即可，輸出格式與判定門檻完全相同（門檻定義見 [驗證報告 §肆](../docs/leaf-analysis-validation-report.md)）。

## 自我測試（不需任何 CSV）

```powershell
python scripts/validate_metrics.py --selftest --outdir examples/plots
```
