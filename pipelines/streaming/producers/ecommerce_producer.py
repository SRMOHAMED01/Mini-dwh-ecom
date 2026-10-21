"""
E-commerce Clickstream & Funnel Producer

Generates realistic user journeys (view -> add_to_cart -> purchase)
tied to real products from the catalog.
"""
import json
import os
import random
import time
from datetime import datetime
import pandas as pd
from kafka import KafkaProducer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC_EVENTS", "ecommerce.events")
CSV_PATH = os.getenv("CSV_PATH", "/data/amazon.csv")

# Fallback catalog if CSV is unreachable
DEFAULT_PRODUCTS = [
    {"product_id": "B07JW9H4J1", "category": "Computers&Accessories", "price": 399.0},
    {"product_id": "B098NS6PVG", "category": "Computers&Accessories", "price": 199.0},
    {"product_id": "B096MSW6CT", "category": "Computers&Accessories", "price": 199.0},
    {"product_id": "B08HDJ86NZ", "category": "Computers&Accessories", "price": 329.0},
    {"product_id": "B08CF3B7N1", "category": "Electronics", "price": 899.0},
    {"product_id": "B09ZBFV7LY", "category": "Home&Kitchen", "price": 1499.0},
    {"product_id": "B082T6V3DW", "category": "OfficeProducts", "price": 249.0},
]


def load_catalog():
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH, on_bad_lines="skip")
            df["category_clean"] = df["category"].fillna("General").str.split("|").str[0]
            catalog = []
            for _, r in df.iterrows():
                try:
                    price_str = str(r.get("discounted_price", "299")).replace("₹", "").replace(",", "").strip()
                    price = float(price_str)
                except ValueError:
                    price = 299.0
                catalog.append({
                    "product_id": str(r["product_id"]),
                    "category": str(r["category_clean"]),
                    "price": price,
                })
            print(f"[ecommerce-producer] Loaded {len(catalog)} real products from catalog.")
            return catalog
        except Exception as e:
            print(f"[ecommerce-producer] Warning loading catalog: {e}. Using fallback.")
    return DEFAULT_PRODUCTS


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
        retries=5,
    )


def run(interval: float = 1.0, count: int | None = None):
    print(f"[ecommerce-producer] Connecting to Kafka at {KAFKA_BOOTSTRAP}...")
    producer = create_producer()
    catalog = load_catalog()

    i = 0
    while count is None or i < count:
        # Generate user journey
        user_id = f"user_{random.randint(1000, 9999)}"
        session_id = f"sess_{random.randint(100000, 999999)}"
        prod = random.choice(catalog)
        now_iso = datetime.utcnow().isoformat() + "Z"

        # 1. Step 1: Always a 'view'
        view_event = {
            "event_id": f"evt_{random.randint(10**9, 10**10 - 1)}",
            "session_id": session_id,
            "user_id": user_id,
            "event_type": "view",
            "product_id": prod["product_id"],
            "category": prod["category"],
            "price": prod["price"],
            "quantity": 1,
            "event_time": now_iso,
            "source": "web_clickstream",
        }
        producer.send(TOPIC, value=view_event)
        print(f"[ecommerce-producer] [VIEW] {user_id} viewed {prod['product_id']}")
        i += 1
        time.sleep(interval * 0.4)

        # 2. Step 2: 35% probability of adding to cart
        if random.random() < 0.35:
            qty = random.choices([1, 2, 3], weights=[0.8, 0.15, 0.05])[0]
            cart_event = {
                "event_id": f"evt_{random.randint(10**9, 10**10 - 1)}",
                "session_id": session_id,
                "user_id": user_id,
                "event_type": "add_to_cart",
                "product_id": prod["product_id"],
                "category": prod["category"],
                "price": prod["price"],
                "quantity": qty,
                "event_time": datetime.utcnow().isoformat() + "Z",
                "source": "web_clickstream",
            }
            producer.send(TOPIC, value=cart_event)
            print(f"[ecommerce-producer] [CART] {user_id} added {prod['product_id']} (qty: {qty})")
            i += 1
            time.sleep(interval * 0.4)

            # 3. Step 3: 40% of carts convert to purchase (overall ~14% conversion)
            if random.random() < 0.40:
                purchase_event = {
                    "event_id": f"evt_{random.randint(10**9, 10**10 - 1)}",
                    "session_id": session_id,
                    "user_id": user_id,
                    "event_type": "purchase",
                    "product_id": prod["product_id"],
                    "category": prod["category"],
                    "price": prod["price"],
                    "quantity": qty,
                    "event_time": datetime.utcnow().isoformat() + "Z",
                    "source": "web_clickstream",
                }
                producer.send(TOPIC, value=purchase_event)
                total_val = round(prod["price"] * qty, 2)
                print(f"[ecommerce-producer] 💰 [PURCHASE] {user_id} ordered {prod['product_id']}! GMV: ₹{total_val}")
                i += 1
            else:
                print(f"[ecommerce-producer] ⏳ [ABANDON] {user_id} left cart with {prod['product_id']}")

        time.sleep(interval * 0.2)

    producer.flush()
    print(f"[ecommerce-producer] Emitted {i} clickstream events.")


if __name__ == "__main__":
    count_env = os.getenv("COUNT", "100")
    run(count=None if count_env.lower() == "infinite" else int(count_env))
