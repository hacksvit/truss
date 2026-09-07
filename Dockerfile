FROM node:22-bookworm-slim AS frontend
WORKDIR /build/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.14-slim-bookworm
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRUSS_CONFIG_DIR=/app/config \
    TRUSS_WEB_DIST=/app/web/dist \
    TRUSS_RUNTIME_ROOT=/tmp/truss-runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends mosquitto \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.lock pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.lock
COPY src/ ./src/
RUN pip install --no-cache-dir --no-deps .
COPY config/ ./config/
COPY --from=frontend /build/web/dist ./web/dist
RUN useradd --create-home truss
USER truss
CMD ["python", "-m", "truss.hosted"]
