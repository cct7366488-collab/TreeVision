# -*- coding: utf-8 -*-
"""
標註者一致性（inter-annotator agreement）：比對兩位標註者對「同一批影像」的 COCO
標註，計算每類別的 IoU 一致性與漏/誤標，依 docs/annotation-plan.md §伍 品質門檻
判 pass/fail。對應 §肆-三「二人交叉複標隨機 5% → 計 IoU」工作流。

定位：import_coco.py 把標註入庫；本工具在「入庫前/抽查時」驗收標註集品質——
門檻不過代表標註規範需釐清、重標，不可直接拿去訓練。

方法（無重依賴，純 stdlib）：
  - rectangle（scale_object）→ bbox 解析式 IoU。
  - polygon（葉片/病徵/樹冠/全株）→ 取 segmentation[0]，網格化（ray-casting
    point-in-polygon）算遮罩 IoU，正確處理非凸多邊形。
  - points（kp_*）→ v1 暫不計 IoU（僅回報數量）。
  - 配對：每（影像×類別）以最大 IoU 貪婪配對 A↔B；配不到的計漏/誤標。

門檻（annotation-plan §伍 / 標註規範 §肆-四）：
  病徵（lesion/chlorosis/necrosis/hole）平均 IoU ≥ 0.55；
  葉片/樹冠/全株/尺度物 ≥ 0.85；漏標+誤標率 < 5%。

用法：
    python scripts/annotation_agreement.py --coco-a A標.json --coco-b B標.json
    python scripts/annotation_agreement.py --selftest
"""
import argparse
import json
import os
import sys

try:  # 確保 ✓/✗ 等符號在 Windows cp950 主控台也能輸出
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEFAULT_LABELS = os.path.join(REPO, "annotations", "cvat-labels.json")

DEFECT = {"lesion", "chlorosis", "necrosis", "hole"}
IOU_THRESHOLD = {"_defect": 0.55, "_default": 0.85}
DISAGREE_MAX = 0.05  # 漏標+誤標率上限


def label_thresh(cat):
    return IOU_THRESHOLD["_defect"] if cat in DEFECT else IOU_THRESHOLD["_default"]


def load_label_types(path):
    with open(path, encoding="utf-8") as f:
        return {l["name"]: l["type"] for l in json.load(f)}


def _pip(x, y, poly):
    """ray-casting point-in-polygon；poly=[(x,y),...]。"""
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def bbox_iou(a, b):
    """a,b = [x,y,w,h]。"""
    ax0, ay0, aw, ah = a
    bx0, by0, bw, bh = b
    ax1, ay1, bx1, by1 = ax0 + aw, ay0 + ah, bx0 + bw, by0 + bh
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def poly_iou(seg_a, seg_b, res=160):
    """seg_* = flat [x1,y1,x2,y2,...]（COCO segmentation[0]）。網格化遮罩 IoU。"""
    A = list(zip(seg_a[0::2], seg_a[1::2]))
    B = list(zip(seg_b[0::2], seg_b[1::2]))
    if len(A) < 3 or len(B) < 3:
        return 0.0
    xs = [p[0] for p in A + B]
    ys = [p[1] for p in A + B]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    if w <= 0 or h <= 0:
        return 0.0
    nx = res if w >= h else max(1, int(round(res * w / h)))
    ny = res if h >= w else max(1, int(round(res * h / w)))
    inter = ua = ub = 0
    for j in range(ny):
        cy = miny + (j + 0.5) * h / ny
        for i in range(nx):
            cx = minx + (i + 0.5) * w / nx
            ina = _pip(cx, cy, A)
            inb = _pip(cx, cy, B)
            if ina:
                ua += 1
            if inb:
                ub += 1
            if ina and inb:
                inter += 1
    union = ua + ub - inter
    return inter / union if union > 0 else 0.0


def ann_iou(a, b, geom):
    if geom == "rectangle":
        return bbox_iou(a["bbox"], b["bbox"])
    if geom == "polygon":
        sa = a.get("segmentation") or []
        sb = b.get("segmentation") or []
        if sa and sb:
            return poly_iou(sa[0], sb[0])
        # 退而求其次：無多邊形時用 bbox
        if a.get("bbox") and b.get("bbox"):
            return bbox_iou(a["bbox"], b["bbox"])
    return 0.0


def index_by_image_cat(coco):
    """COCO → {(file_name, category_name): [annotations]}。"""
    cat = {c["id"]: c["name"] for c in coco.get("categories", [])}
    img = {im["id"]: im["file_name"] for im in coco.get("images", [])}
    out = {}
    for a in coco.get("annotations", []):
        key = (img.get(a["image_id"]), cat.get(a["category_id"]))
        out.setdefault(key, []).append(a)
    return out


def greedy_match(listA, listB, geom, min_iou=0.05):
    """貪婪配對；回傳 (matched_ious, n_unmatched_a, n_unmatched_b)。"""
    pairs = []
    for ia, a in enumerate(listA):
        for ib, b in enumerate(listB):
            pairs.append((ann_iou(a, b, geom), ia, ib))
    pairs.sort(reverse=True)
    usedA, usedB, ious = set(), set(), []
    for iou, ia, ib in pairs:
        if iou < min_iou:
            break
        if ia in usedA or ib in usedB:
            continue
        usedA.add(ia)
        usedB.add(ib)
        ious.append(iou)
    return ious, len(listA) - len(usedA), len(listB) - len(usedB)


def compare(coco_a, coco_b, label_types):
    idxA = index_by_image_cat(coco_a)
    idxB = index_by_image_cat(coco_b)
    cats = sorted({k[1] for k in list(idxA) + list(idxB) if k[1]})
    per = {}
    for cat in cats:
        geom = label_types.get(cat)
        ious, ua_tot, ub_tot, n_match = [], 0, 0, 0
        keys = {k for k in list(idxA) + list(idxB) if k[1] == cat}
        for key in keys:
            la, lb = idxA.get(key, []), idxB.get(key, [])
            if geom == "points":
                ua_tot += abs(len(la) - len(lb))  # 點類僅看數量差
                continue
            m, ua, ub = greedy_match(la, lb, geom)
            ious += m
            n_match += len(m)
            ua_tot += ua
            ub_tot += ub
        per[cat] = {
            "geom": geom,
            "n_match": n_match,
            "mean_iou": (sum(ious) / len(ious)) if ious else None,
            "unmatched_a": ua_tot,
            "unmatched_b": ub_tot,
        }
    return per


def report(per):
    print("=== 標註者一致性（annotation-plan §伍）===")
    print("{:16s} {:>8s} {:>8s} {:>9s} {:>9s} {:>7s}  {}".format(
        "類別", "配對數", "平均IoU", "漏/誤A", "漏/誤B", "門檻", "判定"))
    all_pass = True
    for cat in sorted(per):
        d = per[cat]
        if d["geom"] == "points":
            print("{:16s} {:>8s} {:>8s} {:>9d} {:>9s} {:>7s}  {}".format(
                cat, "-", "(點類)", d["unmatched_a"], "-", "-", "僅計數量差"))
            continue
        thr = label_thresh(cat)
        mi = d["mean_iou"]
        total = d["n_match"] + d["unmatched_a"] + d["unmatched_b"]
        disagree = (d["unmatched_a"] + d["unmatched_b"]) / total if total else 0.0
        ok = (mi is not None and mi >= thr) and (disagree < DISAGREE_MAX)
        all_pass = all_pass and ok
        print("{:16s} {:>8d} {:>8s} {:>9d} {:>9d} {:>7.2f}  {}".format(
            cat, d["n_match"], ("%.3f" % mi) if mi is not None else "n/a",
            d["unmatched_a"], d["unmatched_b"], thr,
            ("✓PASS" if ok else "✗FAIL") + (" (漏誤率%.0f%%)" % (disagree * 100) if disagree >= DISAGREE_MAX else "")))
    print("\nRESULT:", "✓ 全部達標，標註集可進訓練" if all_pass else "✗ 有類別未達標 → 釐清規範/重標後再驗")
    return 0 if all_pass else 1


# ── 自測（合成） ──────────────────────────────────────────────
def _sq(x0, y0, x1, y1):
    return [x0, y0, x1, y0, x1, y1, x0, y1]


def _coco(anns):
    return {
        "images": [{"id": 1, "file_name": "img1.jpg", "width": 500, "height": 500}],
        "categories": [{"id": 1, "name": "leaf"}, {"id": 2, "name": "lesion"}],
        "annotations": anns,
    }


def selftest():
    lt = load_label_types(DEFAULT_LABELS)
    # leaf：位移 5（IoU≈0.905，門檻 0.85 → PASS）
    # lesion：位移 10（IoU≈0.667，門檻 0.55 → PASS），且 A 多一個未配對（漏/誤）
    A = _coco([
        {"id": 1, "image_id": 1, "category_id": 1, "segmentation": [_sq(0, 0, 100, 100)], "bbox": [0, 0, 100, 100], "area": 10000},
        {"id": 2, "image_id": 1, "category_id": 2, "segmentation": [_sq(0, 0, 50, 50)], "bbox": [0, 0, 50, 50], "area": 2500},
        {"id": 3, "image_id": 1, "category_id": 2, "segmentation": [_sq(300, 300, 340, 340)], "bbox": [300, 300, 40, 40], "area": 1600},
    ])
    B = _coco([
        {"id": 1, "image_id": 1, "category_id": 1, "segmentation": [_sq(5, 0, 105, 100)], "bbox": [5, 0, 100, 100], "area": 10000},
        {"id": 2, "image_id": 1, "category_id": 2, "segmentation": [_sq(10, 0, 60, 50)], "bbox": [10, 0, 50, 50], "area": 2500},
    ])
    per = compare(A, B, lt)

    leaf = per["leaf"]
    assert leaf["n_match"] == 1 and abs(leaf["mean_iou"] - 0.905) < 0.03, leaf
    les = per["lesion"]
    assert les["n_match"] == 1 and abs(les["mean_iou"] - 0.667) < 0.03, les
    assert les["unmatched_a"] == 1 and les["unmatched_b"] == 0, les
    # bbox IoU 解析式檢查（位移 25、寬 100 → inter75/union125=0.6）
    assert abs(bbox_iou([0, 0, 100, 100], [25, 0, 100, 100]) - 0.6) < 1e-9
    print("SELFTEST OK — leaf IoU=%.3f(PASS) lesion IoU=%.3f(PASS, 漏/誤A=1) bbox 解析式✓"
          % (leaf["mean_iou"], les["mean_iou"]))
    return 0


def main():
    ap = argparse.ArgumentParser(description="標註者 IoU 一致性（COCO 對 COCO）")
    ap.add_argument("--coco-a", help="標註者 A 的 COCO JSON")
    ap.add_argument("--coco-b", help="標註者 B 的 COCO JSON")
    ap.add_argument("--labels", default=DEFAULT_LABELS)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if not (args.coco_a and args.coco_b):
        ap.error("需要 --coco-a 與 --coco-b，或 --selftest")

    lt = load_label_types(args.labels)
    with open(args.coco_a, encoding="utf-8-sig") as f:  # 容忍 BOM
        A = json.load(f)
    with open(args.coco_b, encoding="utf-8-sig") as f:
        B = json.load(f)
    sys.exit(report(compare(A, B, lt)))


if __name__ == "__main__":
    main()
