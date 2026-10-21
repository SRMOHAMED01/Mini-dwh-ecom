FROM bitnami/spark:3.5

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add Spark Kafka connector jar
RUN SPARK_JAR_DIR=/opt/bitnami/spark/jars \
    && curl -L -o "$SPARK_JAR_DIR/spark-sql-kafka-0-10_2.12-3.5.0.jar" \
      "https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.0/spark-sql-kafka-0-10_2.12-3.5.0.jar"

COPY . .

CMD ["spark-submit", "spark_streaming.py"]