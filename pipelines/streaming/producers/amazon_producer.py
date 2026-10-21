"""
Amazon API Catalog Producer

Simulates the Amazon SP-API streaming product catalog updates to Kafka.
"""
import json
import os
import random
import time
from datetime import datetime

from kafka import KafkaProducer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC_PRODUCTS", "amazon.products")

CATEGORIES = [
    "Computers&Accessories", "Electronics", "Home&Kitchen",
    "OfficeProducts", "MusicalInstruments", "Toys&Games"
]


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
        retries=5,
    )


def generate_product() -> dict:
    actual_price = round(random.uniform(20, 2000), 2)
    discount_pct = round(random.uniform(5, 75), 1)
    discounted_price = round(actual_price * (1 - discount_pct / 100), 2)
    cat = random.choice(CATEGORIES)

    return {
        "product_id": f"B0{random.randint(10**8, 10**9 - 1)}",
        "product_name": f"Amazon Premium {cat} Item #{random.randint(100, 9999)}",
        "category": cat,
        "category_full": f"{cat}|Accessories|Featured",
        "actual_price": actual_price,
        "discounted_price": discounted_price,
        "discount_pct": discount_pct,
        "rating": round(random.uniform(2.5, 5.0), 1),
        "rating_count": random.randint(50, 15000),
        "img_link": f"https://images.example.com/{random.randint(1, 500)}.jpg",
        "product_link": f"https://amazon.com/dp/B0{random.randint(10**8, 10**9 - 1)}",
        "source": "amazon_sp_api",
        "event_time": datetime.utcnow().isoformat() + "Z",
    }


def run(interval: float = 2.0, count: int | None = None):
    print(f"[amazon-producer] Connecting to Kafka at {KAFKA_BOOTSTRAP}...")
    producer = create_producer()
    print(f"[amazon-producer] Publishing to topic '{TOPIC}'...")

    i = 0
    while count is None or i < count:
        product = generate_product()
        producer.send(TOPIC, value=product)
        print(f"[amazon-producer] Catalog update: {product['product_id']} ({product['category']}) -> {TOPIC}")
        time.sleep(interval)
        i += 1

    producer.flush()
    print(f"[amazon-producer] Finished emitting {i} products.")


if __name__ == "__main__":
    count_env = os.getenv("COUNT", "50")
    run(count=None if count_env.lower() == "infinite" else int(count_env))
