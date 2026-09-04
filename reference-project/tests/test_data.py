"""Тесты данных. Проверяем не модель, а то, что в неё попадает:
битые данные — самая частая причина тихой деградации прода.
"""
from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import TARGET, feature_columns
from src.data.generate import generate
from src.data.prepare import clean


def test_schema_is_complete(raw_df, params):
    """Все колонки, объявленные в params.yaml, действительно есть в данных."""
    missing = set(feature_columns(params) + [TARGET]) - set(raw_df.columns)
    assert not missing, f"в датасете нет колонок: {missing}"


def test_value_ranges(raw_df):
    assert raw_df["tenure_months"].between(0, 200).all()
    assert raw_df["monthly_charges"].between(0, 1000).all()
    assert raw_df["num_support_calls"].ge(0).all()
    assert raw_df[TARGET].isin([0, 1]).all()


def test_target_is_not_degenerate(raw_df):
    """Защита от катастрофы 'все нули': такой датасет даст accuracy 0.9 и бесполезную модель."""
    rate = raw_df[TARGET].mean()
    assert 0.05 < rate < 0.60, f"подозрительный churn rate: {rate:.3f}"


def test_clean_fills_total_charges(raw_df):
    assert raw_df["total_charges"].isna().any(), "фикстура должна содержать пропуски"
    cleaned = clean(raw_df)
    assert not cleaned["total_charges"].isna().any()


def test_generation_is_reproducible():
    """Один seed -> побайтово одинаковые данные. Без этого нет воспроизводимости пайплайна."""
    a = generate(n=500, seed=123)
    b = generate(n=500, seed=123)
    pd.testing.assert_frame_equal(a, b)


def test_drift_data_differs_from_reference():
    """Дрейфовый срез обязан отличаться — иначе занятие 15 не покажет ничего."""
    ref = generate(n=3000, seed=1)
    cur = generate(n=3000, seed=1001, drift=True)
    assert cur["monthly_charges"].mean() > ref["monthly_charges"].mean() + 3


def test_split_is_deterministic(raw_df, params):
    seed = params["seed"]
    first = train_test_split(raw_df, test_size=0.2, random_state=seed, stratify=raw_df[TARGET])[1]
    second = train_test_split(raw_df, test_size=0.2, random_state=seed, stratify=raw_df[TARGET])[1]
    assert list(first["customer_id"]) == list(second["customer_id"])
