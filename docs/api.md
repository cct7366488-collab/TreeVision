# REST API 規格

| 版本 | v0.1 |
|------|------|
| Base URL（dev） | `http://localhost:8000/api/v1` |
| Base URL（prod） | `https://api.treevision.<your-domain>/api/v1` |

---

## 壹、通用約定

### 一、認證

所有端點除 `/auth/login` 外都須帶：

```
Authorization: Bearer <jwt_token>
```

### 二、回應格式

成功：

```json
{ "data": {...}, "meta": {...} }
```

失敗：

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "tree_id 不存在",
    "details": {"field": "tree_id"}
  }
}
```

### 三、HTTP 狀態碼

| 範圍 | 用途 |
|------|------|
| 2xx | 成功 |
| 400 | 請求格式錯誤 |
| 401 | 未認證 |
| 403 | 無權限 |
| 404 | 資源不存在 |
| 409 | 資源衝突（重複） |
| 422 | 驗證失敗 |
| 5xx | 伺服器錯誤 |

### 四、分頁

```
GET /resource?page=1&page_size=20&sort=-created_at
```

回應 `meta`：

```json
{ "page": 1, "page_size": 20, "total": 137, "total_pages": 7 }
```

---

## 貳、影像（Image）

### POST `/images`

上傳影像 + metadata。

**Request**：`multipart/form-data`

| 欄位 | 型別 | 必填 |
|------|------|------|
| `file` | File | ✓ |
| `tree_id` | string | ✓ |
| `site_id` | string | ✓ |
| `capture_type` | enum | ✓ |
| `capture_datetime` | ISO8601 | ✓ |
| `view` | enum | ✓ |
| `device_id` | string | ✓ |
| `scale_object_type` | enum | ◎ |
| `scale_object_size_mm` | number | ◎ |
| `has_color_card` | bool | ◎ |
| `weather` | enum | ○ |
| `note` | string | ○ |

**Response 201**：

```json
{
  "data": {
    "image_id": "img_01HXX...",
    "storage_uri": "gs://treevision/raw/...",
    "width_px": 4032,
    "height_px": 3024,
    "sha256": "...",
    "quality_pass": true,
    "next_action": "/images/img_01HXX/analyze"
  }
}
```

### GET `/images/{image_id}`

取得單張影像 metadata + 最新分析結果。

### POST `/images/{image_id}/analyze`

觸發推論（非同步）。

**Body**：

```json
{
  "models": ["canopy_seg"]   // 或 ["leaf_inst", "leaf_defect"]
}
```

**Response 202**：

```json
{
  "data": {
    "run_ids": ["run_01HXX..."]
  }
}
```

### GET `/images?tree_id=...&from=...&to=...`

列表查詢。

---

## 參、推論執行（Run）

### GET `/runs/{run_id}`

```json
{
  "data": {
    "run_id": "run_01HXX...",
    "image_id": "img_...",
    "model_id": "CanopySeg",
    "model_version": "v0.1.0",
    "status": "succeeded",
    "started_at": "2026-05-01T14:32:01Z",
    "finished_at": "2026-05-01T14:32:18Z",
    "metrics": {
      "canopy_ratio": 0.62,
      "green_ratio": 0.81,
      "yellow_ratio": 0.12,
      "brown_ratio": 0.07
    },
    "mask_uri": "gs://.../canopy/masks/canopy/..."
  }
}
```

---

## 肆、樹木（Tree）

### GET `/trees/{tree_id}`

```json
{
  "data": {
    "tree_id": "T0123",
    "site_id": "NTU01",
    "species_zh": "台灣杉",
    "lat": null, "lon": null,    // 已遮罩
    "dbh_cm": 32.5,
    "height_m": 18.2,
    "crown_status": "stressed",
    "image_counts": {"canopy": 12, "leaf_closeup": 24},
    "latest_summary_date": "2026-04-29"
  }
}
```

### GET `/trees/{tree_id}/timeline?metric=health_score_mean`

```json
{
  "data": [
    {"date": "2026-01-15", "value": 92.1},
    {"date": "2026-02-12", "value": 88.5},
    ...
  ]
}
```

### GET `/trees/{tree_id}/summary?date=2026-04-29`

對應 `tree_daily_summary` 一筆。

---

## 伍、場域（Site）

### GET `/sites/{site_id}/dashboard`

```json
{
  "data": {
    "site_id": "NTU01",
    "as_of": "2026-04-29",
    "tree_count": 47,
    "tree_count_high_risk": 6,
    "site_health_grade_distribution": {
      "A": 0.45, "B": 0.28, "C": 0.15, "D": 0.08, "E": 0.04
    },
    "metrics_30d_trend": {
      "green_ratio_mean": [...],
      "yellow_ratio_mean": [...]
    },
    "high_risk_trees": [
      {"tree_id": "T0007", "health_score_mean": 41.2, "main_issue": "necrosis"}
    ]
  }
}
```

---

## 陸、報表（Reports）

### POST `/reports`

```json
{
  "type": "tree",
  "tree_id": "T0123",
  "date_from": "2026-01-01",
  "date_to": "2026-04-29",
  "format": "pdf"
}
```

**Response 202**：

```json
{ "data": { "report_id": "rpt_...", "status_url": "/reports/rpt_..." } }
```

### GET `/reports/{report_id}`

回傳狀態與下載連結（簽名 URL）。

---

## 柒、認證

### POST `/auth/login`

```json
{ "email": "...", "password": "..." }
```

**Response 200**：

```json
{ "data": { "access_token": "...", "refresh_token": "...", "expires_in": 86400 } }
```

### POST `/auth/refresh`

### POST `/auth/logout`

---

## 捌、Rate limit

- 一般：120 req/min/user
- 上傳：30 req/min/user
- 推論觸發：10 req/min/user

超過回 `429 Too Many Requests` + `Retry-After` header。
