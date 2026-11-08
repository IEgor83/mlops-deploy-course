# Занятие 5. Пайплайны DVC

## Проблема

Сейчас ваш проект запускается так:

```bash
make data && make prepare && make train && make eval
```

Три вопроса к этой строке:

1. Вы поменяли только `learning_rate` — зачем заново генерировать данные?
2. Вы вернулись к проекту через месяц — какие шаги нужно перезапустить?
3. Коллега поменял `prepare.py` — он не забудет переобучить модель?

Сегодня описываем пайплайн как граф: DVC сам определит, что устарело.

## Шаг 1. Первая стадия

Создайте `dvc.yaml` в корне проекта:

```yaml
stages:
  generate:
    cmd: python -m src.data.generate
    deps:
      - src/data/generate.py
    params:
      - seed
      - data.n_samples
    outs:
      - data/raw/churn.csv
```

Разберём поля:

| Поле | Смысл |
|---|---|
| `cmd` | что запустить |
| `deps` | файлы, при изменении которых стадию нужно перезапустить |
| `params` | ключи из `params.yaml`, от которых зависит стадия |
| `outs` | что стадия производит — DVC берёт это под управление |

Поскольку выход теперь описан в `dvc.yaml`, старый `.dvc`-файл лишний:

```bash
dvc remove data/raw/churn.csv.dvc
dvc repro
```

## Шаг 2. Остальные стадии

Допишите три стадии. Обратите внимание, как выход одной становится
входом следующей — именно так DVC строит граф.

```yaml
  prepare:
    cmd: python -m src.data.prepare
    deps:
      - src/data/prepare.py
      - data/raw/churn.csv
    params:
      - seed
      - data.test_size
      - data.val_size
    outs:
      - data/processed/train.csv
      - data/processed/val.csv
      - data/processed/test.csv

  train:
    cmd: python -m src.train
    deps:
      - src/train.py
      - src/features.py
      - data/processed/train.csv
      - data/processed/val.csv
    params:
      - seed
      - features
      - train
    outs:
      - models/model.joblib
      - models/model_meta.json
    metrics:
      - reports/train_metrics.json:
          cache: false

  evaluate:
    cmd: python -m src.evaluate
    deps:
      - src/evaluate.py
      - models/model.joblib
      - data/processed/test.csv
    params:
      - evaluate
    metrics:
      - reports/eval_metrics.json:
          cache: false
```

**Не пропустите `src/features.py` в зависимостях train.** Если его там нет,
вы поменяете препроцессор, DVC решит, что ничего не изменилось, и оставит
старую модель. Ошибки не будет — будет неверный результат, а это хуже.

**`cache: false` у метрик** означает, что маленькие JSON-файлы едут прямо
в Git. Так `dvc metrics diff` умеет сравнивать метрики между коммитами.

Модель теперь тоже выход стадии, поэтому `.dvc`-файл из занятия 4 надо убрать —
иначе DVC откажется работать: один и тот же путь описан в двух местах.

```bash
dvc remove models/model.joblib.dvc
```

Если пропустить, `dvc repro` скажет:
`output 'models/model.joblib' is specified in: train, models/model.joblib.dvc`

## Шаг 3. Запуск и наблюдение

```bash
dvc repro
```

Посмотрите на граф:

```bash
dvc dag
```

Запустите ещё раз:

```bash
dvc repro
```

Все стадии пропущены: `Stage 'generate' didn't change, skipping`.

Теперь эксперимент. Поменяйте в `params.yaml` значение
`train.gradient_boosting.learning_rate` на `0.1` и запустите снова:

```bash
dvc repro
```

Перезапустились только `train` и `evaluate`. Генерация и подготовка данных
пропущены — DVC понял, что на них изменение не влияет.

## Шаг 4. dvc.lock

Откройте `dvc.lock`. Там зафиксированы хеши всех входов и выходов каждой
стадии — снимок состояния пайплайна.

```bash
git add dvc.yaml dvc.lock params.yaml reports/
git commit -m "Описать пайплайн в DVC"
dvc push
```

`dvc.lock` **обязательно** коммитится: без него на другой машине DVC
не поймёт, какому состоянию соответствуют данные в хранилище.

Заодно вы только что бесплатно получили привязку метрики к версии данных,
про которую шла речь на занятии 4. В одном коммите лежат `dvc.lock`
с хешами данных и `reports/train_metrics.json` с метриками. По любому
коммиту теперь восстанавливается полный ответ: вот метрика, вот код,
вот конкретные байты данных, на которых она получена. Руками ничего
переписывать не нужно.

## Шаг 5. Сравнение метрик

Это то, ради чего метрики держатся в Git:

```bash
dvc metrics show
dvc metrics diff HEAD~1
```

Вы получаете разницу метрик между коммитами — без ручных таблиц.

Постройте ROC-кривую. Добавьте в `evaluate.py` сохранение точек кривой
в `reports/roc.json`:

```python
from sklearn.metrics import roc_curve   # к остальным импортам evaluate.py

# y_test и proba — те же переменные, по которым вы считаете метрики
fpr, tpr, _ = roc_curve(y_test, proba)
step = max(1, len(fpr) // 200)          # 200 точек хватает для графика
points = [{"fpr": float(a), "tpr": float(b)} for a, b in zip(fpr[::step], tpr[::step])]

with open(resolve("reports/roc.json"), "w", encoding="utf-8") as f:
    json.dump(points, f, indent=2)
```

и опишите в стадии `evaluate`:

```yaml
    plots:
      - reports/roc.json:
          x: fpr
          y: tpr
          cache: false
```

```bash
dvc repro && dvc plots show
```

## Шаг 6. Проверка на чистом клоне

Главная проверка занятия:

```bash
git clone <ваш-репо> /tmp/repro && cd /tmp/repro
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
dvc remote modify --local minio access_key_id minioadmin
dvc remote modify --local minio secret_access_key minioadmin
dvc repro
cat reports/eval_metrics.json
```

Метрики должны совпасть с вашими до третьего знака. Если совпали — у вас
воспроизводимый пайплайн. Это половина курса.

## Шаг 7. Стадия валидации данных

Ваш пайплайн сейчас обучит модель на чём угодно. Придёт выгрузка,
где половина `monthly_charges` — нули, и `dvc repro` спокойно отработает.
Поставим заслон между подготовкой и обучением.

Создайте `src/data/validate.py`. Скрипт читает `data/processed/train.csv`
и **завершается кодом 1**, если нарушено хоть одно правило:

```python
CHECKS = {
    "строк не меньше минимума":    lambda df, p: len(df) >= p["min_rows"],
    "доля пропусков в норме":      lambda df, p: df.isna().mean().max() <= p["max_missing_share"],
    "доля оттока осмысленна":      lambda df, p: p["target_rate"][0] < df[TARGET].mean() < p["target_rate"][1],
    "нет дублей по клиенту":       lambda df, p: not df["customer_id"].duplicated().any(),
    "стаж в допустимом диапазоне": lambda df, p: df["tenure_months"].between(0, 200).all(),
}
```

Пороги — в `params.yaml`, не в коде:

```yaml
validate:
  min_rows: 5000
  max_missing_share: 0.05
  target_rate: [0.05, 0.60]
```

Скрипт печатает результат каждой проверки и пишет `reports/validation.json`
с перечнем пройденного и упавшего.

Вставьте стадию в `dvc.yaml` **между** prepare и train:

```yaml
  validate:
    cmd: python -m src.data.validate
    deps:
      - src/data/validate.py
      - data/processed/train.csv
    params:
      - validate
    metrics:
      - reports/validation.json:
          cache: false
```

И допишите `reports/validation.json` в зависимости стадии `train` —
тогда обучение не запустится, пока валидация не прошла.

Проверьте, что заслон работает: временно поставьте `min_rows: 999999`,
запустите `dvc repro` и убедитесь, что пайплайн остановился на validate
и до обучения не дошёл.

## Что сдать

- [ ] `dvc.yaml` с четырьмя стадиями и корректными `deps`
- [ ] `dvc repro` дважды подряд: второй раз всё пропускается
- [ ] Изменение `learning_rate` перезапускает только `train` и `evaluate`
- [ ] `dvc.lock` закоммичен
- [ ] `dvc metrics diff HEAD~1` показывает изменение
- [ ] Пайплайн воспроизводится на чистом клоне
- [ ] Стадия `validate` в пайплайне, обучение зависит от её результата
- [ ] Показано, что при нарушении порога `dvc repro` останавливается до обучения

## Домашнее задание (1,5–2 ч)

1. Проведите три эксперимента, меняя **только** `params.yaml`
   (модель и гиперпараметры). Каждый — отдельным коммитом с `dvc repro`.
2. Соберите таблицу `dvc metrics diff` между этими коммитами
   и приложите её в `reports/EXPERIMENTS.md`.
3. Добавьте цель в `Makefile`:
   ```make
   pipeline:        ## Воспроизвести пайплайн
   	dvc repro
   ```
4. Письменно ответьте в `README.md`: что произойдёт, если убрать
   `src/features.py` из `deps` стадии `train`? Почему это опаснее,
   чем ошибка, которая роняет скрипт?

## Полезное

| Команда | Зачем |
|---|---|
| `dvc repro` | воспроизвести устаревшие стадии |
| `dvc repro -f` | принудительно всё заново |
| `dvc repro train` | только одну стадию с зависимостями |
| `dvc dag` | граф пайплайна |
| `dvc status` | что устарело |
| `dvc metrics show` / `diff` | метрики и их изменение |
| `dvc plots show` | графики из `reports/` |
