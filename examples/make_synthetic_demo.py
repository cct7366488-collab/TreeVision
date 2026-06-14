#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""產生 validate_metrics.py 的合成示範資料（固定亂數種子，可重現）。

輸出 examples/synthetic_validation_data.csv，含三組「影像估計 vs 人工金標準」：
  - leaf_area   ：近 1:1、低雜訊 → 預期通過
  - plant_height：略有雜訊 → 預期通過
  - leaf_count  ：含些微低估（遮擋）→ 示範邊界情形

此為純合成資料（非真實客戶資料），可版控、可公開。
"""
import csv
import os
import numpy as np

rng = np.random.default_rng(2026)
n = 120

leaf_area_manual = rng.uniform(15, 130, n)
leaf_area_img = leaf_area_manual * 1.02 + rng.normal(0, 2.5, n)

plant_height_manual = rng.uniform(40, 320, n)
plant_height_img = plant_height_manual * 0.99 + rng.normal(0, 9, n)

# 葉片計數：影像在體計數受遮擋略低估（示範偏差）
leaf_count_manual = rng.integers(20, 200, n).astype(float)
leaf_count_img = np.maximum(0, leaf_count_manual * 0.92 + rng.normal(0, 6, n)).round()

out = os.path.join(os.path.dirname(__file__), "synthetic_validation_data.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["sample_id",
                "leaf_area_img", "leaf_area_manual",
                "plant_height_img", "plant_height_manual",
                "leaf_count_img", "leaf_count_manual"])
    for i in range(n):
        w.writerow([f"S{i+1:03d}",
                    round(leaf_area_img[i], 2), round(leaf_area_manual[i], 2),
                    round(plant_height_img[i], 1), round(plant_height_manual[i], 1),
                    int(leaf_count_img[i]), int(leaf_count_manual[i])])
print(f"WROTE {out} (n={n})")
