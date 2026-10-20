"""
Amazon API Producer

Simulates the Amazon Product Advertising API pushing new/updated product
catalog data into Kafka. In production this would be replaced by real
calls to the Amazon SP-API (https://affiliate-program.amazon.com/).
"""
import json
import os
import random
import time
from datetime import datetime

from kafka import KafkaProducer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC_PRODUCTS", "amazon.products")

CATEGORIES = ["Electronics", "Books", "Clothing", "Home", "Sports", "Beauty", "Toys"]

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all",
    retries=5,
)


def generate_product() -> dict:
    return {
        "product_id": f"B0{random.randint(10**8, 10**9 - 1)}",
        "product_name": f"Amazon Product {random.randint(1, 10000)}",
        "category": random.choice(CATEGORIES),
        "category_full": f"Electronics > {random.choice(CATEGORIES)} > Subcat",
        "actual_price": round(random.uniform(5, 1000), 2),
        "discounted_price": round(random.uniform(5, 1000), 2),
        "discount_pct": round(random.uniform(0, 80), 1),
        "rating": round(random.uniform(1, 5), 1),
        "rating_count": random.randint(0, 5000),
        "img_link": f"https://example.com/img/{random.randint(1, 1000)}.jpg",
        "product_link": f"https://example.com/dp/B0{random.randint(10**8, 10**9 - 1)}",
        "source": "amazon_api",
        "event_time": datetime.utcnow().isoformat() + "Z",
    }


def run(interval: float = 2.0, count: int | None = None):
    """Publish `count` product events (or forever if count is None)."""
    i = 0
    while count is None or i < count:
        product = generate_product()
        producer.send(TOPIC, value=product)
        print(f"[amazon] sent product {product['product_id']} -> {TOPIC}")
        time.sleep(interval)
        i += 1
    producer.flush()


if __name__ == "__main__":
    run(count=int(os.getenv("COUNT", "50")))