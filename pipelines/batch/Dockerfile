FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download VADER lexicon during image build
RUN python -c "import nltk; nltk.download('vader_lexicon')"

# Copy source code
COPY . .

# Run batch ETL by default
CMD ["python", "main.py"]
