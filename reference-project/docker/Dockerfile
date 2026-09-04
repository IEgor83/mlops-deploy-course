# Multi-stage: тяжёлая сборка колёс отдельно, в финальный образ едет
# только рантайм. Разница на этом проекте — примерно 1.2 ГБ против 380 МБ.

# ---------- стадия сборки ----------
FROM python:3.11-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Только рантайм-зависимости сервиса: mlflow/dvc/prefect в образ инференса
# не нужны — это лишние сотни мегабайт и лишняя поверхность атаки.
COPY docker/requirements-service.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-service.txt

# ---------- финальный образ ----------
FROM python:3.11-slim AS runtime

# Процесс не должен работать от root: если сервис скомпрометируют,
# у злоумышленника не будет прав внутри контейнера.
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app
COPY --from=builder /install /usr/local

COPY src/ ./src/
COPY params.yaml ./params.yaml
COPY models/ ./models/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import httpx,sys; sys.exit(0 if httpx.get('http://localhost:8000/health').json()['model_loaded'] else 1)"

CMD ["uvicorn", "src.service.app:app", "--host", "0.0.0.0", "--port", "8000"]
