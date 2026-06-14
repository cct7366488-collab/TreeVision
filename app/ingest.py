# -*- coding: utf-8 -*-
"""影像入庫管線：現場影像進系統的第一站。

流程：metadata schema 驗證 → DB 參照（tree/campaign）比對 → 影像品質檢查
（解析度／模糊／曝光）→ 計算雜湊與尺寸 → 寫入 image 表。

決策：
- metadata 或 FK 錯誤 → **拒收**（無法正確歸檔）。
- 品質問題（模糊/過暗/過曝/低解析）→ **仍入庫但標記 quality_pass=False**，列入待補拍。
"""
import hashlib
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage
from jsonschema import Draft202012Validator

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_schema = json.load(open(os.path.join(REPO, "schemas", "image_metadata.schema.json"), encoding="utf-8"))
_validator = Draft202012Validator(_schema)

# 品質門檻（可調）
MIN_LONG_EDGE = 1000      # px；長邊小於此 → low_res
BLUR_MIN = 100.0          # Laplacian 變異數低於此 → blurry
DARK_MAX = 40.0           # 平均亮度低於此 → dark
BRIGHT_MAX = 220.0        # 平均亮度高於此 → overexposed


def validate_metadata(meta):
    """回傳 schema 違規訊息清單（空＝通過）。"""
    clean = {k: v for k, v in meta.items() if v not in (None, "")}
    return [e.message for e in _validator.iter_errors(clean)]


def check_references(meta, con):
    """比對 DB：tree_id 必存在；campaign_id（若有）須存在。回傳問題清單。"""
    issues = []
    if not con.execute("SELECT 1 FROM tree WHERE tree_id=?", (meta.get("tree_id"),)).fetchone():
        issues.append("tree_id 不存在於 DB: {}".format(meta.get("tree_id")))
    cid = meta.get("campaign_id")
    if cid and not con.execute("SELECT 1 FROM campaign WHERE campaign_id=?", (cid,)).fetchone():
        issues.append("campaign_id 不存在於 DB: {}".format(cid))
    return issues


def quality_check(path):
    """解析度／模糊／曝光檢查。回傳量測值與 quality_issues/quality_pass。"""
    im = Image.open(path)
    im.load()
    w, h = im.size
    g = np.asarray(im.convert("L"), dtype=float)
    brightness = float(g.mean())
    blur_var = float(ndimage.laplace(g).var())
    issues = []
    if max(w, h) < MIN_LONG_EDGE:
        issues.append("low_res")
    if blur_var < BLUR_MIN:
        issues.append("blurry")
    if brightness < DARK_MAX:
        issues.append("dark")
    if brightness > BRIGHT_MAX:
        issues.append("overexposed")
    return dict(width_px=w, height_px=h, brightness_mean=round(brightness, 1),
                blur_var=round(blur_var, 1), quality_issues=issues,
                quality_pass=(len(issues) == 0))


def file_info(path):
    data = open(path, "rb").read()
    return dict(sha256=hashlib.sha256(data).hexdigest(), file_size_bytes=len(data))


def ingest(path, meta, con, storage_uri=None, ingested_at=None):
    """單張影像入庫。回傳 dict(accepted, image_id, quality_pass, reasons, quality_issues)。"""
    res = {"image_id": meta.get("image_id"), "accepted": False, "reasons": [], "quality_issues": []}

    me = validate_metadata(meta)
    if me:
        res["reasons"] += ["metadata: " + m for m in me]
        return res
    fe = check_references(meta, con)
    if fe:
        res["reasons"] += fe
        return res
    if not os.path.exists(path):
        res["reasons"].append("影像檔不存在: {}".format(path))
        return res

    q = quality_check(path)
    fi = file_info(path)
    image_id = meta.get("image_id") or "img_" + fi["sha256"][:12]

    rec = dict(
        image_id=image_id, tree_id=meta["tree_id"], plot_id=meta.get("plot_id"),
        treatment_id=meta.get("treatment_id"), campaign_id=meta.get("campaign_id"),
        station_id=meta.get("station_id"), capture_type=meta.get("capture_type"),
        capture_datetime=meta.get("capture_datetime"), view=meta.get("view"),
        device_id=meta.get("device_id"), storage_uri=storage_uri or path,
        width_px=q["width_px"], height_px=q["height_px"], file_size_bytes=fi["file_size_bytes"],
        sha256=fi["sha256"], brightness_mean=q["brightness_mean"], blur_var=q["blur_var"],
        quality_pass=1 if q["quality_pass"] else 0,
        quality_issues=",".join(q["quality_issues"]), ingested_at=ingested_at,
    )
    cols = list(rec.keys())
    con.execute("INSERT OR REPLACE INTO image ({}) VALUES ({})".format(
        ",".join(cols), ",".join("?" * len(cols))), [rec[c] for c in cols])

    res.update(accepted=True, image_id=image_id, quality_pass=q["quality_pass"],
               quality_issues=q["quality_issues"])
    return res
