"""REST-сервис инференса.

Занятие 10 — эндпоинты и валидация, занятие 14 — метрики и логи.
Здесь итоговое состояние: то, что студент собирает за две пары.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from src.config import feature_columns, load_params
from src.logging_setup import setup_logging
from src.service.model_loader import holder
from src.service.schemas import (
    BatchPrediction,
    BatchRequest,
    Customer,
    HealthResponse,
    Prediction,
)

log = setup_logging()

REQUESTS = Counter("prediction_requests_total", "Число запросов предсказания", ["endpoint", "status"])
LATENCY = Histogram(
    "prediction_latency_seconds",
    "Время обработки запроса предсказания",
    ["endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)
# Гистограмма самих предсказаний — дешёвый детектор дрейфа прямо в проде:
# сдвиг распределения вероятностей виден на дашборде раньше, чем упадут метрики.
PROBA = Histogram(
    "prediction_probability",
    "Распределение предсказанных вероятностей оттока",
    buckets=[i / 10 for i in range(11)],
)
MODEL_LOADED = Gauge("model_loaded", "1 — модель загружена, 0 — нет")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Модель грузится один раз на старте, а не на каждый запрос:
    # иначе p95 latency будет измеряться секундами.
    try:
        holder.load()
        MODEL_LOADED.set(1)
    except Exception as exc:  # noqa: BLE001
        log.error("не удалось загрузить модель: %s", exc)
        MODEL_LOADED.set(0)
    yield


app = FastAPI(
    title="Churn Prediction Service",
    version="1.0.0",
    description="Учебный сервис курса MLOps: предсказание оттока клиентов",
    lifespan=lifespan,
)


def _predict_frame(df: pd.DataFrame, threshold: float):
    if not holder.loaded:
        raise HTTPException(status_code=503, detail="Модель не загружена")
    proba = holder.model.predict_proba(df)[:, 1]
    return [
        Prediction(
            churn_probability=round(float(p), 6),
            churn=int(p >= threshold),
            threshold=threshold,
            model_version=holder.version,
        )
        for p in proba
    ]


@app.get("/health", response_model=HealthResponse, tags=["service"])
def health() -> HealthResponse:
    """Жив ли процесс и загружена ли модель. Используется healthcheck'ом в compose."""
    return HealthResponse(
        status="ok" if holder.loaded else "degraded",
        model_loaded=holder.loaded,
        model_version=holder.version,
    )


@app.post("/predict", response_model=Prediction, tags=["inference"])
def predict(customer: Customer) -> Prediction:
    params = load_params()
    threshold = params["evaluate"]["threshold"]
    start = time.perf_counter()
    try:
        df = pd.DataFrame([customer.model_dump()])[feature_columns(params)]
        result = _predict_frame(df, threshold)[0]
        PROBA.observe(result.churn_probability)
        REQUESTS.labels("predict", "ok").inc()
        return result
    except HTTPException:
        REQUESTS.labels("predict", "error").inc()
        raise
    except Exception as exc:  # noqa: BLE001
        REQUESTS.labels("predict", "error").inc()
        log.exception("ошибка предсказания")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        LATENCY.labels("predict").observe(time.perf_counter() - start)


@app.post("/predict/batch", response_model=BatchPrediction, tags=["inference"])
def predict_batch(request: BatchRequest) -> BatchPrediction:
    params = load_params()
    threshold = params["evaluate"]["threshold"]
    start = time.perf_counter()
    try:
        df = pd.DataFrame([i.model_dump() for i in request.items])[feature_columns(params)]
        preds = _predict_frame(df, threshold)
        for p in preds:
            PROBA.observe(p.churn_probability)
        REQUESTS.labels("predict_batch", "ok").inc()
        return BatchPrediction(predictions=preds, count=len(preds))
    except HTTPException:
        REQUESTS.labels("predict_batch", "error").inc()
        raise
    finally:
        LATENCY.labels("predict_batch").observe(time.perf_counter() - start)


@app.post("/reload", tags=["service"])
def reload_model() -> dict:
    """Подтянуть новую версию модели без рестарта контейнера.
    Нужен на занятии 16: пайплайн переобучения промоутит модель и дёргает /reload."""
    holder.load()
    MODEL_LOADED.set(1 if holder.loaded else 0)
    return {"status": "reloaded", "model_version": holder.version}


@app.get("/metrics", tags=["service"])
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    log.info(
        "%s %s -> %s за %.1f мс",
        request.method,
        request.url.path,
        response.status_code,
        (time.perf_counter() - start) * 1000,
    )
    return response
