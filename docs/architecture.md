# 系統架構

| 版本 | v0.1 |

---

## 壹、邏輯架構

```
┌──────────────────────────────────────────────────────────┐
│                       使用者層                            │
│  Web Browser（Next.js SPA）            行動瀏覽器          │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTPS / JSON
┌────────────────────┴─────────────────────────────────────┐
│                 邊界 / 反向代理                            │
│  Cloud Load Balancer / Nginx                              │
│  - TLS 終止                                                │
│  - Rate limit                                              │
│  - WAF（基本）                                             │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────┴─────────────────────────────────────┐
│                 應用層                                     │
│ ┌────────────────┐  ┌──────────────────┐                  │
│ │ Frontend       │  │ Backend API       │                  │
│ │ Next.js        │  │ FastAPI (Python)  │                  │
│ │ - SSR / SSG    │  │ - Auth / RBAC     │                  │
│ │ - Tailwind     │  │ - Upload          │                  │
│ │ - Recharts     │  │ - CRUD            │                  │
│ │                │  │ - Job dispatcher  │                  │
│ └────────────────┘  └────────┬─────────┘                  │
└──────────────────────────────┼────────────────────────────┘
                               │
       ┌───────────────────────┼─────────────────────┐
       │                       │                     │
┌──────┴──────┐       ┌────────┴────────┐    ┌──────┴───────┐
│ PostgreSQL  │       │ Object Storage  │    │ Redis +      │
│ + PostGIS   │       │ GCS / S3        │    │ Celery queue │
│             │       │ - raw           │    │              │
│ - metadata  │       │ - processed     │    └──────┬───────┘
│ - metrics   │       │ - masks         │           │
│ - users     │       │ - reports       │           │
└─────────────┘       └─────────────────┘           │
                                                    │
                                            ┌───────┴────────┐
                                            │ Inference      │
                                            │ Worker (GPU)   │
                                            │ PyTorch / ONNX │
                                            └────────────────┘
```

## 貳、模組責任

| 模組 | 責任 | 技術 |
|------|------|------|
| Frontend | UI、表單驗證、圖表、報表預覽 | Next.js 14 + Tailwind + shadcn/ui + Recharts |
| Backend API | 認證、CRUD、上傳、佇列派工 | FastAPI + SQLAlchemy + Alembic |
| Job Queue | 推論任務排程 | Celery + Redis |
| Inference Worker | 跑 CanopySeg / LeafInst / LeafDefect | PyTorch / ONNX Runtime |
| DB | metadata 與指標 | PostgreSQL 16 + PostGIS |
| Object Storage | 影像、mask、報表檔 | GCS（建議） |
| Auth | JWT 簽發、refresh | FastAPI 自實作或 Firebase Auth |

## 參、資料流

### 一、上傳流程

```
Browser ──multipart──► API
       ◄──signed URL── (or 直接收檔)
       ──direct put──► GCS                ┐
       ──ack──► API                       │
       API ──insert image row──► PostgreSQL
       API ──enqueue──► Redis (Celery)
       Worker ──pull job──► Redis
       Worker ──read image──► GCS
       Worker ──run model──► (in-memory)
       Worker ──write mask──► GCS
       Worker ──insert run + metrics──► PostgreSQL
       Worker ──notify──► (optional WS / push)
       Browser ──poll / WS──► API
```

### 二、報表生成

```
Client ──POST /reports──► API
                         ──enqueue──► Redis
Worker ──query metrics──► PostgreSQL
       ──fetch overlays──► GCS
       ──render──► WeasyPrint / ReportLab
       ──upload──► GCS
       ──update report row──► PostgreSQL
Client ──GET /reports/{id}──► API ──signed URL──► download
```

## 肆、部署拓撲（建議）

### 一、開發環境

- 全部在開發者本機（Docker Compose）
- DB / Redis / Storage 都用 container

### 二、staging

| 服務 | 部署 |
|------|------|
| Frontend | Vercel preview |
| Backend API | Cloud Run（min 0、max 2） |
| Worker | Cloud Run job（觸發式）或 GCE 小機 |
| DB | Cloud SQL PostgreSQL（小規格） |
| Redis | Memorystore basic |
| Storage | GCS（一個 bucket） |

### 三、production

| 服務 | 部署 | 規格建議 |
|------|------|----------|
| Frontend | Vercel | Pro |
| Backend API | Cloud Run | min 1、max 10、CPU 2、RAM 4G |
| Worker | GCE GPU（T4 / L4）或 Cloud Run GPU | 推論用 |
| DB | Cloud SQL PostgreSQL | 2 vCPU、8 G、HA |
| Redis | Memorystore | standard |
| Storage | GCS | 標準儲存 + lifecycle 移轉 |
| Monitoring | Cloud Monitoring + Sentry | |

## 伍、可觀察性（Observability）

| 面向 | 工具 |
|------|------|
| Logs | Cloud Logging（結構化 JSON）、本地 stdout |
| Metrics | Cloud Monitoring、Prometheus（自架） |
| Traces | OpenTelemetry → Cloud Trace |
| Errors | Sentry |
| Uptime | UptimeRobot / Cloud Monitoring |

## 陸、安全控制

- 全程 HTTPS，HSTS 開啟
- API JWT，refresh token 旋轉
- DB 連線使用 IAM / 限定 IP
- 影像 URL 一律簽名（短 TTL）
- 機密用 Secret Manager
- 依賴掃描（Dependabot、`pip-audit`）

## 柒、備份與災難恢復

| 項目 | 頻率 | 保留 | RPO | RTO |
|------|------|------|-----|-----|
| DB 自動備份 | 每日 | 30 天 | 24h | 4h |
| Storage 物件版本 | 啟用 | 90 天 | 即時 | 1h |
| 模型檔 | 每次升級 | 永久 | — | — |
| 程式碼 | 每次 commit | GitHub 永久 | — | — |
