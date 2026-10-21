# 🛒 E-Commerce Decision Intelligence Platform

An End-to-End E-Commerce Decision Intelligence Platform featuring a **Hybrid Batch & Streaming Lakehouse (PostgreSQL, Kafka, PySpark)**, **NLP Customer Sentiment Analysis**, **Real-Time Conversion Funnel Analytics**, and an **Executive Decision Cockpit**.

---

## 🏛️ System Architecture

```text
[ amazon.csv ] ─────────────────► [ Batch ETL + NLTK VADER ] ─────┐
                                                                   ▼
[ Simulated E-Commerce Users ] ─► [ Kafka: ecommerce.events ] ──► [ PostgreSQL 15 DWH ]
                                                                   ▲
[ Simulated Amazon SP-API ] ────► [ Kafka: amazon.products ]  ───┤
                                                                   │
                                  [ Kafka / Spark Streaming ] ────┘
                                           │
                                           ▼
                                [ FastAPI Backend (8000) ]
                                           │
                                           ▼
                       [ React 19 Executive Decision Cockpit (5173) ]
```

### Core Architecture Components:
- **PostgreSQL 15 (Lakehouse / DWH)**:
  - `dwh.dim_product`: Catalog info (prices, ratings, categories, discount tiers).
  - `dwh.dim_reviewer`: Customer profiles.
  - `dwh.fact_reviews`: Fact table with **VADER Sentiment Scores (-1 to +1)**, sentiment labels, and **Review Divergence Flags** (identifies fake reviews or product defects).
  - `dwh.fact_funnel_kpis`: Real-time conversion funnel (Views $\to$ Cart Adds $\to$ Purchases $\to$ Cart Abandonment, and Live GMV).
  - `dwh.fact_streaming_kpis`: Sliding window aggregations from Kafka.
  - `dwh.v_product_sentiment_summary` & `dwh.v_category_performance`: Analytical views.
- **Data Ingestion & Processing**:
  - `pipelines/batch/`: Batch ingestion pipeline with numeric cleaners and NLTK VADER sentiment scoring.
  - `pipelines/streaming/producers/`: Realistic catalog-aware clickstream and catalog update producers.
  - `pipelines/streaming/consumer/`: Windowed stream aggregation engine computing live conversion rates and GMV.
  - `pipelines/streaming/spark/`: PySpark Structured Streaming consumer.
- **Serving Layer**:
  - `backend/`: FastAPI application exposing modular endpoints under `/api/v1` and `/api` with CORS support and Server-Sent Events (SSE).
- **Presentation Layer**:
  - `frontend/`: React 19 + Vite + Recharts dashboard with Executive Overview, NLP Review Intelligence, Conversion Funnel, and Live Clickstream Ticker.

---

## 🚀 Quick Start

Run the entire platform with a single command:

```bash
docker compose up --build
```

Once running, access:
- **Executive Decision Cockpit (Frontend)**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Interactive Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **FastAPI Alternative Docs (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **PostgreSQL Database**: `localhost:5432` (`dwh_user` / `12345`, DB: `ecommerce_dwh`)

---

## 📁 Project Structure

```text
.
├── backend/                             # Dedicated FastAPI Service
│   ├── app/
│   │   ├── api/v1/                      # Modular API endpoints (kpis, sentiment, funnel, streaming)
│   │   ├── core/                        # Settings & configurations
│   │   ├── db/                          # Database connection pool & session
│   │   └── main.py                      # FastAPI application entrypoint
│   ├── Dockerfile
│   └── requirements.txt
├── pipelines/
│   ├── batch/                           # Batch Ingestion & NLP Analysis
│   │   ├── cleaners.py                  # Modular numeric & string cleaning
│   │   ├── sentiment.py                 # NLTK VADER sentiment extraction & divergence detection
│   │   ├── main.py                      # Batch pipeline orchestrator
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── streaming/                       # Event Streaming & Real-Time Aggregation
│       ├── producers/                   # Catalog-aware clickstream & SP-API producers
│       ├── consumer/                    # Kafka consumer with funnel & GMV aggregation
│       ├── spark/                       # PySpark Structured Streaming consumer
│       ├── Dockerfile
│       └── requirements.txt
├── frontend/                            # React 19 + Vite Dashboard
│   ├── src/
│   │   ├── App.jsx                      # Executive Decision Cockpit (Tabs: Overview, NLP, Funnel, Stream)
│   │   ├── App.css                      # Styling for cockpit, badges, feed, and modals
│   │   └── index.css                    # Design tokens & dark/light theme variables
│   ├── Dockerfile
│   └── package.json
├── sql/
│   └── init.sql                         # PostgreSQL schema (dimensions, facts, views, indexes)
├── amazon.csv                           # Historical Amazon catalog & review dataset
├── docker-compose.yml                   # Full-stack container orchestration
├── .env.example
├── README.md
└── TODO.md
```

---

## 📡 API Endpoints

### Core KPIs & Analytics
- `GET /api/v1/kpi-summary`: High-level business metrics (products, average rating, discount %, sentiment score).
- `GET /api/v1/top-categories`: Top 10 categories with volume and pricing metrics.
- `GET /api/v1/top-rated-products`: High-volume products ($\ge 500$ ratings) sorted by rating.
- `GET /api/v1/most-reviewed`: Top 10 most-reviewed products.
- `GET /api/v1/discount-distribution`: Products grouped into discount percentage tiers.

### NLP Sentiment & Review Intelligence
- `GET /api/v1/sentiment/overview`: Global sentiment ratios (Positive / Neutral / Negative / Divergent %).
- `GET /api/v1/sentiment/divergent-products`: Suspicious products with high star ratings ($\ge 4.0$) but negative review content.
- `GET /api/v1/sentiment/product/{id}`: Detailed review breakdown with sentiment tags for a specific product.

### Conversion Funnel & Real-Time Streaming
- `GET /api/v1/funnel/latest`: Cumulative conversion funnel metrics ($\text{Views} \to \text{Cart Adds} \to \text{Purchases}$, Cart Abandonment Rate, and GMV).
- `GET /api/v1/funnel/history`: Historical funnel window timelines.
- `GET /api/v1/streaming/kpis`: Latest sliding window streaming metrics.
- `GET /api/v1/streaming/live-feed`: Server-Sent Events (SSE) stream for live ticking orders and GMV.