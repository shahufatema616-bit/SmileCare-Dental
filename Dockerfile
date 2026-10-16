FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ALLOW_ALL_HOSTS=true \
    SQLITE_PATH=/app/data/db.sqlite3

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/seed \
    && if [ -f /app/db.sqlite3 ]; then cp /app/db.sqlite3 /app/seed/demo.sqlite3; fi \
    && if [ -f /app/seed/demo.sqlite3 ]; then true; elif [ -f /app/db.sqlite3 ]; then cp /app/db.sqlite3 /app/seed/demo.sqlite3; fi \
    && chmod +x /app/docker/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
