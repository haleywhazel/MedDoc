FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    poppler-utils \
    tesseract-ocr \
    libreoffice \
    pandoc \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/logs /app/local

COPY ./scripts/wait-for-chroma.sh /app/
RUN chmod +x /app/wait-for-chroma.sh

CMD ["./wait-for-chroma.sh", "python", "backend/ingestion/ingest.py"]
