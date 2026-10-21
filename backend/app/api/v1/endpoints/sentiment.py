from fastapi import APIRouter
from app.db.session import query

router = APIRouter()


@router.get("/overview")
def get_sentiment_overview():
    """Returns overall catalog sentiment distribution and average polarity."""
    rows = query("""
        SELECT
            COUNT(*)                                                                AS total_reviews,
            COUNT(CASE WHEN sentiment_label = 'POSITIVE' THEN 1 END)               AS positive_count,
            COUNT(CASE WHEN sentiment_label = 'NEUTRAL'  THEN 1 END)               AS neutral_count,
            COUNT(CASE WHEN sentiment_label = 'NEGATIVE' THEN 1 END)               AS negative_count,
            COUNT(CASE WHEN is_divergent = TRUE          THEN 1 END)               AS divergent_count,
            ROUND(AVG(sentiment_score)::numeric, 3)                                AS avg_sentiment_score
        FROM dwh.fact_reviews
    """)
    if not rows or rows[0]["total_reviews"] == 0:
        return {
            "total_reviews": 0, "positive_count": 0, "neutral_count": 0,
            "negative_count": 0, "divergent_count": 0, "avg_sentiment_score": 0.0
        }

    res = rows[0]
    total = res["total_reviews"] or 1
    res["positive_pct"] = round((res["positive_count"] / total) * 100, 1)
    res["neutral_pct"] = round((res["neutral_count"] / total) * 100, 1)
    res["negative_pct"] = round((res["negative_count"] / total) * 100, 1)
    return res


@router.get("/divergent-products")
def get_divergent_products(limit: int = 10):
    """
    Returns products flagged with high star ratings (>= 4.0)
    yet containing negative customer reviews (Fake Review / Defect Alarm).
    """
    return query("""
        SELECT
            p.product_id,
            LEFT(p.product_name, 70) AS product_name,
            p.category,
            p.rating,
            p.rating_count,
            COUNT(r.review_id) AS total_reviews,
            COUNT(CASE WHEN r.is_divergent = TRUE THEN 1 END) AS divergent_reviews_count,
            ROUND(AVG(r.sentiment_score)::numeric, 3) AS avg_sentiment_score
        FROM dwh.dim_product p
        JOIN dwh.fact_reviews r ON p.product_id = r.product_id
        WHERE p.rating >= 4.0
        GROUP BY p.product_id, p.product_name, p.category, p.rating, p.rating_count
        HAVING COUNT(CASE WHEN r.is_divergent = TRUE THEN 1 END) > 0
        ORDER BY divergent_reviews_count DESC, p.rating DESC
        LIMIT :limit
    """, {"limit": limit})


@router.get("/product/{product_id}")
def get_product_sentiment_details(product_id: str):
    """Returns detailed sentiment breakdown and sample reviews for a specific product."""
    prod_rows = query("""
        SELECT product_id, product_name, category, rating, rating_count, img_link, actual_price, discounted_price
        FROM dwh.dim_product
        WHERE product_id = :pid
    """, {"pid": product_id})

    if not prod_rows:
        return {"error": "Product not found"}

    product = prod_rows[0]
    reviews = query("""
        SELECT
            review_id,
            review_title,
            review_content,
            sentiment_score,
            sentiment_label,
            is_divergent
        FROM dwh.fact_reviews
        WHERE product_id = :pid
        ORDER BY is_divergent DESC, sentiment_score ASC
        LIMIT 10
    """, {"pid": product_id})

    summary = query("""
        SELECT
            COUNT(*) AS total_reviews,
            ROUND(AVG(sentiment_score)::numeric, 3) AS avg_sentiment_score,
            COUNT(CASE WHEN sentiment_label = 'POSITIVE' THEN 1 END) AS positive_count,
            COUNT(CASE WHEN sentiment_label = 'NEUTRAL'  THEN 1 END) AS neutral_count,
            COUNT(CASE WHEN sentiment_label = 'NEGATIVE' THEN 1 END) AS negative_count,
            COUNT(CASE WHEN is_divergent = TRUE          THEN 1 END) AS divergent_count
        FROM dwh.fact_reviews
        WHERE product_id = :pid
    """, {"pid": product_id})

    return {
        "product": product,
        "sentiment_summary": summary[0] if summary else {},
        "sample_reviews": reviews
    }
