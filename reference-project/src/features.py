"""Построение препроцессора признаков.

Ключевое требование MLOps: препроцессинг едет вместе с моделью внутри одного
sklearn.Pipeline. Если масштабирование и кодирование живут в ноутбуке отдельно
от модели, сервис на проде получит другие числа — это самый частый
training/serving skew.
"""
from __future__ import annotations

from typing import Any

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_preprocessor(params: dict[str, Any]) -> ColumnTransformer:
    f = params["features"]

    numeric = Pipeline(
        [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    )
    categorical = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            # handle_unknown='ignore' — на проде обязательно: новая категория
            # не должна ронять сервис 500-й ошибкой.
            ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric, list(f["numeric"])),
            ("cat", categorical, list(f["categorical"])),
            ("bin", "passthrough", list(f["binary"])),
        ],
        remainder="drop",
    )
