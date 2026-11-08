# Занятие 8. Тестирование ML-систем

## Проблема

В обычном коде ошибка приводит к исключению. В ML-коде ошибка приводит
к правильно оформленному неправильному ответу.

Пример, который вы только что видели: сдвиг таргета на одну строку.
Пайплайн отработал, модель сохранилась, метрики записались, всё зелёное.
Модель бесполезна, и узнают об этом через месяц по жалобам из бизнеса.

Сегодня строим защиту.

## Что тестируем

| Группа | Вопрос, на который отвечает |
|---|---|
| Данные | пришло ли то, что мы ожидаем |
| Препроцессинг | корректно ли обработаны граничные случаи |
| Поведение модели | осмысленна ли модель как модель предметной области |
| Контракт API | правильно ли сервис реагирует на некорректный вход |

## Шаг 1. Фикстуры

Создайте `tests/conftest.py`. Главное требование: **тесты не должны
зависеть от того, запускал ли кто-то пайплайн**.

```python
@pytest.fixture(scope="session")
def raw_df():
    return generate(n=2000, seed=7)


@pytest.fixture(scope="session")
def trained_pipeline(params, raw_df, cols):
    """scope='session' обязателен: обучение медленное, а тестов много."""
    df = clean(raw_df)
    pipe = build_pipeline(params)
    pipe.fit(df[cols], df["churn"])
    return pipe
```

Без `scope="session"` модель будет обучаться заново на каждый тест,
и прогон займёт минуты вместо секунд.

## Шаг 2. Тесты данных

`tests/test_data.py`:

```python
def test_schema_is_complete(raw_df, params):
    """Все колонки из params.yaml есть в данных."""
    missing = set(feature_columns(params) + [TARGET]) - set(raw_df.columns)
    assert not missing, f"в датасете нет колонок: {missing}"


def test_target_is_not_degenerate(raw_df):
    """Защита от 'все нули': такой датасет даст accuracy 0.9 и бесполезную модель."""
    rate = raw_df[TARGET].mean()
    assert 0.05 < rate < 0.60, f"подозрительный churn rate: {rate:.3f}"


def test_generation_is_reproducible():
    a, b = generate(n=500, seed=123), generate(n=500, seed=123)
    pd.testing.assert_frame_equal(a, b)
```

Допишите сами: проверку диапазонов значений (`tenure_months`, `monthly_charges`,
`num_support_calls`), проверку что `clean()` убирает пропуски,
проверку детерминированности сплита.

## Шаг 3. Тесты препроцессинга

`tests/test_features.py`. Два теста здесь важнее остальных:

```python
def test_unknown_category_does_not_crash(params, raw_df, cols):
    """На проде рано или поздно придёт категория, которой не было в обучении.
    Сервис обязан ответить предсказанием, а не 500-й ошибкой."""
    df = clean(raw_df)[cols]
    pre = build_preprocessor(params).fit(df)
    unseen = df.head(1).copy()
    unseen.loc[:, "contract_type"] = "lifetime"
    assert pre.transform(unseen).shape[0] == 1


def test_column_order_does_not_matter(params, raw_df, cols):
    """ColumnTransformer выбирает колонки по имени. Проверяем, что это правда:
    иначе клиент, приславший поля в другом порядке, получит мусор."""
    df = clean(raw_df)[cols]
    pre = build_preprocessor(params).fit(df)
    shuffled = df.head(10)[list(reversed(cols))]
    np.testing.assert_allclose(pre.transform(df.head(10)), pre.transform(shuffled))
```

## Шаг 4. Поведенческие тесты модели

Здесь главное отличие от обычного тестирования. Мы не знаем, каким должно
быть предсказание для конкретного клиента. Но мы знаем свойства,
которые обязана иметь любая адекватная модель этой задачи.

`tests/test_model.py`:

```python
def test_more_support_calls_increase_churn_risk(trained_pipeline, raw_df, cols):
    """Направленный тест: больше обращений в поддержку -> выше риск ухода.
    Нарушение означает перепутанные признаки или таргет."""
    base = clean(raw_df)[cols].head(200).copy()
    calm, angry = base.copy(), base.copy()
    calm.loc[:, "num_support_calls"] = 0
    angry.loc[:, "num_support_calls"] = 8

    assert (trained_pipeline.predict_proba(angry)[:, 1].mean()
            > trained_pipeline.predict_proba(calm)[:, 1].mean())


def test_probabilities_are_valid(trained_pipeline, raw_df, cols):
    proba = trained_pipeline.predict_proba(clean(raw_df).tail(400)[cols])[:, 1]
    assert ((proba >= 0) & (proba <= 1)).all()
    assert proba.std() > 0.01, "модель выдаёт почти константу — признак сломанного обучения"


def test_prediction_is_row_independent(trained_pipeline, raw_df, cols):
    """Предсказание для строки не зависит от соседей в батче.
    Иначе /predict и /predict/batch дадут разные ответы для одного клиента."""
    X = clean(raw_df).tail(400)[cols]
    assert abs(trained_pipeline.predict_proba(X.head(1))[:, 1][0]
               - trained_pipeline.predict_proba(X.head(50))[:, 1][0]) < 1e-9
```

Допишите сами:
* длинный контракт снижает риск оттока;
* модель проходит порог качества (`roc_auc > 0.70` — чуть ниже вашего
  реального результата, чтобы тест не мигал);
* повторное обучение на тех же данных даёт те же предсказания;
* `churn` и `customer_id` отсутствуют в списке признаков.

**Про порог в тесте.** Не ставьте `assert roc_auc > 0.79`, если у вас
получилось ровно 0.79: тест начнёт падать от смены версии библиотеки.
Порог должен ловить катастрофу (0.5), а не колебания в третьем знаке.

## Шаг 5. Проверка на живой поломке

Внесите в `src/data/prepare.py` эту строку:

```python
df["churn"] = df["churn"].shift(1).fillna(0).astype(int)
```

```bash
pytest
```

Какие тесты покраснели? Если ни один — ваши тесты не защищают проект.
Подумайте, какого теста не хватает, добавьте его, убедитесь, что он ловит
поломку, и **уберите строку обратно**.

## Шаг 6. Оформление

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers"
```

`Makefile`:

```make
test:            ## Прогнать тесты
	pytest
```

## Шаг 7. Два теста, которых обычно не пишут

### Метаморфный тест

Направленные тесты вы уже написали: больше жалоб — выше риск.
Метаморфный проверяет другое свойство: **преобразование входа,
не меняющее смысла, не должно менять ответ**.

```python
def test_duplicate_row_does_not_change_prediction(trained_pipeline, raw_df, cols):
    """Один и тот же клиент, поданный дважды, получает одинаковый ответ.
    Нарушение означает, что модель смотрит на позицию строки в батче."""
    row = clean(raw_df)[cols].head(1)
    doubled = pd.concat([row, row], ignore_index=True)
    proba = trained_pipeline.predict_proba(doubled)[:, 1]
    assert abs(proba[0] - proba[1]) < 1e-12
```

Придумайте и добавьте ещё один метаморфный тест. Варианты:
перестановка колонок, добавление лишней колонки, которой нет
в `feature_columns`, масштабирование денежных величин из рублей
в копейки с одновременной правкой конфига.

### Тест производительности

Качество вы проверяете. Скорость — нет. А на занятии 14 у вас появится
алерт на p95 latency, и хорошо бы ловить регрессию раньше.

```python
def test_batch_inference_is_fast_enough(trained_pipeline, raw_df, cols):
    """1000 объектов должны считаться быстрее секунды.
    Порог с запасом: ловим катастрофу (кто-то вызвал fit в predict),
    а не колебания на разных машинах."""
    batch = clean(raw_df)[cols].sample(1000, replace=True, random_state=0)
    start = time.perf_counter()
    trained_pipeline.predict_proba(batch)
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, f"инференс 1000 строк занял {elapsed:.2f} с"
```

**Про порог.** Он должен ловить поломку, а не разницу между вашим ноутбуком
и раннером CI. Секунда на тысячу строк — запас примерно в сто раз.
Если поставить 0.05, тест начнёт мигать, и его отключат.

Пометьте медленные тесты маркером, чтобы их можно было пропускать локально:

```python
@pytest.mark.slow
```

## Что сдать

- [ ] ≥ 8 тестов в трёх файлах: `test_data.py`, `test_features.py`, `test_model.py`
- [ ] Есть тест на схему данных и минимум два поведенческих теста
- [ ] `make test` зелёный и идёт менее 60 секунд
- [ ] Показано, что тесты ловят сдвиг таргета
- [ ] Два метаморфных теста (один из методички, один свой)
- [ ] Тест производительности инференса с обоснованным порогом

## Домашнее задание (1,5–2 ч)

1. Доведите число тестов до 12+, добавив проверки на дубликаты,
   утечку таргета в признаки и корректную работу на датафрейме из одной строки.
2. Добавьте измерение покрытия: `pytest --cov=src --cov-report=term-missing`.
   Занесите цифру в `README.md`. Гнаться за 100 % не нужно — объясните
   там же, какие части кода покрывать бессмысленно и почему.
3. Придумайте и реализуйте один поведенческий тест, которого нет
   в методичке. Опишите в докстринге, какую именно поломку он ловит.

## Полезное

| Команда | Зачем |
|---|---|
| `pytest -q` | кратко |
| `pytest -k имя` | только подходящие по имени |
| `pytest -x` | остановиться на первом падении |
| `pytest --lf` | перезапустить только упавшие |
| `pytest --durations=5` | пять самых медленных тестов |
