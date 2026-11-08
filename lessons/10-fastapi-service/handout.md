# Занятие 10. Инференс-сервис на FastAPI

## Проблема

У вас есть `models/model.joblib`. Отделу маркетинга нужен риск оттока
для клиента в момент звонка. Отдать им файл модели нельзя: у них нет
Python, нет препроцессинга и нет желания разбираться.

Нужен сервис: принимает JSON, возвращает предсказание.

## Шаг 1. Схемы

Создайте `src/service/schemas.py`. Схема — это граница системы:
всё, что не прошло валидацию, до модели не доходит.

```python
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

ContractType = Literal["month-to-month", "one_year", "two_year"]
InternetService = Literal["fiber", "dsl", "none"]
PaymentMethod = Literal["electronic_check", "mailed_check", "bank_transfer", "credit_card"]


class Customer(BaseModel):
    tenure_months: int = Field(..., ge=0, le=200, description="Стаж клиента в месяцах")
    monthly_charges: float = Field(..., ge=0, le=1000)
    total_charges: Optional[float] = Field(None, ge=0)
    contract_type: ContractType
    internet_service: InternetService
    payment_method: PaymentMethod
    num_support_calls: int = Field(..., ge=0, le=100)
    has_tech_support: int = Field(..., ge=0, le=1)
    is_senior: int = Field(..., ge=0, le=1)
    avg_monthly_gb: float = Field(..., ge=0, le=5000)


class BatchRequest(BaseModel):
    # Верхняя граница обязательна: запрос на миллион строк положит сервис.
    # Понятный отказ лучше, чем OOM.
    items: List[Customer] = Field(..., min_length=1, max_length=1000)


class Prediction(BaseModel):
    churn_probability: float
    churn: int
    threshold: float
    model_version: str
```

**Про `Literal`.** Категория с опечаткой (`"month_to_month"` вместо
`"month-to-month"`) без него молча дойдёт до препроцессора, тот применит
`handle_unknown="ignore"`, и клиент получит предсказание, посчитанное
как будто категория неизвестна. С `Literal` — честный 422 и понятное сообщение.

**Про диапазоны.** Границы взяты из данных, а не выдуманы: `tenure_months`
до 200 месяцев, `monthly_charges` до 1000. Отрицательный стаж —
это ошибка на стороне клиента, и сказать об этом нужно сразу.

## Шаг 2. Приложение

`src/service/app.py`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Модель грузится ОДИН раз на старте. Если грузить в обработчике,
    # каждый запрос будет идти секундами.
    try:
        holder.load()
    except Exception as exc:
        log.error("не удалось загрузить модель: %s", exc)
    yield


app = FastAPI(
    title="Churn Prediction Service",
    version="1.0.0",
    lifespan=lifespan,
)
```

## Шаг 3. Эндпоинты

```python
@app.get("/health", response_model=HealthResponse, tags=["service"])
def health() -> HealthResponse:
    """Жив ли процесс и загружена ли модель."""
    return HealthResponse(
        status="ok" if holder.loaded else "degraded",
        model_loaded=holder.loaded,
        model_version=holder.version,
    )


@app.post("/predict", response_model=Prediction, tags=["inference"])
def predict(customer: Customer) -> Prediction:
    params = load_params()
    threshold = params["evaluate"]["threshold"]
    if not holder.loaded:
        raise HTTPException(status_code=503, detail="Модель не загружена")

    df = pd.DataFrame([customer.model_dump()])[feature_columns(params)]
    proba = float(holder.model.predict_proba(df)[0, 1])
    return Prediction(
        churn_probability=round(proba, 6),
        churn=int(proba >= threshold),
        threshold=threshold,
        model_version=holder.version,
    )
```

Три детали, каждая со смыслом:

**`[feature_columns(params)]`** — колонки выбираются явно и в известном
порядке. Без этого набор и порядок колонок зависят от того, как Pydantic
разложил поля, и рано или поздно разойдутся с обучением.

**503, а не 500, если модель не загружена.** 503 означает «сервис временно
не может обслужить», и балансировщик поймёт, что трафик сюда слать не нужно.

**`model_version` в ответе.** Через месяц придёт вопрос «почему этому
клиенту поставили 0.8». Без версии модели ответить невозможно.

Допишите сами `/predict/batch` по образцу — он принимает `BatchRequest`
и возвращает `BatchPrediction` со списком и полем `count`.

## Шаг 4. Запуск

```make
serve:           ## Запустить сервис локально
	uvicorn src.service.app:app --host 0.0.0.0 --port 8000 --reload
```

```bash
make serve
```

Проверьте:

```bash
curl -s localhost:8000/health | jq
curl -s -X POST localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d @examples/request.json | jq
```

Откройте http://localhost:8000/docs — интерактивная документация
сгенерирована из ваших типов. Ничего писать руками не пришлось:
это и есть причина, по которой схемы описываются типами, а не проверками в коде.

## Шаг 5. Проверить отказы

```bash
# отрицательный стаж
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
  -d '{"tenure_months": -5, "monthly_charges": 50, "contract_type": "two_year", "internet_service": "dsl", "payment_method": "mailed_check", "num_support_calls": 0, "has_tech_support": 1, "is_senior": 0, "avg_monthly_gb": 10}' | jq

# несуществующая категория
# ... contract_type: "lifetime" -> тоже 422

# пустой батч
curl -s -X POST localhost:8000/predict/batch -H 'Content-Type: application/json' \
  -d '{"items": []}' | jq
```

Все три должны вернуть **422** с указанием проблемного поля.
Если где-то 500 — валидация не работает, и вы ловите ошибку слишком поздно.

## Шаг 6. Тесты контракта

`tests/test_api.py` — тесты идут через `TestClient`, поднимать сервис не нужно:

```python
@pytest.fixture(scope="module")
def client(tmp_path_factory, trained_pipeline):
    """Подсовываем сервису модель из фикстуры: тесты API не должны зависеть
    от того, лежит ли в models/ артефакт с прошлого запуска."""
    from src.service import app as app_module
    app_module.holder.model = trained_pipeline
    app_module.holder.version = "test:fixture"
    with TestClient(app_module.app) as c:
        yield c


def test_predict_returns_valid_probability(client):
    body = client.post("/predict", json=VALID).json()
    assert 0.0 <= body["churn_probability"] <= 1.0
    assert body["model_version"]


def test_unknown_category_returns_422(client):
    assert client.post("/predict", json=dict(VALID, contract_type="lifetime")).status_code == 422
```

Напишите минимум шесть тестов: health, успешное предсказание,
отсутствующее поле, значение вне диапазона, неизвестная категория,
батч, пустой батч.

## Шаг 8. Объяснение предсказания и сквозной идентификатор

### `/explain` — почему именно такой ответ

Маркетингу мало числа 0.83. Первый же вопрос: «а почему?»
Без ответа предсказанием не пользуются.

Добавьте эндпоинт, возвращающий вклад признаков:

```python
@app.post("/explain", response_model=Explanation, tags=["inference"])
def explain(customer: Customer) -> Explanation:
    """Вклад каждого признака в предсказание.

    Для линейной модели это коэффициент, умноженный на значение признака
    после препроцессинга. Для деревьев — feature_importances_, они
    глобальные, а не для конкретного клиента, и это нужно честно писать
    в ответе, чтобы бизнес не принял одно за другое.
    """
```

В ответе верните топ-5 признаков с вкладами, отсортированные по модулю,
и поле `method` — `"linear_contribution"` или `"global_importance"`,
чтобы потребитель понимал, что именно получил.

### Идентификатор запроса

Клиент звонит и говорит: «мне выдало странное предсказание полчаса назад».
Найти этот запрос в логах сейчас невозможно.

Добавьте в middleware генерацию `request_id`, верните его в заголовке
`X-Request-ID` и пишите в каждую строку лога:

```python
request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
```

Если заголовок пришёл от клиента — используйте его, не генерируйте свой:
так идентификатор сохранится через всю цепочку сервисов.

## Что сдать

- [ ] `/health`, `/predict`, `/predict/batch` работают
- [ ] Некорректный вход даёт 422, не 500
- [ ] В ответе есть `model_version`
- [ ] Модель грузится в `lifespan`, а не в обработчике
- [ ] ≥ 6 тестов API, `make test` зелёный
- [ ] `/docs` открывается и содержит примеры
- [ ] Эндпоинт `/explain` с топ-5 вкладов и полем `method`
- [ ] `X-Request-ID` в ответе и в каждой строке лога

## Домашнее задание (1,5–2 ч)

1. Добавьте эндпоинт `POST /reload`, перезагружающий модель без рестарта
   процесса. Он понадобится на занятии 16.
2. Замерьте производительность:
   ```bash
   for i in $(seq 1 100); do
     curl -s -o /dev/null -X POST localhost:8000/predict \
       -H 'Content-Type: application/json' -d @examples/request.json
   done
   ```
   Сравните: 100 одиночных запросов против одного батча на 100 записей.
   Запишите цифры и объяснение разницы в `README.md`.
3. Опишите в `README.md` контракт API: эндпоинты, форматы, коды ответов.
   Пишите для внешнего потребителя, который ваш код не читает.

## Полезное

| Что | Зачем |
|---|---|
| `/docs` | Swagger UI, интерактивный |
| `/redoc` | альтернативный вид документации |
| `/openapi.json` | машиночитаемая спецификация |
| `--reload` | автоперезапуск при правке кода (только для разработки!) |
| `curl -w "%{time_total}"` | время выполнения запроса |
