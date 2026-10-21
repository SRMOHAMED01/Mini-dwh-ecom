from fastapi import APIRouter
from app.db.session import query

router = APIRouter()


@router.get("/kpi-summary")
def get_kpi_summary():
    """Returns high-level business KPIs including total products, ratings, discounts, and sentiment."""
    rows = query("""
        SELECT
            COUNT(DISTINCT p.product_id)            AS total_products,
            ROUND(AVG(p.rating)::numeric, 2)        AS avg_rating,
            ROUND(AVG(p.discount_pct)::numeric, 1)  AS avg_discount_pct,
            (SELECT COUNT(*) FROM dwh.fact_reviews) AS total_reviews,
            (SELECT ROUND(AVG(sentiment_score)::numeric, 3) FROM dwh.fact_reviews) AS avg_sentiment
        FROM dwh.dim_product p
    """)
    return rows[0] if rows else {}


@router.get("/top-categories")
def get_top_categories():
    """Returns top 10 categories by product volume with ratings, discounts, and sentiment."""
    return query("""
        SELECT
            category,
            product_count,
            avg_rating,
            avg_discount_pct,
            avg_sentiment_score,
            total_reviews
        FROM dwh.v_category_performance
        ORDER BY product_count DESC
        LIMIT 10
    """)


@router.get("/top-rated-products")
def get_top_rated_products():
    """Top rated products with at least 500 reviews."""
    return query("""
        SELECT
            product_id,
            LEFT(product_name, 60) AS product_name,
            rating,
            rating_count,
            ROUND(discount_pct, 1) AS discount_pct
        FROM dwh.dim_product
        WHERE rating_count >= 500
        ORDER BY rating DESC, rating_count DESC
        LIMIT 10
    """)


@router.get("/most-reviewed")
def get_most_reviewed():
    """Top 10 most-reviewed products with review counts and ratings."""
    return query("""
        SELECT
            p.product_id,
            LEFT(p.product_name, 60) AS product_name,
            COUNT(r.review_id)        AS review_count,
            p.rating,
            ROUND(AVG(r.sentiment_score)::numeric, 2) AS avg_sentiment
        FROM dwh.dim_product p
        JOIN dwh.fact_reviews r ON p.product_id = r.product_id
        GROUP BY p.product_id, p.product_name, p.rating
        ORDER BY review_count DESC
        LIMIT 10
    """)


@router.get("/discount-distribution")
def get_discount_distribution():
    """Distribution of products across discount percentage tiers."""
    return query("""
        SELECT
            CASE
                WHEN discount_pct < 20  THEN '0-19%'
                WHEN discount_pct < 40  THEN '20-39%'
                WHEN discount_pct < 60  THEN '40-59%'
                WHEN discount_pct < 80  THEN '60-79%'
                ELSE '80-100%'
            END AS bucket,
            COUNT(*) AS product_count
        FROM dwh.dim_product
        WHERE discount_pct IS NOT NULL
        GROUP BY bucket
        ORDER BY bucket
    """)
