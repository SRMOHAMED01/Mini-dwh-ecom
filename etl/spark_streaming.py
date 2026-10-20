"""
Spark Structured Streaming consumer

Reads from Kafka, aggregates events in tumbling windows, and writes
the results to PostgreSQL (dwh.fact_streaming_kpis).

Run with:
    spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 spark_streaming.py
"""
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, window, count, sum as spark_sum, avg,
    current_timestamp, date_format
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType
)
from pyspark.sql.functions import lit, concat

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_PRODUCTS = os.getenv("KAFKA_TOPIC_PRODUCTS", "amazon.products")
TOPIC_EVENTS = os.getenv("KAFKA_TOPIC_EVENTS", "ecommerce.events")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "dwh_user")
DB_PASS = os.getenv("DB_PASS", "12345")
DB_NAME = os.getenv("DB_NAME", "ecommerce_dwh")
JDBC_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"
PROPS = {"user": DB_USER, "password": DB_PASS, "driver": "org.postgresql.Driver"}

PRODUCT_SCHEMA = StructType([
    StructField("product_id", StringType(), True),
    StructField("product_name", StringType(), True),
    StructField("category", StringType(), True),
    StructField("category_full", StringType(), True),
    StructField("actual_price", DoubleType(), True),
    StructField("discounted_price", DoubleType(), True),
    StructField("discount_pct", DoubleType(), True),
    StructField("rating", DoubleType(), True),
    StructField("rating_count", IntegerType(), True),
    StructField("img_link", StringType(), True),
    StructField("product_link", StringType(), True),
    StructField("source", StringType(), True),
    StructField("event_time", StringType(), True),
])

EVENT_SCHEMA = StructType([
    StructField("event_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("session_id", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("category", StringType(), True),
    StructField("price", DoubleType(), True),
    StructField("quantity", IntegerType(), True),
    StructField("event_time", StringType(), True),
    StructField("source", StringType(), True),
])


def main():
    spark = (
        SparkSession.builder
        .appName("EcommerceStreamingDWH")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # ── Product catalog stream ─────────────────────────────────────────────
    products_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC_PRODUCTS)
        .option("startingOffsets", "latest")
        .load()
        .select(from_json(col("value").cast("string"), PRODUCT_SCHEMA).alias("data"))
        .select("data.*")
    )

    product_agg = (
        products_df
        .withWatermark("event_time", "30 seconds")
        .groupBy(
            window(col("event_time"), "30 seconds"),
            col("category"),
        )
        .agg(count("*").alias("product_count"))
        .select(
            col("window.start").alias("window_start"),
            lit("products_by_category").alias("metric"),
            col("category").alias("key"),
            col("product_count").alias("value"),
        )
    )

    # ── Website events stream ──────────────────────────────────────────────
    events_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC_EVENTS)
        .option("startingOffsets", "latest")
        .load()
        .select(from_json(col("value").cast("string"), EVENT_SCHEMA).alias("data"))
        .select("data.*")
    )

    event_agg = (
        events_df
        .withWatermark("event_time", "30 seconds")
        .groupBy(
            window(col("event_time"), "30 seconds"),
            col("event_type"),
        )
        .agg(count("*").alias("event_count"))
        .select(
            col("window.start").alias("window_start"),
            concat(lit("events_"), col("event_type")).alias("metric"),
            col("event_type").alias("key"),
            col("event_count").alias("value"),
        )
    )

    revenue_agg = (
        events_df
        .filter(col("event_type") == "purchase")
        .withWatermark("event_time", "30 seconds")
        .groupBy(
            window(col("event_time"), "30 seconds"),
            col("category"),
        )
        .agg((spark_sum(col("price") * col("quantity"))).alias("revenue"))
        .select(
            col("window.start").alias("window_start"),
            lit("revenue_by_category").alias("metric"),
            col("category").alias("key"),
            col("revenue").alias("value"),
        )
    )

    combined = product_agg.union(event_agg).union(revenue_agg)

    (
        combined
        .writeStream
        .outputMode("update")
        .option("checkpointLocation", "/tmp/spark-checkpoints")
        .foreachBatch(lambda df, batch_id -> df.write
                      .format("jdbc")
                      .option("url", JDBC_URL)
                      .option("table", "dwh.fact_streaming_kpis")
                      .option("user", DB_USER)
                      .option("password", DB_PASS)
                      .driver("org.postgresql.Driver")
                      .mode("append")
                      .save())
        .start()
        .awaitTermination()
    )


if __name__ == "__main__":
    from pyspark.sql.functions import lit, concat
    main()