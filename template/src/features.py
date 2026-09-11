"""Построение препроцессора признаков.

Требования:
  * числовые признаки: заполнение пропусков + масштабирование;
  * категориальные: заполнение пропусков + OneHotEncoder;
  * бинарные: без изменений;
  * списки колонок берутся из params.yaml, а не пишутся в коде.

Подсказка: почему препроцессор обязан ехать в одном Pipeline с моделью,
разбирается на паре. Если сделать иначе — сервис на занятии 10 сломается.
"""
from __future__ import annotations

from typing import Any

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_preprocessor(params: dict[str, Any]) -> ColumnTransformer:
    """Собирает ColumnTransformer для разных типов признаков.

    | Тип признаков | Обработка |
    |---|---|
    | numeric | SimpleImputer(strategy="median") -> StandardScaler() |
    | categorical | SimpleImputer(strategy="most_frequent") -> OneHotEncoder(handle_unknown="ignore") |
    | binary | "passthrough" |
    """
    f = params["features"]

    # Для числовых: заполнение пропусков медианой + масштабирование
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])

    # Для категориальных: заполнение пропусков модой + OneHot
    # handle_unknown="ignore" важен: если на сервере появится новая категория,
    # сервис не упадёт, а вернёт нули
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    # Собираем всё вместе
    preprocessor = ColumnTransformer([
        ("num", numeric_pipe, f["numeric"]),
        ("cat", categorical_pipe, f["categorical"]),
        ("bin", "passthrough", f["binary"]),  # бинарные не обрабатываем
    ])

    return preprocessor
