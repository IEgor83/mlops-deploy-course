"""Общие фикстуры. Тесты не должны зависеть от того, что кто-то заранее
запустил пайплайн: данные для тестов генерируются на лету и живут в tmp.
"""
from __future__ import annotations

import pytest

from src.config import feature_columns, load_params
from src.data.generate import generate


@pytest.fixture(scope="session")
def params():
    return load_params()


@pytest.fixture(scope="session")
def raw_df():
    return generate(n=2000, seed=7)


@pytest.fixture(scope="session")
def cols(params):
    return feature_columns(params)


@pytest.fixture(scope="session")
def trained_pipeline(params, raw_df, cols):
    """Обучаем один раз на сессию: обучение медленное, а тестов много."""
    from src.data.prepare import clean
    from src.train import build_pipeline

    df = clean(raw_df)
    pipe = build_pipeline(params)
    pipe.fit(df[cols], df["churn"])
    return pipe
