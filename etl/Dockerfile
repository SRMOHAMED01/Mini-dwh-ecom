FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create producers directory (ensure __init__.py exists for package imports)
RUN mkdir -p producers && touch producers/__init__.py

# Default: run ETL pipeline
CMD ["python", "main.py"]