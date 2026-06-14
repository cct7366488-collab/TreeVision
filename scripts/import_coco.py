# -*- coding: utf-8 -*-
"""
標註匯入：把 CVAT 匯出的 COCO 1.0 標註 JSON 載入 TreeVision DB 的 annotation 層。

定位：銜接 docs/annotation-plan.md「建模期標註集」與 db/schema.sql 的
annotation_set / annotation 兩表。標註者在 CVAT 標完（label 設定用
annotations/cvat-labels.json）→ 匯出 COCO 1.0 → 本腳本入庫。

對照與防呆：
  - category 名稱一律對照 annotations/cvat-labels.json 之 label 集合；出現未知
    類別即報錯（避免 typo 污染訓練集）。geom_type 亦由該檔的 label.type 決定。
  - COCO image.file_name 去副檔名後＝我方 image_id；預設啟用 image FK。
  - 影像尚未入庫時用 --skip-image-fk：關閉 FK 先匯入，並回報「孤兒標註」
    （image_id 不在 image 表者），待影像就緒再核對。

匯入後印出各類別實例數，對照 annotation-plan §貳-一「各病徵 ≥ 100」目標。

用法：
    python scripts/import_coco.py --coco path/to/instances_default.json
    python scripts/import_coco.py --coco ann.json --skip-image-fk --annotator A
    python scripts/import_coco.py --selftest        # 合成資料自我驗證，不需真實檔
"""
import argparse
import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime

try:  # 確保 ✓/⚠ 等符號在 Windows cp950 主控台也能輸出
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEFAULT_LABELS = os.path.join(REPO, "annotations", "cvat-labels.json")
DEFAULT_SCHEMA = os.path.join(REPO, "db", "schema.sql")
DEFAULT_DB = os.path.join(REPO, "outputs", "treevision.db")


def load_label_types(labels_path):
    """讀 cvat-labels.json → {label_name: geom_type}。"""
    with open(labels_path, encoding="utf-8") as f:
        labels = json.load(f)
    return {l["name"]: l["type"] for l in labels}


def image_id_from_filename(file_name):
    """COCO file_name → 我方 image_id（去路徑與副檔名）。"""
    return os.path.splitext(os.path.basename(file_name))[0]


def parse_coco(coco, label_types):
    """把 COCO dict 轉成待插入的 annotation row 列表；回傳 (rows, image_ids, errors)。"""
    cat_by_id = {c["id"]: c["name"] for c in coco.get("categories", [])}
    img_by_id = {im["id"]: im for im in coco.get("images", [])}
    errors = []

    # 類別合法性：COCO 類別名須全部落在 cvat-labels 集合內
    unknown = sorted({n for n in cat_by_id.values() if n not in label_types})
    if unknown:
        errors.append("未知類別（不在 cvat-labels.json）：{}".format(", ".join(unknown)))

    image_ids = {im["id"]: image_id_from_filename(im["file_name"]) for im in coco.get("images", [])}

    rows = []
    for a in coco.get("annotations", []):
        cat = cat_by_id.get(a["category_id"])
        if cat is None:
            errors.append("annotation id={} 參照不存在的 category_id={}".format(a.get("id"), a.get("category_id")))
            continue
        if a["image_id"] not in img_by_id:
            errors.append("annotation id={} 參照不存在的 image_id={}".format(a.get("id"), a.get("image_id")))
            continue
        seg = a.get("segmentation")
        kp = a.get("keypoints")
        rows.append({
            "coco_id": a["id"],
            "image_id": image_ids[a["image_id"]],
            "category": cat,
            "geom_type": label_types.get(cat),
            "bbox": json.dumps(a["bbox"], ensure_ascii=False) if a.get("bbox") else None,
            "segmentation": json.dumps(seg, ensure_ascii=False) if seg else None,
            "keypoints": json.dumps(kp, ensure_ascii=False) if kp else None,
            "area": a.get("area"),
            "attributes": json.dumps(a["attributes"], ensure_ascii=False) if a.get("attributes") else None,
            "is_crowd": int(a.get("iscrowd", 0)),
        })
    return rows, image_ids, errors


def import_coco(con, coco, label_types, set_id, source_file, annotator, skip_image_fk, note=""):
    rows, image_ids, errors = parse_coco(coco, label_types)
    if errors:
        return {"ok": False, "errors": errors}

    con.execute("PRAGMA foreign_keys = {}".format("OFF" if skip_image_fk else "ON"))
    con.execute(
        "INSERT INTO annotation_set (set_id, source_file, source_format, annotator, "
        "image_count, annotation_count, imported_at, note) VALUES (?,?,?,?,?,?,?,?)",
        (set_id, source_file, "coco", annotator, len(image_ids), len(rows),
         datetime.now().isoformat(timespec="seconds"), note))

    ins = (
        "INSERT INTO annotation (annotation_id, set_id, image_id, category, geom_type, "
        "bbox, segmentation, keypoints, area, attributes, is_crowd) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)")
    try:
        con.executemany(ins, [
            ("{}:{}".format(set_id, r["coco_id"]), set_id, r["image_id"], r["category"],
             r["geom_type"], r["bbox"], r["segmentation"], r["keypoints"], r["area"],
             r["attributes"], r["is_crowd"]) for r in rows])
    except sqlite3.IntegrityError as e:
        con.rollback()
        return {"ok": False, "errors": ["完整性違規（image FK？改用 --skip-image-fk 先匯入）: {}".format(e)]}
    con.commit()

    # 各類別實例數（對照 plan §貳-一）
    per_cat = dict(con.execute(
        "SELECT category, COUNT(*) FROM annotation WHERE set_id=? GROUP BY category", (set_id,)).fetchall())
    # 孤兒標註：image_id 不在 image 表
    orphans = con.execute(
        "SELECT COUNT(*) FROM annotation a WHERE a.set_id=? AND NOT EXISTS "
        "(SELECT 1 FROM image i WHERE i.image_id=a.image_id)", (set_id,)).fetchone()[0]
    return {"ok": True, "rows": len(rows), "images": len(image_ids),
            "per_cat": per_cat, "orphans": orphans}


def ensure_db(db_path, schema_path, fresh=False):
    if fresh and os.path.exists(db_path):
        os.remove(db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(open(schema_path, encoding="utf-8").read())
    return con


def report(res, set_id):
    if not res["ok"]:
        print("ERR 匯入中止：")
        for e in res["errors"]:
            print("   -", e)
        return 1
    print("=== 匯入完成 set_id={} ===".format(set_id))
    print("影像數={}  標註數={}  孤兒標註（image 未入庫）={}".format(
        res["images"], res["rows"], res["orphans"]))
    print("各類別實例數（對照 annotation-plan §貳-一 病徵各 ≥100）:")
    defects = {"lesion", "chlorosis", "necrosis", "hole"}
    for cat in sorted(res["per_cat"]):
        n = res["per_cat"][cat]
        flag = ""
        if cat in defects:
            flag = "  ✓達標" if n >= 100 else "  ⚠未達100"
        print("   {:16s} {:5d}{}".format(cat, n, flag))
    return 0


SYNTH_COCO = {
    "images": [
        {"id": 1, "file_name": "115121-C0-001_leaf_closeup_20260601_1000_macro_001.jpg", "width": 4000, "height": 3000},
        {"id": 2, "file_name": "115121-C0-002_canopy_20260601_1010_north_001.jpg", "width": 4000, "height": 3000},
    ],
    "categories": [
        {"id": 1, "name": "leaf"}, {"id": 2, "name": "scale_object"}, {"id": 3, "name": "lesion"},
        {"id": 4, "name": "veg_green"}, {"id": 5, "name": "veg_yellow"},
    ],
    "annotations": [
        {"id": 1, "image_id": 1, "category_id": 1, "segmentation": [[10, 10, 100, 10, 100, 100, 10, 100]],
         "bbox": [10, 10, 90, 90], "area": 8100, "iscrowd": 0, "attributes": {"leaf_age": "mature"}},
        {"id": 2, "image_id": 1, "category_id": 3, "segmentation": [[20, 20, 40, 20, 40, 40, 20, 40]],
         "bbox": [20, 20, 20, 20], "area": 400, "iscrowd": 0},
        {"id": 3, "image_id": 1, "category_id": 2, "segmentation": [], "bbox": [200, 200, 300, 400],
         "area": 120000, "iscrowd": 0, "attributes": {"scale_type": "a4_grid"}},
        {"id": 4, "image_id": 2, "category_id": 4, "segmentation": [[0, 0, 50, 0, 50, 50, 0, 50]],
         "bbox": [0, 0, 50, 50], "area": 2500, "iscrowd": 0},
        {"id": 5, "image_id": 2, "category_id": 5, "segmentation": [[60, 60, 90, 60, 90, 90, 60, 90]],
         "bbox": [60, 60, 30, 30], "area": 900, "iscrowd": 0},
    ],
}


def selftest():
    label_types = load_label_types(DEFAULT_LABELS)
    tmp = tempfile.mkdtemp(prefix="tv_anno_")
    db = os.path.join(tmp, "t.db")
    con = ensure_db(db, DEFAULT_SCHEMA, fresh=True)

    # 1) happy path（無影像 → --skip-image-fk）
    res = import_coco(con, SYNTH_COCO, label_types, "selftest", "synthetic", "tester",
                      skip_image_fk=True, note="selftest")
    assert res["ok"], res
    assert res["rows"] == 5, res
    assert res["images"] == 2, res
    assert res["orphans"] == 5, ("孤兒應為 5（無影像入庫）", res)
    assert res["per_cat"] == {"leaf": 1, "scale_object": 1, "lesion": 1, "veg_green": 1, "veg_yellow": 1}, res
    # geom_type 由 cvat-labels 推得
    gt = dict(con.execute("SELECT category, geom_type FROM annotation").fetchall())
    assert gt["leaf"] == "polygon" and gt["scale_object"] == "rectangle", gt
    # attributes 保留
    a1 = con.execute("SELECT attributes FROM annotation WHERE annotation_id='selftest:1'").fetchone()[0]
    assert json.loads(a1)["leaf_age"] == "mature", a1
    con.close()

    # 2) 未知類別 → 報錯中止
    con2 = ensure_db(os.path.join(tmp, "t2.db"), DEFAULT_SCHEMA, fresh=True)
    bad = {"images": [{"id": 1, "file_name": "x.jpg"}],
           "categories": [{"id": 1, "name": "bogus_label"}],
           "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [0, 0, 1, 1], "area": 1}]}
    res2 = import_coco(con2, bad, label_types, "bad", "bad", None, skip_image_fk=True)
    assert not res2["ok"] and any("未知類別" in e for e in res2["errors"]), res2
    con2.close()

    # 3) image FK 生效：補影像鏈後預設 FK 應通過、孤兒=0
    con3 = ensure_db(os.path.join(tmp, "t3.db"), DEFAULT_SCHEMA, fresh=True)
    con3.execute("PRAGMA foreign_keys=ON")
    con3.execute("INSERT INTO treatment VALUES ('C0','對照',0,0,NULL)")
    con3.execute("INSERT INTO site (site_id,name,owner) VALUES ('115-12-1','大雪山','合作社')")
    con3.execute("INSERT INTO plot VALUES ('115121-C0','115-12-1','C0',30)")
    con3.execute("INSERT INTO campaign (campaign_id,site_id,season) VALUES ('115121-115Q2','115-12-1','115Q2')")
    for tno, iid in ((1, SYNTH_COCO["images"][0]["file_name"]), (2, SYNTH_COCO["images"][1]["file_name"])):
        tid = "115121-C0-00{}".format(tno)
        con3.execute("INSERT INTO tree (tree_id,site_id,plot_id,treatment_id,tree_no,species_zh) "
                     "VALUES (?,?,?,?,?,?)", (tid, "115-12-1", "115121-C0", "C0", tno, "土肉桂"))
        con3.execute("INSERT INTO image (image_id,tree_id) VALUES (?,?)",
                     (image_id_from_filename(iid), tid))
    con3.commit()
    res3 = import_coco(con3, SYNTH_COCO, label_types, "withimg", "synthetic", None, skip_image_fk=False)
    assert res3["ok"] and res3["orphans"] == 0, res3
    con3.close()

    print("SELFTEST OK — 3 情境通過（happy/未知類別/image FK）")
    return 0


def main():
    ap = argparse.ArgumentParser(description="匯入 CVAT COCO 標註至 TreeVision DB")
    ap.add_argument("--coco", help="COCO 1.0 JSON 路徑")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    ap.add_argument("--labels", default=DEFAULT_LABELS)
    ap.add_argument("--set-id", help="標註集 ID（預設＝COCO 檔名 stem + 時間）")
    ap.add_argument("--annotator", default=None)
    ap.add_argument("--skip-image-fk", action="store_true",
                    help="影像尚未入庫時：關閉 image FK，匯入後回報孤兒標註")
    ap.add_argument("--note", default="")
    ap.add_argument("--selftest", action="store_true", help="合成資料自我驗證")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if not args.coco:
        ap.error("需要 --coco 或 --selftest")

    label_types = load_label_types(args.labels)
    with open(args.coco, encoding="utf-8-sig") as f:  # 容忍 BOM
        coco = json.load(f)
    set_id = args.set_id or (os.path.splitext(os.path.basename(args.coco))[0]
                             + "_" + datetime.now().strftime("%Y%m%d%H%M"))
    con = ensure_db(args.db, args.schema, fresh=False)
    res = import_coco(con, coco, label_types, set_id, os.path.basename(args.coco),
                      args.annotator, args.skip_image_fk, args.note)
    con.close()
    sys.exit(report(res, set_id))


if __name__ == "__main__":
    main()
