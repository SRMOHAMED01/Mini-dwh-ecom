# 📋 Master To-Do List: E-Commerce Decision Intelligence Platform

A complete, prioritized execution checklist tracking the platform build-out.

---

## 🏛️ Phase 1: Structural Reorganization & Clean Architecture
- [x] **1.1 Workspace & Folder Alignment**
  - [x] Flatten nested folder (`Mini-dwh-ecom/Mini-dwh-ecom` → project root). *(Done)*
  - [x] Update `.gitignore` and `.dockerignore`. *(Done)*
- [x] **1.2 Decouple Backend Service (`backend/`)**
  - [x] Create `backend/app/core/config.py` (Pydantic Settings for DB, Kafka, CORS). *(Done)*
  - [x] Create `backend/app/db/session.py` (SQLAlchemy connection). *(Done)*
  - [x] Create `backend/app/api/v1/router.py` & modular endpoints (`kpis.py`, `sentiment.py`, `funnel.py`, `products.py`, `streaming.py`). *(Done)*
  - [x] Create `backend/Dockerfile` & `backend/requirements.txt`. *(Done)*
- [x] **1.3 Modularize Data Pipelines (`pipelines/`)**
  - [x] Set up `pipelines/batch/` (`cleaners.py`, `sentiment.py`, `main.py`, `Dockerfile`, `requirements.txt`). *(Done)*
  - [x] Set up `pipelines/streaming/` (`producers/`, `consumer/`, `spark/`, `Dockerfile`, `requirements.txt`). *(Done)*
- [x] **1.4 Full-Stack Docker Compose**
  - [x] Create `frontend/Dockerfile`. *(Done)*
  - [x] Update `docker-compose.yml` to orchestrate postgres, backend, frontend, kafka, zookeeper, batch-etl, and streaming consumers. *(Done)*

---

## 🧠 Phase 2: NLP Customer Sentiment & Review Intelligence
- [x] **2.1 Database Schema Upgrade (`sql/init.sql`)**
  - [x] Add `sentiment_score NUMERIC(4,3)`, `sentiment_label VARCHAR(20)`, `is_divergent BOOLEAN` to `dwh.fact_reviews`. *(Done)*
  - [x] Add indexes on `(product_id, sentiment_label)` and `is_divergent`. *(Done)*
  - [x] Create views `dwh.v_product_sentiment_summary` and `dwh.v_category_performance`. *(Done)*
- [x] **2.2 NLP Ingestion Engine**
  - [x] Implement VADER sentiment analyzer in batch ETL pipeline (`pipelines/batch/sentiment.py`). *(Done)*
  - [x] Compute sentiment compound score, labels (`POSITIVE`, `NEUTRAL`, `NEGATIVE`), and divergence flags. *(Done)*
  - [x] Batch upsert enriched reviews into PostgreSQL. *(Done)*
- [x] **2.3 Sentiment API Endpoints**
  - [x] `GET /api/v1/sentiment/overview` (catalog sentiment distribution). *(Done)*
  - [x] `GET /api/v1/sentiment/divergent-products` (fake review / defect alert list). *(Done)*
  - [x] `GET /api/v1/sentiment/product/{id}` (reviews with sentiment badges and inspection modal). *(Done)*

---

## ⚡ Phase 3: Connected Streaming & Real-Time Conversion Funnel
- [x] **3.1 Realistic Catalog-Aware E-Commerce Producer**
  - [x] Update `ecommerce_producer.py` to sample real catalog product IDs from `amazon.csv`. *(Done)*
  - [x] Simulate realistic session journeys: `view` (100%) → `add_to_cart` (35%) → `purchase` (14%). *(Done)*
- [x] **3.2 Funnel & GMV Aggregation Engine**
  - [x] Add `dwh.fact_funnel_kpis` table in `sql/init.sql`. *(Done)*
  - [x] Aggregate windowed views, carts, purchases, cart abandonment rate, and GMV in `kafka_consumer.py`. *(Done)*
- [x] **3.3 Live Real-Time Server-Sent Events (SSE)**
  - [x] Implement `GET /api/v1/streaming/live-feed` in FastAPI to push real-time events to the frontend. *(Done)*

---

## 📊 Phase 4: Executive Decision Cockpit (Frontend UI)
- [x] **4.1 Cockpit Shell & Theme System**
  - [x] Tabbed interface in `App.jsx`: Executive Overview, NLP Sentiment, Funnel & Pricing, Live Event Stream. *(Done)*
  - [x] Dark / Light theme toggle with CSS variables. *(Done)*
  - [x] Loading states & error alert banners. *(Done)*
- [x] **4.2 Tab 1: Executive Overview Widgets**
  - [x] Real-time GMV counter, conversion rate, rating, discount, and catalog product count. *(Done)*
  - [x] Rendered Most-Reviewed Products chart (P0 fix!). *(Done)*
  - [x] Top Categories by Volume and Discount Tiers chart. *(Done)*
- [x] **4.3 Tab 2: NLP Customer Sentiment Widgets**
  - [x] Sentiment distribution metrics (Positive / Neutral / Negative %). *(Done)*
  - [x] "Divergence Alarm" table (high star rating with negative review text). *(Done)*
  - [x] Product Review Inspector modal: view actual customer reviews with sentiment tags. *(Done)*
- [x] **4.4 Tab 3: Conversion Funnel & Pricing Widgets**
  - [x] Visual conversion funnel (Views → Cart Adds → Purchases → Cart Abandonment). *(Done)*
  - [x] Cart Abandonment rate metrics and GMV. *(Done)*
- [x] **4.5 Tab 4: Live Event Stream**
  - [x] Real-time SSE connection feeding live purchase events and amounts without page refreshes. *(Done)*

---

## 🧪 Phase 5: Verification & Testing
- [ ] **5.1 Unit Tests for Cleaners & Sentiment**:
  - [ ] Add `pytest` test suite for `clean_price`, `clean_pct`, `clean_count`, and `analyze_review`.
- [ ] **5.2 Integration Tests for API**:
  - [ ] Write integration test verifying FastAPI endpoints respond correctly with mock DB.
- [ ] **5.3 Docker Compose Smoke Test**:
  - [ ] Run `docker compose up --build` and verify service health.