# Mini DWH E-commerce

A mini Data Warehouse for Amazon product & review data, with an ETL pipeline, a FastAPI backend, and a React dashboard.

## Architecture

```
amazon.csv ──► [ETL container] ──► PostgreSQL (DWH) ──► FastAPI ──► React Dashboard
```

- **PostgreSQL 15** — stores `dwh.dim_product`, `dwh.dim_reviewer`, `dwh.fact_reviews`
- **ETL** (`etl/main.py`) — reads `amazon.csv`, cleans it, upserts into the DWH
- **API** (`etl/api.py`) — FastAPI exposing `/api/*` endpoints
- **Frontend** — React + Vite + Recharts dashboard

## Quick start

```bash
docker compose up
```

Then open the dashboard at http://localhost:5173 and the API docs at http://localhost:8000/docs.

## Project structure

```
.
├── docker-compose.yml
├── amazon.csv              # source data
├── sql/
│   └── init.sql            # schema (dimensions + facts)
├── etl/
│   ├── main.py             # ETL pipeline
│   ├── api.py              # FastAPI backend
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/               # React + Vite app
```

## Data model

| Table | Type | Description |
|-------|------|-------------|
| `dwh.dim_product` | Dimension | Product info (price, rating, category) |
| `dwh.dim_reviewer` | Dimension | Reviewer info |
| `dwh.fact_reviews` | Fact | Reviews linking products to reviewers |

## API endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/kpi-summary` | Total products, avg rating, avg discount, total reviews |
| `GET /api/top-categories` | Top 10 categories by product count |
| `GET /api/top-rated-products` | Top 10 rated products (≥ 500 ratings) |
| `GET /api/most-reviewed` | Top 10 most-reviewed products |
| `GET /api/discount-distribution` | Discount bucket distribution |

## TODO — Improvements

### Data quality & ETL
- [ ] Add data validation (reject rows with missing required fields)
- [ ] Handle `review_content` containing commas properly (current split-by-comma approach can corrupt content)
- [ ] Add incremental loads instead of full reloads
- [ ] Add logging + error reporting (currently only prints to stdout)
- [ ] Add unit tests for cleaning functions (`clean_price`, `clean_pct`, etc.)

### Backend
- [ ] Use environment variables in `api.py` (currently hardcoded `dwh_user:dwh_pass`)
- [ ] Add pagination to list endpoints
- [ ] Add authentication (API key / JWT)
- [ ] Add SQLAlchemy models instead of raw SQL strings
- [ ] Add rate limiting
- [ ] Add OpenAPI docs customization / health check endpoint

### Database
- [ ] Add foreign keys (`fact_reviews.product_id → dim_product`, `fact_reviews.user_id → dim_reviewer`)
- [ ] Add `created_at` / `updated_at` timestamps
- [ ] Add partitioning for large fact tables
- [ ] Add materialized views for slow KPI queries
- [ ] Add a proper ETL job scheduler (Airflow / Prefect / cron)

### Frontend
- [ ] Add product detail page with review list
- [ ] Add search & filtering (by category, price range, rating)
- [ ] Add loading skeletons / error states
- [ ] Add most-reviewed chart (data is fetched but not displayed)
- [ ] Use environment variable for API URL instead of hardcoded `localhost:8000`
- [ ] Add responsive design for mobile
- [ ] Add dark mode

### DevOps / Observability
- [ ] Add `.env.example` files
- [ ] Add GitLab/GitHub CI pipeline (lint, build, test)
- [ ] Add Docker `.dockerignore`
- [ ] Use non-root user in containers
- [ ] Add secrets management (Docker secrets / env vault) for DB password
- [ ] Add database backup strategy
- [ ] Add structured logging (JSON) and centralization