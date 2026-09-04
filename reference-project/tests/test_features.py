"""Тесты препроцессинга: он едет в прод вместе с моделью, значит тестируется как код."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.data.prepare import clean
from src.features import build_preprocessor


def test_preprocessor_output_has_no_nan(params, raw_df, cols):
    pre = build_preprocessor(params)
    X = pre.fit_transform(clean(raw_df)[cols])
    assert not np.isnan(X).any(), "после препроцессинга не должно остаться NaN"


def test_unknown_category_does_not_crash(params, raw_df, cols):
    """На проде рано или поздно придёт категория, которой не было в обучении.
    Сервис обязан ответить предсказанием, а не 500-й ошибкой."""
    df = clean(raw_df)[cols]
    pre = build_preprocessor(params).fit(df)

    unseen = df.head(1).copy()
    unseen.loc[:, "contract_type"] = "lifetime"   # категории не было в train
    assert pre.transform(unseen).shape[0] == 1


def test_missing_numeric_is_imputed(params, raw_df, cols):
    df = clean(raw_df)[cols]
    pre = build_preprocessor(params).fit(df)

    row = df.head(1).copy()
    row.loc[:, "avg_monthly_gb"] = np.nan
    assert not np.isnan(pre.transform(row)).any()


def test_column_order_does_not_matter(params, raw_df, cols):
    """ColumnTransformer выбирает колонки по имени — проверяем, что это правда.
    Иначе клиент, приславший поля в другом порядке, получит мусор."""
    df = clean(raw_df)[cols]
    pre = build_preprocessor(params).fit(df)

    shuffled = df.head(10)[list(reversed(cols))]
    np.testing.assert_allclose(pre.transform(df.head(10)), pre.transform(shuffled))


def test_transform_is_stateless_across_calls(params, raw_df, cols):
    df = clean(raw_df)[cols]
    pre = build_preprocessor(params).fit(df)
    first = pre.transform(df.head(50))
    _ = pre.transform(df.tail(50))
    np.testing.assert_allclose(first, pre.transform(df.head(50)))


def test_dataframe_shape_is_preserved(params, raw_df, cols):
    pre = build_preprocessor(params)
    df = clean(raw_df)[cols]
    X = pre.fit_transform(df)
    assert isinstance(df, pd.DataFrame)
    assert X.shape[0] == len(df)
