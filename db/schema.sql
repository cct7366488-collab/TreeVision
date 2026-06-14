-- TreeVision DB Schema（核心試驗骨架，v0.2）
-- 對齊 docs/data-schema.md 與 schemas/*.schema.json（四層架構之林地實體 + 試驗設計層核心 6 表）。
--
-- 可攜式 DDL：使用 TEXT / DOUBLE PRECISION / INTEGER / BOOLEAN / DATE + CHECK 約束，
-- 同時相容 PostgreSQL（生產）與 SQLite（本機開發/測試，型別親和性自動套用）。
-- 故意不使用 PG 原生 ENUM（改 CHECK ... IN），以維持單一 DDL 來源。
--
-- 載入順序（FK 相依）：treatment → site → plot → campaign → tree → tree_measurement
-- 影像/模型層、觀測層、試驗對照層俟有資料再補（見 docs/data-schema.md）。

-- ── 試驗設計層 ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS treatment (
    treatment_id  TEXT PRIMARY KEY
                  CHECK (treatment_id IN ('C0','P1','F150','P1F150')),
    label_zh      TEXT NOT NULL,
    pruning       INTEGER NOT NULL CHECK (pruning IN (0,1)),
    fertilizer_g  INTEGER NOT NULL CHECK (fertilizer_g IN (0,150)),
    note          TEXT
);

-- ── 林地實體層 ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS site (
    site_id          TEXT PRIMARY KEY,
    site_code_short  TEXT,
    plot_type        TEXT CHECK (plot_type IN ('永久樣區','臨時樣區')),
    name             TEXT NOT NULL,
    owner            TEXT NOT NULL,
    region           TEXT,
    township         TEXT,
    forest_district  TEXT,
    compartment      TEXT,
    sub_lot_no       TEXT,
    gps_datum        TEXT CHECK (gps_datum IN ('WGS84','TWD97')),
    centroid_lat     DOUBLE PRECISION,
    centroid_lon     DOUBLE PRECISION,
    area_ha          DOUBLE PRECISION,
    age_stage        TEXT,
    age_class        TEXT CHECK (age_class IN ('mature','juvenile')),
    planted_date     TEXT
);

CREATE TABLE IF NOT EXISTS plot (
    plot_id       TEXT PRIMARY KEY,
    site_id       TEXT NOT NULL REFERENCES site(site_id),
    treatment_id  TEXT NOT NULL REFERENCES treatment(treatment_id),
    tree_count    INTEGER
);

CREATE TABLE IF NOT EXISTS campaign (
    campaign_id    TEXT PRIMARY KEY,
    site_id        TEXT NOT NULL REFERENCES site(site_id),
    season         TEXT NOT NULL,
    date_estimated DATE,
    operator       TEXT
);

CREATE TABLE IF NOT EXISTS tree (
    tree_id       TEXT PRIMARY KEY,
    site_id       TEXT NOT NULL REFERENCES site(site_id),
    plot_id       TEXT NOT NULL REFERENCES plot(plot_id),
    treatment_id  TEXT NOT NULL REFERENCES treatment(treatment_id),
    tree_no       INTEGER NOT NULL CHECK (tree_no >= 1),
    species_zh    TEXT NOT NULL,
    species_sci   TEXT,
    is_multistem  BOOLEAN,
    stem_count    INTEGER,
    status        TEXT CHECK (status IN ('存活','枯立','倒伏','缺測','死亡'))
);

CREATE TABLE IF NOT EXISTS tree_measurement (
    tree_id          TEXT NOT NULL REFERENCES tree(tree_id),
    campaign_id      TEXT REFERENCES campaign(campaign_id),
    season           TEXT NOT NULL,
    measure_date     DATE,
    stem_seq         INTEGER NOT NULL DEFAULT 1,
    measure_part     TEXT CHECK (measure_part IN ('胸徑','地徑')),
    dbh_cm           DOUBLE PRECISION,
    height_m         DOUBLE PRECISION,
    crown_w1_m       DOUBLE PRECISION,
    crown_w2_m       DOUBLE PRECISION,
    volume_m3        DOUBLE PRECISION,
    growth_increment DOUBLE PRECISION,
    status           TEXT CHECK (status IN ('存活','枯立','倒伏','缺測','死亡')),
    measured_by      TEXT,
    PRIMARY KEY (tree_id, season, stem_seq)
);

-- ── 影像層（入庫管線）──────────────────────────────────────
-- 接收現場影像的第一站：metadata 驗證 + FK 比對 + 品質檢查後入此表。
-- station_id 暫不設 FK（fixed_camera_station 俟攝點建置後才有資料）。
CREATE TABLE IF NOT EXISTS image (
    image_id         TEXT PRIMARY KEY,
    tree_id          TEXT NOT NULL REFERENCES tree(tree_id),
    plot_id          TEXT REFERENCES plot(plot_id),
    treatment_id     TEXT REFERENCES treatment(treatment_id),
    campaign_id      TEXT REFERENCES campaign(campaign_id),
    station_id       TEXT,
    capture_type     TEXT CHECK (capture_type IN ('canopy','leaf_closeup','whole_plant','scale_ref')),
    capture_datetime TEXT,
    view             TEXT,
    device_id        TEXT,
    storage_uri      TEXT,
    width_px         INTEGER,
    height_px        INTEGER,
    file_size_bytes  INTEGER,
    sha256           TEXT,
    brightness_mean  DOUBLE PRECISION,
    blur_var         DOUBLE PRECISION,
    quality_pass     BOOLEAN,
    quality_issues   TEXT,
    ingested_at      TEXT
);

-- ── 標註層（標註集匯入：CVAT COCO / labelme → DB）──────────────
-- 影像標註的落點。annotation_set 記錄每次匯入批次；annotation 存單一標註幾何。
-- category 對齊 annotations/cvat-labels.json 之 17 個 label 名稱（CVAT 匯出即用此名）。
-- annotation.image_id 參照 image 表；尚無影像入庫時，import_coco.py --skip-image-fk
-- 可先匯入並回報「孤兒標註」（image_id 不在 image 表者），待影像就緒再對齊。
CREATE TABLE IF NOT EXISTS annotation_set (
    set_id            TEXT PRIMARY KEY,
    source_file       TEXT,
    source_format     TEXT CHECK (source_format IN ('coco','labelme')),
    annotator         TEXT,
    image_count       INTEGER,
    annotation_count  INTEGER,
    imported_at       TEXT,
    note              TEXT
);

CREATE TABLE IF NOT EXISTS annotation (
    annotation_id  TEXT PRIMARY KEY,
    set_id         TEXT NOT NULL REFERENCES annotation_set(set_id),
    image_id       TEXT NOT NULL REFERENCES image(image_id),
    category       TEXT NOT NULL CHECK (category IN (
                       'leaf','scale_object','lesion','chlorosis','necrosis','hole',
                       'canopy_other','veg_green','veg_yellow','veg_brown',
                       'plant_whole','plant_canopy','plant_trunk',
                       'kp_height_top','kp_height_bottom','kp_crown_top','kp_crown_bottom')),
    geom_type      TEXT CHECK (geom_type IN ('polygon','rectangle','points')),
    bbox           TEXT,             -- JSON [x,y,w,h]
    segmentation   TEXT,             -- JSON（polygon 點串）
    keypoints      TEXT,             -- JSON（points 類）
    area           DOUBLE PRECISION,
    attributes     TEXT,             -- JSON（leaf_age / scale_type / compound_leaf_id / is_uncertain…）
    is_crowd       INTEGER CHECK (is_crowd IN (0,1))
);

-- ── 索引 ────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_tree_plot        ON tree(plot_id);
CREATE INDEX IF NOT EXISTS idx_tree_treatment   ON tree(treatment_id);
CREATE INDEX IF NOT EXISTS idx_meas_season      ON tree_measurement(season);
CREATE INDEX IF NOT EXISTS idx_meas_campaign    ON tree_measurement(campaign_id);
CREATE INDEX IF NOT EXISTS idx_image_tree       ON image(tree_id);
CREATE INDEX IF NOT EXISTS idx_image_campaign    ON image(campaign_id);
CREATE INDEX IF NOT EXISTS idx_image_station     ON image(station_id);
CREATE INDEX IF NOT EXISTS idx_anno_image        ON annotation(image_id);
CREATE INDEX IF NOT EXISTS idx_anno_category     ON annotation(category);
CREATE INDEX IF NOT EXISTS idx_anno_set          ON annotation(set_id);
