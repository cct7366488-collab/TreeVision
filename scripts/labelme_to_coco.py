# -*- coding: utf-8 -*-
"""
labelme → COCO 1.0 轉換器（備援格式）。

主標註管線走 CVAT → COCO（import_coco.py）。少數情況以 labelme 標（每影像一個
JSON）時，用本工具把整個資料夾的 labelme JSON 合併成單一 COCO 1.0 JSON，再交給
import_coco.py 入庫。

對應：annotations/README.md「備援可接受 labelme JSON …透過 scripts/labelme_to_coco.py 轉換」。

對照與防呆：
  - label 名稱一律對照 annotations/cvat-labels.json；出現未知 label 即報錯（除非
    --skip-unknown）。輸出的 categories 採 cvat-labels.json 全量（id 穩定），與
    import_coco.py 的類別驗證一致。
  - shape_type 對應：polygon→segmentation+bbox+area；rectangle（兩角點）→bbox；
    point→keypoints。其餘（line/linestrip/circle）非本案類別，略過並回報。

用法：
    python scripts/labelme_to_coco.py --labelme-dir annotations/_labelme --out out.json
    python scripts/labelme_to_coco.py --selftest
"""
import argparse
import glob
import json
import os
import sys

try:  # cp950 主控台安全輸出
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEFAULT_LABELS = os.path.join(REPO, "annotations", "cvat-labels.json")


def load_labels(path):
    with open(path, encoding="utf-8") as f:
        return [l["name"] for l in json.load(f)]


def _poly_area(pts):
    s = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]


def shape_to_ann(shape):
    """labelme shape → (coco_fields dict) 或 None（不支援的 shape_type）。"""
    st = shape.get("shape_type")
    pts = shape.get("points", [])
    if st == "polygon" and len(pts) >= 3:
        bb = _bbox(pts)
        flat = [c for p in pts for c in p]
        return {"segmentation": [flat], "bbox": bb, "area": _poly_area(pts), "keypoints": None}
    if st == "rectangle" and len(pts) == 2:
        (x1, y1), (x2, y2) = pts
        x, y, w, h = min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)
        seg = [[x, y, x + w, y, x + w, y + h, x, y + h]]
        return {"segmentation": seg, "bbox": [x, y, w, h], "area": w * h, "keypoints": None}
    if st in ("point", "points") and len(pts) >= 1:
        x, y = pts[0]
        return {"segmentation": [], "bbox": [x, y, 0, 0], "area": 0.0, "keypoints": [x, y, 2]}
    return None


def convert(labelme_docs, label_names, skip_unknown=False):
    """labelme_docs: [(filename, doc_dict)] → (coco, errors, warnings)。"""
    cat_id = {name: i + 1 for i, name in enumerate(label_names)}
    categories = [{"id": i + 1, "name": name} for i, name in enumerate(label_names)]
    images, annotations, errors, warnings = [], [], [], []
    unknown = set()
    img_id = ann_id = 0

    for fname, doc in labelme_docs:
        img_id += 1
        file_name = os.path.basename(doc.get("imagePath") or fname)
        images.append({
            "id": img_id, "file_name": file_name,
            "width": doc.get("imageWidth"), "height": doc.get("imageHeight"),
        })
        for sh in doc.get("shapes", []):
            label = sh.get("label")
            if label not in cat_id:
                unknown.add(label)
                continue
            fields = shape_to_ann(sh)
            if fields is None:
                warnings.append("{}：略過不支援 shape_type={} (label={})".format(
                    file_name, sh.get("shape_type"), label))
                continue
            ann_id += 1
            ann = {"id": ann_id, "image_id": img_id, "category_id": cat_id[label],
                   "iscrowd": 0}
            ann.update({k: v for k, v in fields.items() if v is not None})
            flags = sh.get("flags") or {}
            if flags:
                ann["attributes"] = flags
            annotations.append(ann)

    if unknown and not skip_unknown:
        errors.append("未知 label（不在 cvat-labels.json）：{}".format(
            ", ".join(sorted(str(u) for u in unknown))))
    elif unknown:
        warnings.append("已略過未知 label：{}".format(", ".join(sorted(str(u) for u in unknown))))

    coco = {"images": images, "categories": categories, "annotations": annotations}
    return coco, errors, warnings


def read_dir(d):
    docs = []
    for p in sorted(glob.glob(os.path.join(d, "*.json"))):
        with open(p, encoding="utf-8-sig") as f:  # 容忍 BOM（Windows 編輯器常見）
            docs.append((os.path.basename(p), json.load(f)))
    return docs


# ── 自測 ─────────────────────────────────────────────────────
def selftest():
    labels = load_labels(DEFAULT_LABELS)
    docs = [
        ("a.json", {
            "imagePath": "115121-C0-001_leaf_closeup_001.jpg", "imageWidth": 4000, "imageHeight": 3000,
            "shapes": [
                {"label": "leaf", "shape_type": "polygon",
                 "points": [[0, 0], [100, 0], [100, 100], [0, 100]], "flags": {}},
                {"label": "scale_object", "shape_type": "rectangle",
                 "points": [[200, 200], [500, 600]], "flags": {}},
                {"label": "lesion", "shape_type": "polygon",
                 "points": [[10, 10], [40, 10], [40, 40], [10, 40]], "flags": {}},
            ]}),
        ("b.json", {
            "imagePath": "115121-C0-002_canopy_north_001.jpg", "imageWidth": 4000, "imageHeight": 3000,
            "shapes": [
                {"label": "veg_green", "shape_type": "polygon",
                 "points": [[0, 0], [50, 0], [50, 50], [0, 50]], "flags": {}},
                {"label": "kp_height_top", "shape_type": "point", "points": [[123, 45]], "flags": {}},
            ]}),
    ]
    coco, errors, warnings = convert(docs, labels)
    assert not errors, errors
    assert len(coco["images"]) == 2, coco["images"]
    assert len(coco["annotations"]) == 5, len(coco["annotations"])
    assert len(coco["categories"]) == len(labels) == 17, len(coco["categories"])

    by = {a["id"]: a for a in coco["annotations"]}
    # polygon leaf：bbox + area + segmentation
    leaf = by[1]
    assert leaf["bbox"] == [0, 0, 100, 100] and leaf["area"] == 10000.0 and leaf["segmentation"], leaf
    # rectangle scale_object：兩角點 → bbox 300×400
    rect = by[2]
    assert rect["bbox"] == [200, 200, 300, 400] and rect["area"] == 120000.0, rect
    # point kp：keypoints
    kp = next(a for a in coco["annotations"] if a["category_id"] == labels.index("kp_height_top") + 1)
    assert kp.get("keypoints") == [123, 45, 2], kp
    # 類別名稱全部落在 cvat-labels
    names = {c["name"] for c in coco["categories"]}
    assert all(a_name in names for a_name in ["leaf", "scale_object", "lesion", "veg_green", "kp_height_top"])

    # 未知 label → 報錯
    bad, e2, _ = convert([("x.json", {"imagePath": "x.jpg", "shapes": [
        {"label": "bogus", "shape_type": "polygon", "points": [[0, 0], [1, 0], [1, 1]]}]})], labels)
    assert e2 and "未知 label" in e2[0], e2
    # --skip-unknown → 不報錯、略過
    _, e3, w3 = convert([("x.json", {"imagePath": "x.jpg", "shapes": [
        {"label": "bogus", "shape_type": "polygon", "points": [[0, 0], [1, 0], [1, 1]]}]})], labels, skip_unknown=True)
    assert not e3 and any("略過未知" in w for w in w3), (e3, w3)

    print("SELFTEST OK — 2 影像/5 標註（polygon+rectangle+point）轉換正確；未知 label 報錯✓、--skip-unknown✓")
    return 0


def main():
    ap = argparse.ArgumentParser(description="labelme JSON 資料夾 → COCO 1.0")
    ap.add_argument("--labelme-dir", help="含每影像一個 labelme JSON 的資料夾")
    ap.add_argument("--out", help="輸出 COCO JSON 路徑")
    ap.add_argument("--labels", default=DEFAULT_LABELS)
    ap.add_argument("--skip-unknown", action="store_true", help="略過未知 label（預設報錯中止）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if not (args.labelme_dir and args.out):
        ap.error("需要 --labelme-dir 與 --out，或 --selftest")

    labels = load_labels(args.labels)
    docs = read_dir(args.labelme_dir)
    if not docs:
        ap.error("資料夾無 *.json：{}".format(args.labelme_dir))
    coco, errors, warnings = convert(docs, labels, args.skip_unknown)
    for w in warnings:
        print("WARN", w)
    if errors:
        for e in errors:
            print("ERR ", e)
        sys.exit(1)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(coco, f, ensure_ascii=False, indent=2)
    print("✓ 轉換完成：{} 影像 / {} 標註 → {}".format(
        len(coco["images"]), len(coco["annotations"]), args.out))
    print("  下一步：python scripts/import_coco.py --coco {} [--skip-image-fk]".format(args.out))
    sys.exit(0)


if __name__ == "__main__":
    main()
