-- sql/init.sql  (Amazon product, review & real-time streaming DWH)

CREATE SCHEMA IF NOT EXISTS dwh;

-- ── Dimension: Products ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dwh.dim_product (
    product_id       VARCHAR(50)  PRIMARY KEY,
    product_name     TEXT,
    category         VARCHAR(300),   -- top-level category (first segment)
    category_full    TEXT,           -- full pipe-separated hierarchy
    actual_price     NUMERIC(12,2),
    discounted_price NUMERIC(12,2),
    discount_pct     NUMERIC(5,2),
    rating           NUMERIC(3,1),
    rating_count     INT,
    img_link         TEXT,
    product_link     TEXT,
    created_at       TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ── Dimension: Reviewers ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dwh.dim_reviewer (
    user_id    VARCHAR(100) PRIMARY KEY,
    user_name  VARCHAR(300),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ── Fact: Reviews (With NLP Sentiment & Divergence Flags) ─────────────────────
CREATE TABLE IF NOT EXISTS dwh.fact_reviews (
    review_id       VARCHAR(100) PRIMARY KEY,
    product_id      VARCHAR(50),
    user_id         VARCHAR(100),
    review_title    TEXT,
    review_content  TEXT,
    sentiment_score NUMERIC(4,3),   -- VADER compound score (-1.000 to +1.000)
    sentiment_label VARCHAR(20),    -- 'POSITIVE', 'NEUTRAL', 'NEGATIVE'
    is_divergent    BOOLEAN DEFAULT FALSE, -- Flag: rating vs. sentiment mismatch
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_reviews_product   ON dwh.fact_reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user      ON dwh.fact_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON dwh.fact_reviews(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_reviews_divergent ON dwh.fact_reviews(is_divergent);
CREATE INDEX IF NOT EXISTS idx_product_category  ON dwh.dim_product(category);
CREATE INDEX IF NOT EXISTS idx_product_rating    ON dwh.dim_product(rating);

-- ── Foreign Keys ──────────────────────────────────────────────────────────────
ALTER TABLE dwh.fact_reviews
    DROP CONSTRAINT IF EXISTS fk_review_product,
    ADD CONSTRAINT fk_review_product FOREIGN KEY (product_id) REFERENCES dwh.dim_product(product_id) ON DELETE CASCADE;

ALTER TABLE dwh.fact_reviews
    DROP CONSTRAINT IF EXISTS fk_review_user,
    ADD CONSTRAINT fk_review_user FOREIGN KEY (user_id) REFERENCES dwh.dim_reviewer(user_id) ON DELETE CASCADE;

-- ── Streaming General KPIs (Kafka / Spark Structured Streaming) ────────────────
CREATE TABLE IF NOT EXISTS dwh.fact_streaming_kpis (
    window_start TIMESTAMPTZ NOT NULL,
    metric       TEXT        NOT NULL,
    key          TEXT        NOT NULL,
    value        DOUBLE PRECISION,
    created_at   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_streaming_window ON dwh.fact_streaming_kpis(window_start);
CREATE INDEX IF NOT EXISTS idx_streaming_metric ON dwh.fact_streaming_kpis(metric);

-- ── Streaming Conversion Funnel KPIs ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dwh.fact_funnel_kpis (
    window_start    TIMESTAMPTZ PRIMARY KEY,
    views           INT NOT NULL DEFAULT 0,
    adds_to_cart    INT NOT NULL DEFAULT 0,
    purchases       INT NOT NULL DEFAULT 0,
    abandoned_carts INT NOT NULL DEFAULT 0,
    total_gmv       NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    conversion_rate NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_funnel_window ON dwh.fact_funnel_kpis(window_start);

-- ── Analytical Views ──────────────────────────────────────────────────────────

-- View: Product Sentiment Summary (Aggregated per product)
CREATE OR REPLACE VIEW dwh.v_product_sentiment_summary AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.rating,
    p.rating_count,
    COUNT(r.review_id) AS total_reviews_analyzed,
    ROUND(AVG(r.sentiment_score)::numeric, 3) AS avg_sentiment_score,
    COUNT(CASE WHEN r.sentiment_label = 'POSITIVE' THEN 1 END) AS positive_count,
    COUNT(CASE WHEN r.sentiment_label = 'NEUTRAL' THEN 1 END) AS neutral_count,
    COUNT(CASE WHEN r.sentiment_label = 'NEGATIVE' THEN 1 END) AS negative_count,
    COUNT(CASE WHEN r.is_divergent = TRUE THEN 1 END) AS divergent_reviews_count
FROM dwh.dim_product p
LEFT JOIN dwh.fact_reviews r ON p.product_id = r.product_id
GROUP BY p.product_id, p.product_name, p.category, p.rating, p.rating_count;

-- View: Category Performance & Sentiment
CREATE OR REPLACE VIEW dwh.v_category_performance AS
SELECT
    p.category,
    COUNT(DISTINCT p.product_id) AS product_count,
    ROUND(AVG(p.rating)::numeric, 2) AS avg_rating,
    ROUND(AVG(p.discount_pct)::numeric, 1) AS avg_discount_pct,
    ROUND(AVG(r.sentiment_score)::numeric, 3) AS avg_sentiment_score,
    COUNT(r.review_id) AS total_reviews
FROM dwh.dim_product p
LEFT JOIN dwh.fact_reviews r ON p.product_id = r.product_id
WHERE p.category IS NOT NULL AND p.category <> ''
GROUP BY p.category;