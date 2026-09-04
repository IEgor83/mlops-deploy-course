"""Поведенческие тесты модели.

Отличие от юнит-тестов бэкенда: мы не можем проверить точное значение выхода.
Проверяем свойства, которые обязаны выполняться у любой адекватной модели
этой задачи — минимальное качество, диапазон выходов, направление реакции
на изменение признака и устойчивость к перестановке строк.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import TARGET
from src.data.prepare import clean
from src.train import compute_metrics


def _holdout(raw_df, cols):
    df = clean(raw_df)
    return df.tail(400)[cols], df.tail(400)[TARGET]


def test_model_beats_quality_gate(trained_pipeline, raw_df, cols, params):
    X, y = _holdout(raw_df, cols)
    proba = trained_pipeline.predict_proba(X)[:, 1]
    metrics = compute_metrics(y, proba, params["evaluate"]["threshold"])
    assert metrics["roc_auc"] > 0.70, f"модель слабее порога: {metrics}"


def test_probabilities_are_valid(trained_pipeline, raw_df, cols):
    X, _ = _holdout(raw_df, cols)
    proba = trained_pipeline.predict_proba(X)[:, 1]
    assert ((proba >= 0) & (proba <= 1)).all()
    assert proba.std() > 0.01, "модель выдаёт почти константу — признак сломанного обучения"


def test_more_support_calls_increase_churn_risk(trained_pipeline, raw_df, cols):
    """Направленный тест: чем больше обращений в поддержку, тем выше риск ухода.
    Если это правило нарушено — где-то перепутаны признаки или таргет."""
    base = clean(raw_df)[cols].head(200).copy()
    calm = base.copy()
    calm.loc[:, "num_support_calls"] = 0
    angry = base.copy()
    angry.loc[:, "num_support_calls"] = 8

    assert trained_pipeline.predict_proba(angry)[:, 1].mean() > trained_pipeline.predict_proba(calm)[:, 1].mean()


def test_long_contract_reduces_churn_risk(trained_pipeline, raw_df, cols):
    base = clean(raw_df)[cols].head(200).copy()
    monthly = base.copy()
    monthly.loc[:, "contract_type"] = "month-to-month"
    yearly = base.copy()
    yearly.loc[:, "contract_type"] = "two_year"

    assert trained_pipeline.predict_proba(yearly)[:, 1].mean() < trained_pipeline.predict_proba(monthly)[:, 1].mean()


def test_prediction_is_row_independent(trained_pipeline, raw_df, cols):
    """Предсказание для строки не должно зависеть от соседей в батче:
    иначе батч-режим и одиночный /predict дадут разные ответы."""
    X, _ = _holdout(raw_df, cols)
    single = trained_pipeline.predict_proba(X.head(1))[:, 1][0]
    in_batch = trained_pipeline.predict_proba(X.head(50))[:, 1][0]
    assert abs(single - in_batch) < 1e-9


def test_training_is_reproducible(params, raw_df, cols):
    """Дважды обученная на одних данных модель обязана дать одинаковые предсказания."""
    from src.train import build_pipeline

    df = clean(raw_df)
    preds = []
    for _ in range(2):
        pipe = build_pipeline(params)
        pipe.fit(df[cols], df[TARGET])
        preds.append(pipe.predict_proba(df.head(100)[cols])[:, 1])
    np.testing.assert_allclose(preds[0], preds[1])


def test_model_handles_single_row_dataframe(trained_pipeline, raw_df, cols):
    row = clean(raw_df)[cols].head(1)
    assert trained_pipeline.predict_proba(row).shape == (1, 2)


def test_no_target_leakage_in_features(cols):
    """Таргет не должен попасть в признаки — банально, но случается регулярно."""
    assert TARGET not in cols
    assert "customer_id" not in cols, "идентификатор клиента не признак"


def test_empty_frame_raises(trained_pipeline, cols):
    empty = pd.DataFrame(columns=cols)
    try:
        trained_pipeline.predict_proba(empty)
    except Exception:
        return  # ожидаемое поведение
    # если не упало — результат должен быть пустым, а не мусорным
    assert len(trained_pipeline.predict_proba(empty)) == 0
