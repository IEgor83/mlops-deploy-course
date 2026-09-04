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
fpr, tpr, _ = roc_curve(y_test, proba)
step = max(1, len(fpr) // 200)
json.dump([{"fpr": float(a), "tpr": float(b)} for a, b in zip(fpr[::step], tpr[::step])], f)
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

## Что сдать

- [ ] `dvc.yaml` с четырьмя стадиями и корректными `deps`
- [ ] `dvc repro` дважды подряд: второй раз всё пропускается
- [ ] Изменение `learning_rate` перезапускает только `train` и `evaluate`
- [ ] `dvc.lock` закоммичен
- [ ] `dvc metrics diff HEAD~1` показывает изменение
- [ ] Пайплайн воспроизводится на чистом клоне

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
