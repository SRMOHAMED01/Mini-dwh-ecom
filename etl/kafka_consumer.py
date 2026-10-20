"""
Kafka Consumer (lightweight, Python)

Consumes product + website events from Kafka, aggregates them in a
sliding window, and upserts into PostgreSQL (dwh schema).

For true Spark Structured Streaming, see spark_streaming.py.
"""
import json
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

from kafka import KafkaConsumer
from sqlalchemy import create_engine, MetaData, Table
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

# In-memory windowed aggregations
product_counts = defaultdict(int)      # category -> product count
event_counts = defaultdict(int)        # event_type -> count
purchase_by_category = defaultdict(float)  # category -> revenue

# Trailing window of events for review aggregation
recent_events = []


def flush_to_db():
    """Upsert windowed aggregates into dwh.fact_streaming_kpis."""
    now = datetime.utcnow()
    window_start = (now - timedelta(seconds=WINDOW_SECONDS)).isoformat() + "Z"

    rows = []
    for cat, cnt in product_counts.items():
        rows.append({
            "window_start": window_start,
            "metric": "products_by_category",
            "key": cat,
            "value": cnt,
        })
    for et, cnt in event_counts.items():
        rows.append({
            "window_start": window_start,
            "metric": f"events_{et}",
            "key": et,
            "value": cnt,
        })
    for cat, rev in purchase_by_category.items():
        rows.append({
            "window_start": window_start,
            "metric": "revenue_by_category",
            "key": cat,
            "value": round(rev, 2),
        })

    if not rows:
        return

    metadata = MetaData()
    streaming_table = Table(
        "fact_streaming_kpis", metadata,
        schema="dwh", autoload_with=engine,
    )
    with engine.begin() as conn:
        stmt = pg_insert(streaming_table).values(rows).on_conflict_do_nothing()
        conn.execute(stmt)

    product_counts.clear()
    event_counts.clear()
    purchase_by_category.clear()
    print(f"[consumer] flushed {len(rows)} aggregate rows at {window_start}")


def process_event(event: dict):
    etype = event.get("event_type")
    category = event.get("category", "Unknown")
    event_counts[etype] = event_counts.get(etype, 0) + 1

    if etype == "purchase":
        purchase_by_category[category] += float(event.get("price", 0)) * int(event.get("quantity", 1))

    # Track product catalog events
    if "product_id" in event and "category" in event and etype is None:
        product_counts[category] += 1

    recent_events.append(event)
    # Keep only last 1000 events in memory
    if len(recent_events) > 1000:
        recent_events.pop(0)


def run():
    consumer = KafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=GROUP_ID,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    print(f"[consumer] subscribed to {TOPICS}")

    last_flush = time.time()
    for msg in consumer:
        try:
            event = json.loads(msg.value.decode("utf-8"))
        except Exception:
            continue
        process_event(event)

        now = time.time()
        if now - last_flush >= WINDOW_SECONDS:
            flush_to_db()
            last_flush = now


if __name__ == "__main__":
    run()