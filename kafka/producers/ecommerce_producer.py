"""
E-commerce Website Producer

Simulates the e-commerce website's event stream: user actions, page views,
cart adds, and purchases. In production this would come from your website's
analytics pipeline (e.g. Segment, Kafka Connect, or a JS SDK).
"""
import json
import os
import random
import time
from datetime import datetime

from kafka import KafkaProducer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC_EVENTS", "ecommerce.events")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all",
    retries=5,
)

EVENT_TYPES = ["view", "add_to_cart", "remove_from_cart", "purchase", "review"]
CATEGORIES = ["Electronics", "Books", "Clothing", "Home", "Sports", "Beauty", "Toys"]


def generate_event() -> dict:
    return {
        "event_id": f"evt_{random.randint(10**9, 10**10 - 1)}",
        "user_id": f"user_{random.randint(1, 10000)}",
        "session_id": f"sess_{random.randint(10**6, 10**7 - 1)}",
        "event_type": random.choice(EVENT_TYPES),
        "product_id": f"B0{random.randint(10**8, 10**9 - 1)}",
        "category": random.choice(CATEGORIES),
        "price": round(random.uniform(5, 500), 2),
        "quantity": random.randint(1, 5),
        "event_time": datetime.utcnow().isoformat() + "Z",
        "source": "ecommerce_website",
    }


def run(interval: float = 1.5, count: int | None = None):
    i = 0
    while count is None or i < count:
        event = generate_event()
        producer.send(TOPIC, value=event)
        print(f"[website] sent {event['event_type']} user={event['user_id']} -> {TOPIC}")
        time.sleep(interval)
        i += 1
    producer.flush()


if __name__ == "__main__":
    run(count=int(os.getenv("COUNT", "100")))