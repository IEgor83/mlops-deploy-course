# Занятие 6. MLflow Tracking

## Проблема

К этому моменту вы провели около десяти прогонов и ведёте таблицу руками.
Проверьте себя: можете ли вы сейчас, глядя в `EXPERIMENTS.md`, точно сказать
для строки с лучшей метрикой — какой был коммит кода, какая версия данных,
и где лежит та самая модель?

Обычно нет. Сегодня ставим инструмент, который записывает это сам.

## Шаг 1. Поднять MLflow

В отдельном терминале (он должен остаться открытым):

```bash
pip install "mlflow>=2.11,<3.0"
mlflow server --host 127.0.0.1 --port 5000 \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./mlartifacts
```

Откройте http://localhost:5000 — увидите пустой список экспериментов.

Добавьте в `.gitignore`:

```
mlflow.db
mlartifacts/
mlruns/
```

## Шаг 2. Настройки в конфиг

В `params.yaml`:

```yaml
mlflow:
  enabled: true
  tracking_uri: http://localhost:5000
  experiment_name: churn
  registered_model_name: churn-classifier
```

## Шаг 3. Логирование прогона

В `src/train.py` добавьте функцию:

```python
def log_to_mlflow(params, pipe, metrics, input_example) -> None:
    import mlflow
    import mlflow.sklearn

    cfg = params["mlflow"]
    mlflow.set_tracking_uri(cfg["tracking_uri"])
    mlflow.set_experiment(cfg["experiment_name"])

    name = params["train"]["model"]
    with mlflow.start_run():
        mlflow.log_params({"model": name, "seed": params["seed"]})
        mlflow.log_params({f"{name}.{k}": v for k, v in params["train"][name].items()})
        mlflow.log_metrics(metrics)
        mlflow.set_tag("git_sha", git_sha())
        mlflow.log_artifact("params.yaml")
        mlflow.sklearn.log_model(pipe, artifact_path="model", input_example=input_example)
```

Обратите внимание на три вещи:

* **Импорт внутри функции.** Так обучение продолжит работать в окружении
  без MLflow — это понадобится в CI на занятии 9.
* **`set_tag("git_sha", ...)`.** Без привязки к коммиту прогон невоспроизводим:
  вы будете знать метрику, но не код, который её дал.
* **`log_model`, а не `log_artifact` для модели.** MLflow сохранит вместе
  с моделью её сигнатуру и окружение — это понадобится на занятии 7.

## Шаг 4. Выключатель

Обучение не должно намертво зависеть от трекера. Добавьте флаг:

```python
parser.add_argument("--no-mlflow", action="store_true")
...
if params["mlflow"]["enabled"] and not args.no_mlflow:
    log_to_mlflow(params, pipe, metrics, train_df[cols].head(5))
```

И правьте `dvc.yaml`, стадию train:

```yaml
    cmd: python -m src.train --no-mlflow
```

Почему в пайплайне трекинг выключен: `dvc repro` должен работать в CI,
где MLflow-сервера нет. Логирование — отдельное действие исследователя,
а не часть воспроизводимого пайплайна.

## Шаг 5. Провести эксперименты

Запустите минимум пять прогонов, меняя `params.yaml`:

```bash
python -m src.train         # gradient_boosting, learning_rate 0.05
# правим learning_rate -> 0.1, повторяем
# правим n_estimators -> 400
# меняем model -> random_forest
# меняем model -> logreg
```

Откройте http://localhost:5000 и разберитесь в UI:

* отсортируйте таблицу по `roc_auc`;
* выделите два прогона → **Compare** → посмотрите разницу параметров;
* в режиме Compare откройте **Parallel Coordinates Plot** — видно,
  какие параметры реально влияют на метрику;
* зайдите в лучший прогон → вкладка Artifacts — там лежит модель.

## Шаг 6. Логировать графики

Метрика — одно число, оно не показывает, где модель ошибается.
Добавьте в логирование ROC-кривую:

```python
import matplotlib
matplotlib.use("Agg")          # без этого упадёт в среде без дисплея
import matplotlib.pyplot as plt
from sklearn.metrics import RocCurveDisplay

fig, ax = plt.subplots(figsize=(5, 5))
RocCurveDisplay.from_predictions(y_val, val_proba, ax=ax)
fig.savefig("reports/roc_curve.png", dpi=100, bbox_inches="tight")
mlflow.log_artifact("reports/roc_curve.png")
plt.close(fig)
```

## Шаг 7. Выбрать модель осознанно

Найдите в UI лучший прогон по ROC-AUC. Теперь проверьте его F1 —
скорее всего, около 0.39. Так происходит, потому что порог 0.5
не подходит для несбалансированной задачи: отток составляет ~21 % клиентов.

Подберите порог по валидации:

```python
from sklearn.metrics import precision_recall_curve
prec, rec, thr = precision_recall_curve(y_val, val_proba)
f1 = 2 * prec * rec / (prec + rec + 1e-9)
best = thr[f1[:-1].argmax()]
print("лучший порог:", round(float(best), 3))
```

Запишите найденное значение в `params.yaml → evaluate.threshold`
и перезапустите `make eval`.

**Что здесь важно понять:** порог — это не гиперпараметр модели,
а продуктовое решение. Он отвечает на вопрос «что дороже: упустить
уходящего клиента или потратить скидку на того, кто и так остался».
Занесите своё обоснование в `EXPERIMENTS.md`.

## Что сдать

- [ ] MLflow поднят, логирование работает
- [ ] ≥ 5 прогонов с параметрами, метриками, тегом `git_sha` и артефактами
- [ ] Флаг `--no-mlflow` работает, `dvc.yaml` использует его
- [ ] Порог подобран по валидации, обоснование записано
- [ ] Скриншот UI со сравнением прогонов — в `reports/`

## Домашнее задание (1,5–2 ч)

1. Доведите число прогонов до 10+, покрыв все три алгоритма
   и минимум по три набора гиперпараметров.
2. Добавьте логирование матрицы ошибок как артефакта.
3. Залогируйте версию данных: `mlflow.set_tag("data_md5", ...)`,
   взяв хеш из `data/raw/churn.csv.dvc`. Объясните в `README.md`,
   зачем это нужно, если git sha уже логируется.
4. Напишите в `README.md` раздел «Выбор модели»: какая выбрана,
   по какой метрике, какой порог и почему.

## Полезное

| Термин | Что это |
|---|---|
| run | один прогон обучения |
| experiment | группа прогонов, решающих одну задачу |
| artifact | файл, привязанный к прогону (модель, график, конфиг) |
| tag | произвольная метка прогона (git sha, автор, версия данных) |

`mlflow.sklearn.autolog()` логирует многое автоматически, но не знает
о версии данных и ваших бизнес-метриках — поэтому в реальных проектах
его сочетают с ручным логированием, а не заменяют им.
