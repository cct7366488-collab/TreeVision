# -*- coding: utf-8 -*-
"""批次影像入庫 CLI：讀 metadata CSV + 影像資料夾，逐張入庫至 DB。

metadata CSV 欄位同 metadata/image_metadata.template.csv，另需 `filename` 欄
指向影像檔（相對 --images-dir）；若無 filename 欄則以 <image_id>.jpg 尋找。

用法：
    python scripts/ingest_images.py --metadata <meta.csv> --images-dir <dir>
"""
import argparse
import csv
import datetime
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
from app import ingest as ing  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="批次影像入庫")
    ap.add_argument("--metadata", required=True, help="image metadata CSV")
    ap.add_argument("--images-dir", required=True, help="影像資料夾")
    ap.add_argument("--db", default=os.path.join(REPO, "outputs", "treevision.db"))
    args = ap.parse_args()
    if not os.path.exists(args.db):
        ap.error("找不到 DB {}；請先跑 load_entities_to_db.py".format(args.db))

    con = sqlite3.connect(args.db)
    con.execute("PRAGMA foreign_keys = ON")
    rows = list(csv.DictReader(open(args.metadata, encoding="utf-8-sig")))
    now = datetime.datetime.now().isoformat(timespec="seconds")

    accepted = flagged = rejected = 0
    print("=== 入庫 ===")
    for r in rows:
        meta = {k: (v if v != "" else None) for k, v in r.items() if k != "filename"}
        fname = r.get("filename") or (str(meta.get("image_id") or "") + ".jpg")
        path = os.path.join(args.images_dir, fname)
        res = ing.ingest(path, meta, con, ingested_at=now)
        if not res["accepted"]:
            rejected += 1
            print("REJECT {:22s} {}".format(str(meta.get("image_id"))[:22], "; ".join(res["reasons"])[:80]))
        elif res["quality_pass"]:
            accepted += 1
            print("OK     {:22s} 入庫".format(res["image_id"][:22]))
        else:
            flagged += 1
            accepted += 1
            print("FLAG   {:22s} 入庫但待補拍：{}".format(res["image_id"][:22], ",".join(res["quality_issues"])))
    con.commit()

    total = con.execute("SELECT COUNT(*) FROM image").fetchone()[0]
    npass = con.execute("SELECT COUNT(*) FROM image WHERE quality_pass=1").fetchone()[0]
    con.close()
    print("\n本批：入庫 {}（其中待補拍 {}）、拒收 {}".format(accepted, flagged, rejected))
    print("DB image 表共 {} 張，品質合格 {}".format(total, npass))
    sys.exit(0)


if __name__ == "__main__":
    main()
