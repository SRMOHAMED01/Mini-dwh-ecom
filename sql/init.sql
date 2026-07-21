-- sql/init.sql  (Amazon product & review DWH)

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
    product_link     TEXT
);

-- ── Dimension: Reviewers ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dwh.dim_reviewer (
    user_id   VARCHAR(100) PRIMARY KEY,
    user_name VARCHAR(300)
);

-- ── Fact: Reviews ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dwh.fact_reviews (
    review_id      VARCHAR(100) PRIMARY KEY,
    product_id     VARCHAR(50),
    user_id        VARCHAR(100),
    review_title   TEXT,
    review_content TEXT
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_reviews_product  ON dwh.fact_reviews(product_id); 
CREATE INDEX IF NOT EXISTS idx_reviews_user     ON dwh.fact_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_product_category ON dwh.dim_product(category);
CREATE INDEX IF NOT EXISTS idx_product_rating   ON dwh.dim_product(rating); 