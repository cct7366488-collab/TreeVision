#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validate_metrics.py — 影像指標 vs 人工金標準 一致性驗證工具

把 docs/leaf-analysis-validation-report.md 的 a-priori 驗證協定（第肆、伍章）
操作化為可執行程式。真實資料導入後，餵入「影像估計值」與「人工量測值」即可
自動產出方法一致性報告與通過/未通過判定。

實作之一致性統計（皆有文獻依據，見驗證報告參考文獻）：
  - Lin 一致性相關係數 CCC          [Lin 1989, Biometrics 45(1):255-268]
  - Bland-Altman 偏差與一致界限      [Bland & Altman 1986, Lancet]
  - MAPE / MAE
  - Pearson r
  - Deming 迴歸（量測誤差存在於兩軸時的迴歸）

用法：
  # 自我測試（合成資料，不需真實資料即可驗證程式可跑）
  python scripts/validate_metrics.py --selftest

  # 真實資料：CSV 含多組 (影像欄, 人工欄)，逐指標驗收
  python scripts/validate_metrics.py --csv data.csv \
      --pair leaf_area_img:leaf_area_manual:leaf_area \
      --pair plant_height_img:plant_height_manual:plant_height
"""
from __future__ import annotations
import argparse
import sys
import numpy as np

# ---- 驗收門檻（對齊 docs/leaf-analysis-validation-report.md 第肆章二節）----
# 每個 metric_key -> dict(主驗收統計與門檻)。None 表示該統計不設門檻、僅報告。
ACCEPTANCE = {
    "leaf_area":     {"mape_max": 0.08, "ccc_min": 0.80, "label": "葉面積(A4)"},
    "leaf_count":    {"mape_max": 0.15, "ccc_min": None, "label": "葉片計數(A1)"},
    "leaf_color":    {"r_min": 0.70,    "ccc_min": None, "label": "葉色 GLI/TGI vs SPAD"},
    "plant_height":  {"mape_max": 0.10, "ccc_min": None, "label": "株高(C1)"},
    "yield":         {"ccc_min": 0.70,  "mape_max": None, "label": "採收量估計"},
    "defect_ratio":  {"mae_max": 0.05,  "ccc_min": None, "label": "病斑率(B4/B5)"},
    "_default":      {"ccc_min": 0.70,  "mape_max": None, "label": "(未指定)"},
}


def pearson_r(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 2:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def ccc(x: np.ndarray, y: np.ndarray) -> float:
    """Lin 一致性相關係數。ρc = 2ρσxσy / (σx² + σy² + (μx-μy)²)。"""
    x, y = np.asarray(x, float), np.asarray(y, float)
    mx, my = x.mean(), y.mean()
    # 母體變異數/共變異數（除以 N，與 Lin 原式一致）
    vx = x.var(ddof=0)
    vy = y.var(ddof=0)
    sxy = ((x - mx) * (y - my)).mean()
    denom = vx + vy + (mx - my) ** 2
    return float(2 * sxy / denom) if denom > 0 else float("nan")


def mape(true: np.ndarray, pred: np.ndarray) -> float:
    """平均絕對百分比誤差；以人工量測為分母，排除分母為 0。"""
    true, pred = np.asarray(true, float), np.asarray(pred, float)
    m = true != 0
    if not m.any():
        return float("nan")
    return float(np.mean(np.abs((pred[m] - true[m]) / true[m])))


def mae(true: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(pred, float) - np.asarray(true, float))))


def bland_altman(img: np.ndarray, ref: np.ndarray) -> dict:
    """回傳偏差、一致界限(LoA)，及比例性偏差檢定（diff 對 mean 之迴歸斜率）。"""
    img, ref = np.asarray(img, float), np.asarray(ref, float)
    diff = img - ref
    mean = (img + ref) / 2.0
    bias = float(diff.mean())
    sd = float(diff.std(ddof=1)) if diff.size > 1 else float("nan")
    loa_lower, loa_upper = bias - 1.96 * sd, bias + 1.96 * sd
    # 比例性偏差：diff ~ a + b*mean，b 顯著異於 0 表示有比例偏差
    prop_slope = float("nan")
    if mean.size > 2 and np.ptp(mean) > 0:
        b, a = np.polyfit(mean, diff, 1)
        prop_slope = float(b)
    return {
        "bias": bias, "sd_diff": sd,
        "loa_lower": loa_lower, "loa_upper": loa_upper,
        "proportional_bias_slope": prop_slope,
    }


def deming_regression(x: np.ndarray, y: np.ndarray, lam: float = 1.0) -> dict:
    """Deming 迴歸（誤差比 λ = var(ε_y)/var(ε_x)，預設 1）。回傳斜率、截距。"""
    x, y = np.asarray(x, float), np.asarray(y, float)
    mx, my = x.mean(), y.mean()
    sxx = ((x - mx) ** 2).mean()
    syy = ((y - my) ** 2).mean()
    sxy = ((x - mx) * (y - my)).mean()
    if sxy == 0:
        return {"slope": float("nan"), "intercept": float("nan")}
    slope = (syy - lam * sxx + np.sqrt((syy - lam * sxx) ** 2 + 4 * lam * sxy ** 2)) / (2 * sxy)
    intercept = my - slope * mx
    return {"slope": float(slope), "intercept": float(intercept)}


def evaluate_pair(img: np.ndarray, ref: np.ndarray, metric_key: str) -> dict:
    """對單一指標跑完整一致性電池並依門檻判定 pass/fail。"""
    img, ref = np.asarray(img, float), np.asarray(ref, float)
    crit = ACCEPTANCE.get(metric_key, ACCEPTANCE["_default"])
    stats = {
        "n": int(img.size),
        "pearson_r": pearson_r(ref, img),
        "ccc": ccc(ref, img),
        "mape": mape(ref, img),
        "mae": mae(ref, img),
        **bland_altman(img, ref),
        "deming": deming_regression(ref, img),
    }
    checks, passed = [], True
    if crit.get("ccc_min") is not None:
        ok = stats["ccc"] >= crit["ccc_min"]
        checks.append(("CCC", stats["ccc"], f">= {crit['ccc_min']}", ok)); passed &= ok
    if crit.get("mape_max") is not None:
        ok = stats["mape"] <= crit["mape_max"]
        checks.append(("MAPE", stats["mape"], f"<= {crit['mape_max']}", ok)); passed &= ok
    if crit.get("mae_max") is not None:
        ok = stats["mae"] <= crit["mae_max"]
        checks.append(("MAE", stats["mae"], f"<= {crit['mae_max']}", ok)); passed &= ok
    if crit.get("r_min") is not None:
        ok = stats["pearson_r"] >= crit["r_min"]
        checks.append(("Pearson r", stats["pearson_r"], f">= {crit['r_min']}", ok)); passed &= ok
    stats["checks"] = checks
    stats["passed"] = bool(passed) if checks else None
    stats["label"] = crit["label"]
    return stats


def format_report(name: str, metric_key: str, s: dict) -> str:
    lines = []
    lines.append(f"── 指標：{name}  [{s['label']}]  n={s['n']} ──")
    lines.append(f"  Pearson r = {s['pearson_r']:.3f} | CCC = {s['ccc']:.3f} | "
                 f"MAPE = {s['mape']*100:.1f}% | MAE = {s['mae']:.4g}")
    lines.append(f"  Bland-Altman: 偏差 {s['bias']:.4g}, "
                 f"一致界限 [{s['loa_lower']:.4g}, {s['loa_upper']:.4g}], "
                 f"比例偏差斜率 {s['proportional_bias_slope']:.3f}")
    lines.append(f"  Deming: y = {s['deming']['slope']:.3f}·x + {s['deming']['intercept']:.4g}")
    for stat, val, rule, ok in s["checks"]:
        disp = f"{val*100:.1f}%" if stat in ("MAPE",) else f"{val:.3f}"
        lines.append(f"  [{'PASS' if ok else 'FAIL'}] {stat} = {disp}  (門檻 {rule})")
    if s["passed"] is not None:
        lines.append(f"  → 判定：{'通過 ✔' if s['passed'] else '未通過 ✗（需迭代模型/校正）'}")
    else:
        lines.append("  → 判定：（此指標未設門檻，僅報告）")
    return "\n".join(lines)


def make_plots(img, ref, metric_key: str, name: str, outdir: str) -> str:
    """繪散點（含 1:1 線與 Deming 擬合）+ Bland-Altman 圖，存 PNG。標籤用英文避免 CJK 缺字。"""
    import os
    import matplotlib
    matplotlib.use("Agg")  # 非互動後端
    import matplotlib.pyplot as plt

    img, ref = np.asarray(img, float), np.asarray(ref, float)
    s = evaluate_pair(img, ref, metric_key)
    os.makedirs(outdir, exist_ok=True)
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 4.6))

    # 左：散點 + 1:1 線 + Deming 擬合
    lo = float(min(ref.min(), img.min())); hi = float(max(ref.max(), img.max()))
    pad = (hi - lo) * 0.05 or 1.0
    axL.scatter(ref, img, s=18, alpha=0.6, edgecolor="none")
    axL.plot([lo - pad, hi + pad], [lo - pad, hi + pad], "k--", lw=1, label="1:1 line")
    sl, ic = s["deming"]["slope"], s["deming"]["intercept"]
    xs = np.array([lo - pad, hi + pad])
    axL.plot(xs, sl * xs + ic, "r-", lw=1.2, label=f"Deming: y={sl:.2f}x+{ic:.2f}")
    axL.set_xlabel("Manual (reference)"); axL.set_ylabel("Image estimate")
    axL.set_title(f"{name}  (CCC={s['ccc']:.3f}, r={s['pearson_r']:.3f}, MAPE={s['mape']*100:.1f}%)", fontsize=9)
    axL.legend(fontsize=8); axL.grid(alpha=0.25); axL.set_aspect("equal", "box")

    # 右：Bland-Altman
    mean = (img + ref) / 2.0; diff = img - ref
    axR.scatter(mean, diff, s=18, alpha=0.6, edgecolor="none")
    axR.axhline(s["bias"], color="b", lw=1.2, label=f"bias={s['bias']:.2f}")
    axR.axhline(s["loa_upper"], color="grey", ls="--", lw=1, label=f"+1.96SD={s['loa_upper']:.2f}")
    axR.axhline(s["loa_lower"], color="grey", ls="--", lw=1, label=f"-1.96SD={s['loa_lower']:.2f}")
    axR.set_xlabel("Mean of methods"); axR.set_ylabel("Difference (image - manual)")
    axR.set_title(f"Bland-Altman  (prop.bias slope={s['proportional_bias_slope']:.3f})", fontsize=9)
    axR.legend(fontsize=8); axR.grid(alpha=0.25)

    verdict = "PASS" if s["passed"] else ("FAIL" if s["passed"] is False else "report")
    fig.suptitle(f"[{verdict}] {metric_key} — {name}", fontsize=11, y=1.02)
    fig.tight_layout()
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in f"{metric_key}_{name}")
    path = os.path.join(outdir, f"agreement_{safe}.png")
    fig.savefig(path, dpi=130, bbox_inches="tight"); plt.close(fig)
    return path


def run_csv(csv_path: str, pairs: list[str], outdir: str | None = None) -> int:
    import pandas as pd
    df = pd.read_csv(csv_path)
    any_fail = False
    print(f"== 一致性驗證報告：{csv_path} ==\n")
    for spec in pairs:
        parts = spec.split(":")
        if len(parts) != 3:
            print(f"[略過] --pair 格式須為 影像欄:人工欄:metric_key（得到 {spec!r}）")
            continue
        img_col, ref_col, key = parts
        if img_col not in df or ref_col not in df:
            print(f"[略過] 找不到欄位 {img_col} 或 {ref_col}")
            continue
        sub = df[[img_col, ref_col]].dropna()
        s = evaluate_pair(sub[img_col].values, sub[ref_col].values, key)
        print(format_report(f"{img_col} vs {ref_col}", key, s) + "\n")
        if outdir:
            p = make_plots(sub[img_col].values, sub[ref_col].values, key, f"{img_col}_vs_{ref_col}", outdir)
            print(f"    圖已存：{p}\n")
        if s["passed"] is False:
            any_fail = True
    return 1 if any_fail else 0


def selftest(outdir: str | None = None) -> int:
    """以合成資料驗證程式可跑、統計合理（不需真實資料）。"""
    rng = np.random.default_rng(42)
    print("== 自我測試（合成資料）==\n")

    # 案例 1：好的影像方法（高一致），應 PASS
    ref = rng.uniform(20, 120, 200)                      # 人工葉面積 cm²
    img = ref * 1.01 + rng.normal(0, 2.0, ref.size)      # 影像：近 1:1、低雜訊
    s1 = evaluate_pair(img, ref, "leaf_area")
    print(format_report("leaf_area_img vs manual（理想）", "leaf_area", s1) + "\n")
    assert s1["ccc"] > 0.95 and s1["passed"] is True, "理想案例應通過且 CCC 高"

    # 案例 2：有系統性比例偏差 + 高雜訊，應 FAIL（示警）
    img_bad = ref * 1.3 + rng.normal(0, 15, ref.size)    # 高估 30% + 高雜訊
    s2 = evaluate_pair(img_bad, ref, "leaf_area")
    print(format_report("leaf_area_img vs manual（劣化）", "leaf_area", s2) + "\n")
    assert s2["passed"] is False, "劣化案例應未通過"
    assert abs(s2["proportional_bias_slope"]) > 0.1, "應偵測到比例偏差"

    # 案例 3：株高（cm），中等雜訊，檢查 MAPE 門檻
    h_ref = rng.uniform(50, 300, 150)
    h_img = h_ref * 1.0 + rng.normal(0, 8, h_ref.size)
    s3 = evaluate_pair(h_img, h_ref, "plant_height")
    print(format_report("plant_height_img vs manual", "plant_height", s3) + "\n")

    if outdir:
        for arr_img, arr_ref, key, nm in [
            (img, ref, "leaf_area", "ideal"),
            (img_bad, ref, "leaf_area", "degraded"),
            (h_img, h_ref, "plant_height", "selftest"),
        ]:
            print(f"    圖已存：{make_plots(arr_img, arr_ref, key, nm, outdir)}")
        print()

    # 已知數值健全性檢查
    x = np.array([1., 2, 3, 4, 5])
    assert abs(ccc(x, x) - 1.0) < 1e-9, "CCC(x,x) 應為 1"
    assert abs(mape(x, x)) < 1e-12, "MAPE(x,x) 應為 0"

    print("✔ 自我測試全部通過：統計函式與門檻判定運作正常。")
    print("  真實資料導入後，改用 --csv 即可對實測值產出相同報告。")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="影像指標 vs 人工金標準 一致性驗證")
    p.add_argument("--selftest", action="store_true", help="以合成資料自我測試")
    p.add_argument("--csv", help="輸入 CSV 路徑")
    p.add_argument("--pair", action="append", default=[],
                   help="影像欄:人工欄:metric_key（可重複）")
    p.add_argument("--outdir", help="輸出散點/Bland-Altman 圖之資料夾（需 matplotlib）")
    a = p.parse_args(argv)
    if a.selftest:
        return selftest(a.outdir)
    if a.csv:
        if not a.pair:
            p.error("--csv 需搭配至少一個 --pair")
        return run_csv(a.csv, a.pair, a.outdir)
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
