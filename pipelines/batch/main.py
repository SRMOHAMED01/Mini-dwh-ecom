"""
Batch Ingestion Pipeline with NLP Sentiment Analysis for Amazon Products & Reviews.
"""
import os
import time
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from cleaners import clean_price, clean_pct, clean_count, clean_rating
from sentiment import analyze_review

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "dwh_user")
DB_PASS = os.getenv("DB_PASS", "12345")
DB_NAME = os.getenv("DB_NAME", "ecommerce_dwh")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

CSV_PATH = os.getenv("CSV_PATH", "/data/amazon.csv")


def wait_for_db(engine, retries=15, delay=3):
    print(f"🔄 Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}...")
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connection established successfully!")
            return True
        except Exception as e:
            print(f"⏳ Waiting for DB... ({i+1}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("❌ Could not connect to database after retries.")


def pg_upsert(table, conn, keys, data_iter):
    """Insert rows, silently skip duplicates (ON CONFLICT DO NOTHING)."""
    data = [dict(zip(keys, row)) for row in data_iter]
    stmt = pg_insert(table.table).values(data).on_conflict_do_nothing()
    conn.execute(stmt)


def run_etl():
    engine = create_engine(DATABASE_URL)
    wait_for_db(engine)

    print(f"📥 Loading dataset from {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH, on_bad_lines="skip")
    print(f"   Raw rows read: {len(df)}")

    # ── 1. Clean Numeric Fields ──────────────────────────────────────────────
    df["actual_price"]     = df["actual_price"].apply(clean_price)
    df["discounted_price"] = df["discounted_price"].apply(clean_price)
    df["discount_pct"]     = df["discount_percentage"].apply(clean_pct)
    df["rating"]           = df["rating"].apply(clean_rating)
    df["rating_count"]     = df["rating_count"].apply(clean_count)

    # ── 2. Category Hierarchy ────────────────────────────────────────────────
    df["category_full"] = df["category"].fillna("")
    df["category"]      = df["category_full"].str.split("|").str[0]

    # ── 3. Upsert dim_product ────────────────────────────────────────────────
    products = (
        df.drop_duplicates(subset="product_id")[[
            "product_id", "product_name", "category", "category_full",
            "actual_price", "discounted_price", "discount_pct",
            "rating", "rating_count", "img_link", "product_link",
        ]]
    )
    products.to_sql(
        "dim_product", engine, schema="dwh",
        if_exists="append", index=False, method=pg_upsert,
    )
    print(f"✅ Loaded dim_product : {len(products)} records")

    # ── 4. Explode Reviewers & Fact Reviews with NLP Sentiment ───────────────
    reviewer_rows = []
    review_rows   = []
    sentiment_stats = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0, "DIVERGENT": 0}

    print("🧠 Performing NLP sentiment analysis on reviews...")
    for _, row in df.iterrows():
        pid = row["product_id"]
        prod_rating = row["rating"]

        def split(field, join_remainder=False, expected_n=None):
            raw = row.get(field, "")
            parts = [v.strip() for v in str(raw).split(",")] if pd.notna(raw) else []
            if join_remainder and expected_n is not None and len(parts) > expected_n:
                parts = parts[:expected_n - 1] + [",".join(parts[expected_n - 1:])]
            return parts

        user_ids      = split("user_id")
        n = len(user_ids)
        user_names    = split("user_name")
        review_ids    = split("review_id")
        review_titles = split("review_title")
        rev_contents  = split("review_content", join_remainder=True, expected_n=n)

        for i in range(n):
            uid    = user_ids[i]
            uname  = user_names[i]    if i < len(user_names)    else ""
            rid    = review_ids[i]    if i < len(review_ids)    else ""
            rtitle = review_titles[i] if i < len(review_titles) else ""
            rcont  = rev_contents[i]  if i < len(rev_contents)  else ""

            if uid:
                reviewer_rows.append({"user_id": uid, "user_name": uname})

            if rid:
                # Perform VADER sentiment analysis
                sentiment_res = analyze_review(rtitle, rcont, product_rating=prod_rating)
                lbl = sentiment_res["label"]
                sentiment_stats[lbl] += 1
                if sentiment_res["is_divergent"]:
                    sentiment_stats["DIVERGENT"] += 1

                review_rows.append({
                    "review_id":       rid,
                    "product_id":      pid,
                    "user_id":         uid,
                    "review_title":    rtitle,
                    "review_content":  rcont,
                    "sentiment_score": sentiment_res["score"],
                    "sentiment_label": sentiment_res["label"],
                    "is_divergent":    sentiment_res["is_divergent"],
                })

    reviewers_df = pd.DataFrame(reviewer_rows).drop_duplicates(subset="user_id")
    reviews_df   = pd.DataFrame(review_rows).drop_duplicates(subset="review_id")

    reviewers_df.to_sql(
        "dim_reviewer", engine, schema="dwh",
        if_exists="append", index=False, method=pg_upsert,
    )
    print(f"✅ Loaded dim_reviewer: {len(reviewers_df)} records")

    reviews_df.to_sql(
        "fact_reviews", engine, schema="dwh",
        if_exists="append", index=False, method=pg_upsert,
    )
    print(f"✅ Loaded fact_reviews: {len(reviews_df)} records with sentiment scores")
    print(f"   📊 Sentiment Breakdown -> Positive: {sentiment_stats['POSITIVE']}, "
          f"Neutral: {sentiment_stats['NEUTRAL']}, Negative: {sentiment_stats['NEGATIVE']}")
    print(f"   🚨 Divergent Reviews Identified: {sentiment_stats['DIVERGENT']}")
    print("🎉 Batch ETL with NLP Intelligence completed successfully!")


if __name__ == "__main__":
    run_etl()
