import os
import time
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "dwh_user")
DB_PASS = os.getenv("DB_PASS", "12345")
DB_NAME = os.getenv("DB_NAME", "ecommerce_dwh")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
CSV_PATH = os.getenv("CSV_PATH", "/data/amazon.csv")


def wait_for_db(engine, retries=10, delay=3):
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database is ready!")
            return True
        except Exception as e:
            print(f"⏳ Waiting for DB... ({i+1}/{retries}): {e}")
            time.sleep(delay)
    raise Exception("❌ Could not connect to database")


def pg_upsert(table, conn, keys, data_iter):
    """Insert rows, silently skip duplicates (ON CONFLICT DO NOTHING)."""
    data = [dict(zip(keys, row)) for row in data_iter]
    stmt = pg_insert(table.table).values(data).on_conflict_do_nothing()
    conn.execute(stmt)


# ── Cleaners ──────────────────────────────────────────────────────────────────

def clean_price(val):
    """'₹1,099' → 1099.0"""
    if pd.isna(val):
        return None
    return float(str(val).replace("₹", "").replace(",", "").strip())


def clean_pct(val):
    """'64%' → 64.0"""
    if pd.isna(val):
        return None
    try:
        return float(str(val).replace("%", "").strip())
    except ValueError:
        return None


def clean_count(val):
    """'24,269' → 24269"""
    if pd.isna(val):
        return 0
    try:
        return int(str(val).replace(",", "").strip())
    except ValueError:
        return 0


def clean_rating(val):
    """'4.2' → 4.2  (handles the rare '4,2' locale variant)"""
    if pd.isna(val):
        return None
    try:
        return float(str(val).replace(",", ".").strip())
    except ValueError:
        return None


# ── ETL ───────────────────────────────────────────────────────────────────────

def run_etl():
    engine = create_engine(DATABASE_URL)
    wait_for_db(engine)

    print(f"📥 Loading {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH, on_bad_lines="skip")
    print(f"   Raw rows: {len(df)}")

    # ── Clean numeric fields ─────────────────────────────────────────────────
    df["actual_price"]     = df["actual_price"].apply(clean_price)
    df["discounted_price"] = df["discounted_price"].apply(clean_price)
    df["discount_pct"]     = df["discount_percentage"].apply(clean_pct)
    df["rating"]           = df["rating"].apply(clean_rating)
    df["rating_count"]     = df["rating_count"].apply(clean_count)

    # ── Category: top-level and full hierarchy ───────────────────────────────
    df["category_full"] = df["category"].fillna("")
    df["category"]      = df["category_full"].str.split("|").str[0]

    # ── dim_product ──────────────────────────────────────────────────────────
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
    print(f"✅ dim_product   : {len(products)} rows")

    # ── Explode reviewers → dim_reviewer + fact_reviews ─────────────────────
    reviewer_rows = []
    review_rows   = []

    for _, row in df.iterrows():
        pid = row["product_id"]

        def split(field, join_remainder=False, expected_n=None):
            raw = row.get(field, "")
            parts = [v.strip() for v in str(raw).split(",")] if pd.notna(raw) else []
            # review_content is free text and may contain commas.
            # If it produced more segments than expected, re-join the tail
            # so alignment with the other fields is preserved.
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
            uname  = user_names[i]  if i < len(user_names)    else ""
            rid    = review_ids[i]  if i < len(review_ids)    else ""
            rtitle = review_titles[i] if i < len(review_titles) else ""
            rcont  = rev_contents[i]  if i < len(rev_contents)  else ""

            if uid:
                reviewer_rows.append({"user_id": uid, "user_name": uname})
            if rid:
                review_rows.append({
                    "review_id":      rid,
                    "product_id":     pid,
                    "user_id":        uid,
                    "review_title":   rtitle,
                    "review_content": rcont,
                })

    reviewers_df = pd.DataFrame(reviewer_rows).drop_duplicates(subset="user_id")
    reviews_df   = pd.DataFrame(review_rows).drop_duplicates(subset="review_id")

    reviewers_df.to_sql(
        "dim_reviewer", engine, schema="dwh",
        if_exists="append", index=False, method=pg_upsert,
    )
    print(f"✅ dim_reviewer  : {len(reviewers_df)} rows")

    reviews_df.to_sql(
        "fact_reviews", engine, schema="dwh",
        if_exists="append", index=False, method=pg_upsert,
    )
    print(f"✅ fact_reviews  : {len(reviews_df)} rows")

    print("🎉 ETL complete!")


if __name__ == "__main__":
    run_etl()
