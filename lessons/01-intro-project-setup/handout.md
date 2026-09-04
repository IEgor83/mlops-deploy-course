# Занятие 1. Введение в MLOps. Окружение и структура проекта

## Зачем это занятие

Модель, которая работает только на вашем ноутбуке, — это не результат.
Результат — процесс, который любой человек (включая вас через три месяца)
может запустить и получить ту же модель.

Сегодня вы берёте типичный код из ноутбука и превращаете его в то,
что можно запустить одной командой.

## Что должно быть готово

```bash
cd template
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
make install
make check                    # environment: OK
make data                     # data/raw/churn.csv, 20000 строк
```

## Шаг 0. Разбор исходника (10 минут, без кода)

Откройте [`notebooks/baseline_notebook.py`](../../template/notebooks/baseline_notebook.py).
Это рабочий код: он обучает модель и печатает ROC-AUC.

Выпишите в файл `notebooks/PROBLEMS.md` всё, что помешает вам воспроизвести
этот результат на другой машине. Ищите не «некрасиво», а «не воспроизведётся»
или «тихо сломается на новых данных». Минимум семь пунктов.

Не читайте дальше, пока не выписали.

## Шаг 1. Признаки — в конфиг

Откройте `params.yaml`. Секция `features` пустая — заполните её,
разложив колонки датасета по типам:

```yaml
features:
  numeric:
    - tenure_months
    - monthly_charges
    - total_charges
    - num_support_calls
    - avg_monthly_gb
  categorical:
    - contract_type
    - internet_service
    - payment_method
  binary:
    - has_tech_support
    - is_senior
```

`customer_id` в списки не входит: это идентификатор, а не признак.
Модель, обученная на идентификаторе, запоминает конкретных клиентов
вместо закономерности.

Проверьте, что конфиг читается:

```bash
python -c "from src.config import load_params, feature_columns; print(feature_columns(load_params()))"
```

## Шаг 2. Подготовка данных

Реализуйте `src/data/prepare.py`. Требования:

* **Пропуски.** В `total_charges` пропуски у клиентов первого месяца.
  `dropna()` запрещён — это выброс целого сегмента. Заполните осмысленно:
  `monthly_charges * tenure_months`.
* **Сплит.** Сначала отделите тест, затем валидацию от остатка.
  Обязательны `stratify=df["churn"]` и `random_state=params["seed"]`.
* **Сохранение.** Три файла в `data/processed/`: `train.csv`, `val.csv`, `test.csv`.
* **Лог.** Печатайте размер каждой части и долю оттока в ней.

Каркас:

```python
def main() -> None:
    params = load_params()
    d = params["data"]
    raw = pd.read_csv(resolve(d["raw_path"]))
    df = clean(raw)

    train_val, test = train_test_split(
        df, test_size=d["test_size"], random_state=params["seed"], stratify=df["churn"]
    )
    # val_size задан в долях от всего датасета, а отделяем мы его от остатка —
    # поэтому долю нужно пересчитать:
    val_ratio = d["val_size"] / (1.0 - d["test_size"])
    ...
```

Проверка:

```bash
make prepare
wc -l data/processed/*.csv
```

Доля оттока в трёх частях должна совпадать до третьего знака —
это и означает, что `stratify` сработал.

## Шаг 3. Препроцессор

Реализуйте `build_preprocessor` в `src/features.py` через `ColumnTransformer`:

| Тип признаков | Обработка |
|---|---|
| numeric | `SimpleImputer(strategy="median")` → `StandardScaler()` |
| categorical | `SimpleImputer(strategy="most_frequent")` → `OneHotEncoder(handle_unknown="ignore", sparse_output=False)` |
| binary | `"passthrough"` |

Списки колонок берите из `params`, не пишите их в коде.

**Про `handle_unknown="ignore"`.** Завтра в данных появится тариф,
которого не было при обучении. С этим параметром сервис вернёт предсказание;
без него — упадёт с ошибкой в проде. Это не мелочь, а решение об отказоустойчивости.

## Шаг 4. Обучение

Реализуйте `src/train.py`. Ключевое требование — **препроцессор и модель
живут в одном `Pipeline`**:

```python
pipe = Pipeline([
    ("preprocess", build_preprocessor(params)),
    ("model", build_model(params)),
])
pipe.fit(train_df[cols], train_df["churn"])
```

Почему так, а не отдельно: на занятии 10 вы будете принимать JSON от клиента
и отдавать предсказание. Если препроцессинг остался в ноутбуке, его придётся
воспроизвести в сервисе руками — и рано или поздно он разойдётся с обучением.
Это называется training/serving skew и ловится в проде месяцами.

Скрипт должен:

1. прочитать `data/processed/train.csv` и `val.csv`;
2. обучить пайплайн;
3. посчитать на валидации `roc_auc`, `pr_auc`, `f1`;
4. сохранить `models/model.joblib` через `joblib.dump`;
5. записать метрики в `reports/train_metrics.json`;
6. напечатать метрики в лог.

Запуск:

```bash
make train
cat reports/train_metrics.json
```

Ориентир: ROC-AUC около 0.78–0.80. Если сильно меньше — проверьте,
не попал ли `customer_id` в признаки. Если 1.0 — в признаки попал `churn`.

## Шаг 5. Проверка воспроизводимости

```bash
make train && cp reports/train_metrics.json /tmp/first.json
make train && diff /tmp/first.json reports/train_metrics.json && echo "воспроизводится"
```

Если `diff` показал разницу — где-то остался незафиксированный источник
случайности. Найдите его сейчас, на занятии 3 это станет обязательным требованием.

## Что сдать

Коммит в вашем репозитории, содержащий:

- [ ] заполненный `params.yaml` (секция `features`)
- [ ] работающие `src/data/prepare.py`, `src/features.py`, `src/train.py`
- [ ] `notebooks/PROBLEMS.md` — минимум 7 пунктов
- [ ] `reports/train_metrics.json` с ROC-AUC ≥ 0.75

## Домашнее задание (1,5–2 ч)

1. Добавьте в `src/train.py` функцию `build_model(params)`, которая
   по значению `params["train"]["model"]` возвращает `logreg`,
   `random_forest` или `gradient_boosting`. Гиперпараметры каждой —
   отдельной секцией в `params.yaml`.
2. Обучите все три модели, меняя **только** `params.yaml`.
   Занесите результаты в `reports/EXPERIMENTS.md`: модель, параметры, ROC-AUC.
3. Ответьте там же одним абзацем: почему при ROC-AUC около 0.79
   значение F1 получается около 0.39? Что это говорит о пороге 0.5?

Если для смены модели пришлось править код `train.py` в месте, не связанном
с `build_model`, — переделайте: конфиг должен управлять поведением полностью.

## Полезное

* `python -m src.train` — запуск модуля; `python src/train.py` сломает импорты
* `make help` — список доступных команд
* Метрики: ROC-AUC устойчив к дисбалансу классов, F1 — нет. Об этом ещё поговорим
