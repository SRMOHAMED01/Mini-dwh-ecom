"""
Kafka Streaming Consumer & Funnel KPI Engine

Consumes events from Kafka, aggregates metric windows (views, carts, purchases, GMV),
and flushes to PostgreSQL (dwh.fact_streaming_kpis and dwh.fact_funnel_kpis).
"""
import json
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

from kafka import KafkaConsumer
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "dwh-consumer-group")
TOPICS = [
    os.getenv("KAFKA_TOPIC_PRODUCTS", "amazon.products"),
    os.getenv("KAFKA_TOPIC_EVENTS", "ecommerce.events"),
]

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "dwh_user")
DB_PASS = os.getenv("DB_PASS", "12345")
DB_NAME = os.getenv("DB_NAME", "ecommerce_dwh")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

WINDOW_SECONDS = int(os.getenv("WINDOW_SECONDS", "30"))

engine = create_engine(DATABASE_URL)

# General In-Memory Window Aggregates
product_counts = defaultdict(int)         # category -> count
event_counts = defaultdict(int)           # event_type -> count
purchase_by_category = defaultdict(float) # category -> revenue

# Funnel Specific Counters for Current Window
funnel_views = 0
funnel_carts = 0
funnel_purchases = 0
funnel_gmv = 0.0


def wait_for_postgres(retries=15, delay=3):
    print(f"[consumer] Connecting to DB {DB_HOST}:{DB_PORT}/{DB_NAME}...")
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[consumer] Connected to PostgreSQL!")
            return True
        except Exception as e:
            print(f"[consumer] Waiting for DB ({i+1}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("[consumer] Could not connect to DB.")


def flush_to_db():
    global funnel_views, funnel_carts, funnel_purchases, funnel_gmv
    now = datetime.utcnow()
    window_start = (now - timedelta(seconds=WINDOW_SECONDS)).isoformat() + "Z"

    # ── 1. Flush General Streaming KPIs ──────────────────────────────────────
    kpi_rows = []
    for cat, cnt in product_counts.items():
        kpi_rows.append({
            "window_start": window_start,
            "metric": "products_by_category",
            "key": cat,
            "value": cnt,
        })
    for et, cnt in event_counts.items():
        kpi_rows.append({
            "window_start": window_start,
            "metric": f"events_{et}",
            "key": et,
            "value": cnt,
        })
    for cat, rev in purchase_by_category.items():
        kpi_rows.append({
            "window_start": window_start,
            "metric": "revenue_by_category",
            "key": cat,
            "value": round(rev, 2),
        })

    # ── 2. Flush Funnel Specific KPIs ────────────────────────────────────────
    abandoned = max(0, funnel_carts - funnel_purchases)
    conv_rate = round((funnel_purchases / funnel_views * 100), 2) if funnel_views > 0 else 0.0

    funnel_row = {
        "window_start": window_start,
        "views": funnel_views,
        "adds_to_cart": funnel_carts,
        "purchases": funnel_purchases,
        "abandoned_carts": abandoned,
        "total_gmv": round(funnel_gmv, 2),
        "conversion_rate": conv_rate,
    }

    metadata = MetaData()
    with engine.begin() as conn:
        if kpi_rows:
            tbl_kpi = Table("fact_streaming_kpis", metadata, schema="dwh", autoload_with=engine)
            stmt_kpi = pg_insert(tbl_kpi).values(kpi_rows).on_conflict_do_nothing()
            conn.execute(stmt_kpi)

        if funnel_views > 0 or funnel_purchases > 0:
            tbl_funnel = Table("fact_funnel_kpis", metadata, schema="dwh", autoload_with=engine)
            stmt_funnel = pg_insert(tbl_funnel).values([funnel_row]).on_conflict_do_nothing()
            conn.execute(stmt_funnel)

    print(f"[consumer] Window {window_start} -> Views: {funnel_views}, Carts: {funnel_carts}, "
          f"Orders: {funnel_purchases}, GMV: ₹{round(funnel_gmv, 2)}, Conv Rate: {conv_rate}%")

    # Clear window
    product_counts.clear()
    event_counts.clear()
    purchase_by_category.clear()
    funnel_views = 0
    funnel_carts = 0
    funnel_purchases = 0
    funnel_gmv = 0.0


def process_event(event: dict):
    global funnel_views, funnel_carts, funnel_purchases, funnel_gmv
    etype = event.get("event_type")
    category = event.get("category", "General")
    price = float(event.get("price", 0.0))
    qty = int(event.get("quantity", 1))

    if etype:
        event_counts[etype] += 1
        if etype == "view":
            funnel_views += 1
        elif etype == "add_to_cart":
            funnel_carts += 1
        elif etype == "purchase":
            funnel_purchases += 1
            rev = price * qty
            funnel_gmv += rev
            purchase_by_category[category] += rev
    elif "product_id" in event and "category" in event:
        # Catalog event
        product_counts[category] += 1


def run():
    wait_for_postgres()
    print(f"[consumer] Subscribing to topics {TOPICS} at {KAFKA_BOOTSTRAP}...")
    consumer = KafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=GROUP_ID,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    print(f"[consumer] Listening for events (window={WINDOW_SECONDS}s)...")

    last_flush = time.time()
    for msg in consumer:
        try:
            event = msg.value
            process_event(event)
        except Exception as e:
            continue

        now = time.time()
        if now - last_flush >= WINDOW_SECONDS:
            flush_to_db()
            last_flush = now


if __name__ == "__main__":
    run()
