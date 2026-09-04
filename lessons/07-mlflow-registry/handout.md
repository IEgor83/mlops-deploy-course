# Занятие 7. MLflow Model Registry

## Проблема

У вас 10+ прогонов и лучшая модель среди них. Теперь ответьте:

1. Какая модель должна работать в проде **прямо сейчас**?
2. Как ваш будущий сервис узнает, какую загружать?
3. Как откатиться на предыдущую за минуту, а не за переобучение?

Путь `models/model.joblib` не отвечает ни на один вопрос: это просто
последний файл, который перезаписало последнее обучение.

## Шаг 1. Зарегистрировать модель

Добавьте в `log_to_mlflow` регистрацию:

```python
mlflow.sklearn.log_model(
    pipe,
    artifact_path="model",
    input_example=input_example,
    registered_model_name=cfg["registered_model_name"],
)
```

`input_example` не декоративный: по нему MLflow выводит **сигнатуру** —
какие колонки и типы модель ожидает на входе. Это первый рубеж защиты
от несовпадения данных обучения и инференса.

Запустите обучение:

```bash
python -m src.train
```

Откройте http://localhost:5000 → вкладка **Models**. Появилась модель
`churn-classifier`, версия 1.

Запустите ещё дважды с разными параметрами — появятся версии 2 и 3.

## Шаг 2. Стадии

В UI: Models → `churn-classifier` → Version 3 → Stage → **Transition to Production**.

Три стадии и их смысл:

| Стадия | Что означает |
|---|---|
| `None` | только что зарегистрирована, никем не проверена |
| `Staging` | проходит проверку, можно тестировать |
| `Production` | работает на реальных клиентах |
| `Archived` | выведена, но сохранена для отката |

Это контракт между людьми: разработчик знает, что трогать `Production`
без причины нельзя, а сервис знает, что грузить нужно именно её.

## Шаг 3. Загрузка по имени

Создайте `src/service/model_loader.py`:

```python
class ModelHolder:
    def __init__(self) -> None:
        self.model = None
        self.version = "not-loaded"

    @property
    def loaded(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        params = load_params()
        if params["mlflow"]["enabled"] and self._try_registry(params):
            return
        self._load_local(params)

    def _try_registry(self, params) -> bool:
        try:
            import mlflow
            mlflow.set_tracking_uri(params["mlflow"]["tracking_uri"])
            name = params["mlflow"]["registered_model_name"]
            stage = params["service"]["model_stage"]
            self.model = mlflow.sklearn.load_model(f"models:/{name}/{stage}")
            self.version = f"registry:{name}/{stage}"
            return True
        except Exception as exc:
            log.warning("MLflow Registry недоступен (%s), берём локальный файл", exc)
            return False

    def _load_local(self, params) -> None:
        self.model = joblib.load(resolve(params["service"]["model_path"]))
        self.version = "local:..."   # достаньте детали из models/model_meta.json


holder = ModelHolder()
```

Добавьте в `params.yaml`:

```yaml
service:
  model_stage: Production
  model_path: models/model.joblib
```

Проверьте:

```bash
python -c "from src.service.model_loader import holder; holder.load(); print(holder.version)"
```

## Шаг 4. Зачем фолбэк

Обратите внимание на `try/except` в `_try_registry`: если MLflow недоступен,
сервис не падает, а берёт локальный файл.

Это осознанное решение, и его нужно уметь защитить. Аргумент: недоступность
**вспомогательной** системы не должна ронять **основную**. Трекинг-сервер —
инструмент разработчика; клиенты, которым нужны предсказания, про него
ничего не знают.

Обратная сторона тоже есть: молчаливый фолбэк может скрыть проблему.
Поэтому в коде стоит `log.warning`, а на занятии 14 вы добавите метрику
`model_loaded` и алерт на неё.

## Шаг 5. Отработать откат

Разыграйте инцидент на своём проекте:

1. Переведите версию 3 в `Production`, загрузите модель, запомните `version`.
2. «Обнаружили проблему»: в UI переведите версию 3 в `Archived`,
   версию 2 — в `Production`.
3. Загрузите заново — убедитесь, что подтянулась другая модель.

Засеките, сколько это заняло. Сравните с временем полного переобучения.

## Шаг 6. Записать регламент

Создайте `docs/model-promotion.md` в своём репозитории. Опишите
своими словами, но конкретно:

* при каких условиях модель переводится в `Staging`;
* какие проверки проходят перед `Production` (минимум: ROC-AUC не хуже
  текущей продовой, тесты зелёные, сигнатура не изменилась);
* кто принимает решение;
* как выполняется откат и за какое время.

Это не бюрократия: на занятии 16 вы будете автоматизировать именно
этот регламент, и его придётся сначала сформулировать.

## Что сдать

- [ ] Модель зарегистрирована, ≥ 3 версии
- [ ] Одна версия в `Production`, одна в `Archived`
- [ ] `model_loader.py` грузит по `models:/имя/Production` с фолбэком
- [ ] Продемонстрирован откат на предыдущую версию
- [ ] `docs/model-promotion.md` написан

## Домашнее задание (1,5–2 ч)

1. Добавьте в `model_loader` метод, возвращающий подробности версии:
   номер, дату регистрации, `git_sha` исходного прогона.
   Подсказка: `mlflow.MlflowClient().get_latest_versions(name, stages=["Production"])`.
2. Напишите скрипт `scripts/promote.py`, который сам сравнивает
   кандидата с текущей продовой версией на тестовой выборке и переводит
   в `Production`, только если ROC-AUC выше хотя бы на 0.005.
3. Ответьте письменно в `docs/model-promotion.md`: почему автоматический
   промоут «по метрике выше» без порога минимального прироста — плохая идея?

## Полезное

* `models:/имя/Production` — по стадии
* `models:/имя/3` — по номеру версии
* `runs:/<run_id>/model` — напрямую из прогона
* В MLflow 2.9+ стадии считаются устаревшими; в новых проектах используют
  алиасы: `models:/churn-classifier@champion`. Механика та же
