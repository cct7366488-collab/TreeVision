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

-- ── 索引 ────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_tree_plot        ON tree(plot_id);
CREATE INDEX IF NOT EXISTS idx_tree_treatment   ON tree(treatment_id);
CREATE INDEX IF NOT EXISTS idx_meas_season      ON tree_measurement(season);
CREATE INDEX IF NOT EXISTS idx_meas_campaign    ON tree_measurement(campaign_id);
