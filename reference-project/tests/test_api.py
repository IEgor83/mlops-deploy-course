"""Тесты HTTP-контракта. Проверяем границу системы: коды ответов,
валидацию и то, что в ответе есть версия модели.
"""
from __future__ import annotations

import joblib
import pytest
from fastapi.testclient import TestClient

VALID = {
    "tenure_months": 3,
    "monthly_charges": 89.4,
    "total_charges": 268.2,
    "contract_type": "month-to-month",
    "internet_service": "fiber",
    "payment_method": "electronic_check",
    "num_support_calls": 4,
    "has_tech_support": 0,
    "is_senior": 0,
    "avg_monthly_gb": 61.3,
}


@pytest.fixture(scope="module")
def client(tmp_path_factory, trained_pipeline):
    """Подсовываем сервису обученную в тестах модель: тесты API не должны
    зависеть от того, лежит ли в models/ артефакт с прошлого запуска."""
    path = tmp_path_factory.mktemp("model") / "model.joblib"
    joblib.dump(trained_pipeline, path)

    from src.service import app as app_module

    app_module.holder.model = joblib.load(path)
    app_module.holder.version = "test:fixture"
    with TestClient(app_module.app) as c:
        yield c


def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_predict_returns_valid_probability(client):
    r = client.post("/predict", json=VALID)
    assert r.status_code == 200
    body = r.json()
    assert 0.0 <= body["churn_probability"] <= 1.0
    assert body["churn"] in (0, 1)
    assert body["model_version"], "версия модели обязана быть в ответе"


def test_missing_field_returns_422(client):
    payload = {k: v for k, v in VALID.items() if k != "contract_type"}
    assert client.post("/predict", json=payload).status_code == 422


def test_out_of_range_value_returns_422(client):
    payload = dict(VALID, tenure_months=-5)
    assert client.post("/predict", json=payload).status_code == 422


def test_unknown_category_returns_422(client):
    """Литеральный тип в схеме ловит опечатку в категории до модели."""
    payload = dict(VALID, contract_type="lifetime")
    assert client.post("/predict", json=payload).status_code == 422


def test_batch_predict(client):
    r = client.post("/predict/batch", json={"items": [VALID, dict(VALID, tenure_months=60)]})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    assert len(body["predictions"]) == 2


def test_empty_batch_returns_422(client):
    assert client.post("/predict/batch", json={"items": []}).status_code == 422


def test_metrics_endpoint_exposes_prometheus_format(client):
    client.post("/predict", json=VALID)
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "prediction_requests_total" in r.text
