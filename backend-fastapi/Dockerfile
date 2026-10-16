FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .

ENV ENABLE_LEGALBERT=false
ENV LEGALBERT_ENABLED=false
ENV SBERT_MODEL=sentence-transformers/all-MiniLM-L6-v2
ENV HF_HOME=/app/models
ENV TRANSFORMERS_CACHE=/app/models

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]