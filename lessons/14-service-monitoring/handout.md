# Занятие 14. Мониторинг сервиса

## Проблема

Ваш сервис в контейнере, `docker ps` показывает `Up 3 hours`.
Вопросы, на которые вы сейчас не можете ответить:

* сколько запросов в секунду он обрабатывает;
* сколько из них завершились ошибкой;
* сколько ждёт самый невезучий пользователь;
* загружена ли вообще модель.

Пока ответов нет, «работает» — это предположение.

## Шаг 1. Метрики в коде

Установите `prometheus-client` (он уже в `requirements-service.txt`)
и добавьте в `src/service/app.py` **на уровне модуля**:

```python
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

REQUESTS = Counter(
    "prediction_requests_total", "Число запросов предсказания", ["endpoint", "status"]
)
LATENCY = Histogram(
    "prediction_latency_seconds", "Время обработки запроса", ["endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)
PROBA = Histogram(
    "prediction_probability", "Распределение предсказанных вероятностей",
    buckets=[i / 10 for i in range(11)],
)
MODEL_LOADED = Gauge("model_loaded", "1 — модель загружена, 0 — нет")
```

**Объявлять обязательно на уровне модуля.** Если создать метрику внутри
функции, каждый запрос будет создавать новый объект, и значения не накопятся.

Три типа и когда какой:

| Тип | Что делает | Пример |
|---|---|---|
| Counter | только растёт | число запросов |
| Gauge | растёт и падает | модель загружена: 1/0 |
| Histogram | копит распределение по корзинам | время ответа |

**Про `prediction_probability`.** Это не метрика инфраструктуры,
а метрика модели. Сдвиг распределения предсказаний виден за часы,
а падение бизнес-метрик — за недели. Дешёвый ранний детектор дрейфа.

## Шаг 2. Инструментировать эндпоинты

```python
@app.post("/predict", response_model=Prediction)
def predict(customer: Customer) -> Prediction:
    start = time.perf_counter()
    try:
        ...
        PROBA.observe(result.churn_probability)
        REQUESTS.labels("predict", "ok").inc()
        return result
    except HTTPException:
        REQUESTS.labels("predict", "error").inc()
        raise
    finally:
        LATENCY.labels("predict").observe(time.perf_counter() - start)


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

`finally` важен: время нужно замерять и для упавших запросов тоже,
иначе метрика latency будет врать в самый интересный момент.

В `lifespan` добавьте `MODEL_LOADED.set(1)` после успешной загрузки
и `MODEL_LOADED.set(0)` при ошибке.

Проверьте:

```bash
make serve
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' -d @examples/request.json
curl -s localhost:8000/metrics | grep prediction_
```

## Шаг 3. Структурные логи

Добавьте middleware, логирующее каждый запрос:

```python
@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    log.info("%s %s -> %s за %.1f мс", request.method, request.url.path,
             response.status_code, (time.perf_counter() - start) * 1000)
    return response
```

Разделение труда: метрики отвечают на вопрос «что происходит вообще»,
логи — «что случилось с конкретным запросом». Нужны оба.

## Шаг 4. Prometheus

`monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 10s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/alerts.yml

scrape_configs:
  - job_name: churn-api
    metrics_path: /metrics
    static_configs:
      - targets: ["api:8000"]
```

`api:8000`, а не `localhost:8000` — Prometheus живёт в своём контейнере
и обращается к сервису по имени, как вы разбирали на занятии 12.

В `docker-compose.yml`:

```yaml
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ../monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ../monitoring/alerts.yml:/etc/prometheus/alerts.yml:ro
    depends_on:
      - api
```

```bash
make up
```

Откройте http://localhost:9090/targets — цель `churn-api` должна быть `UP`.
**Если нет — дальше идти бессмысленно**, разберитесь здесь.

## Шаг 5. Запросы PromQL

Создайте нагрузку:

```bash
for i in $(seq 1 500); do
  curl -s -o /dev/null -X POST localhost:8000/predict \
    -H 'Content-Type: application/json' -d @examples/request.json
done
```

Попробуйте в Prometheus:

```promql
# запросов в секунду по эндпоинтам
sum by (endpoint) (rate(prediction_requests_total[1m]))

# доля ошибок
sum(rate(prediction_requests_total{status="error"}[5m]))
  / clamp_min(sum(rate(prediction_requests_total[5m])), 0.001)

# p95 времени ответа
histogram_quantile(0.95, sum(rate(prediction_latency_seconds_bucket[5m])) by (le))

# медиана предсказанной вероятности
histogram_quantile(0.5, sum(rate(prediction_probability_bucket[10m])) by (le))
```

**Почему p95, а не среднее.** Среднее время ответа 100 мс звучит хорошо,
но если 5 % пользователей ждут 3 секунды — это плохой сервис.
Среднее прячет хвост, перцентиль показывает.

`clamp_min` в знаменателе защищает от деления на ноль, когда трафика нет.

## Шаг 6. Grafana

Добавьте в compose:

```yaml
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - ../monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ../monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
```

`monitoring/grafana/provisioning/datasources/prometheus.yml`:

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

Постройте дашборд из пяти панелей:

1. `model_loaded` — Stat
2. RPS по эндпоинтам — Time series
3. Доля ошибок — Time series
4. Latency p50 / p95 / p99 — Time series
5. Медиана предсказанной вероятности — Time series

**Обязательно экспортируйте дашборд**: Share → Export → Save to file,
положите JSON в `monitoring/grafana/dashboards/`. Дашборд, живущий
только в базе Grafana, исчезнет при первом `docker compose down -v`.

## Шаг 7. Алерты

`monitoring/alerts.yml`:

```yaml
groups:
  - name: churn-service
    rules:
      - alert: ModelNotLoaded
        expr: model_loaded == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Процесс жив, но модель не загружена"
          action: "Проверить доступность MLflow Registry и наличие models/model.joblib"

      - alert: HighLatencyP95
        expr: histogram_quantile(0.95, sum(rate(prediction_latency_seconds_bucket[5m])) by (le)) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "p95 latency превысил 500 мс"
          action: "Смотреть размер батчей и загрузку CPU контейнера"
```

Два обязательных элемента каждого правила:

**`for:`** — сколько условие должно держаться. Без него алерт сработает
на единичный всплеск и разбудит человека зря.

**`action:`** — что делать дежурному. Алерт без инструкции бесполезен:
через месяц его отключат, потому что никто не понимает, что предпринять.

Проверьте, что алерт работает: остановите сервис (`docker compose stop api`)
и посмотрите http://localhost:9090/alerts — правило должно перейти
в `PENDING`, затем в `FIRING`.

## Шаг 8. SLO и бюджет ошибок

Алерты вы настроили. Но на вопрос «сервис работает хорошо или плохо»
они не отвечают: алерт либо горит, либо нет, а между «всё отлично»
и «пожар» есть огромная серая зона.

### Сформулируйте SLO

SLO (Service Level Objective) — измеримое обещание, которое вы даёте
потребителю. Для нашего сервиса разумно:

> 99 % запросов к `/predict` обрабатываются быстрее 300 мс
> в течение календарного месяца.

Запишите его в `docs/slo.md` вместе с обоснованием: почему 300 мс,
а не 100 или 1000. Подсказка: оператор колл-центра разговаривает
с клиентом, и пауза дольше трети секунды уже заметна в разговоре.

### Посчитайте бюджет ошибок

Из SLO следует бюджет: если обещано 99 %, то 1 % запросов **можно**
обслужить медленно. Это не недостаток — это разрешённый расход.

```promql
# доля запросов быстрее 300 мс за 30 дней
sum(rate(prediction_latency_seconds_bucket{le="0.3"}[30d]))
  / sum(rate(prediction_latency_seconds_count[30d]))
```

Добавьте на дашборд панель «остаток бюджета ошибок» в процентах.

### Алерт на скорость сжигания

Главное отличие от порогового алерта: он срабатывает не когда стало
плохо, а когда **бюджет кончится раньше срока**.

```yaml
      - alert: ErrorBudgetBurningFast
        expr: |
          (1 - (
            sum(rate(prediction_latency_seconds_bucket{le="0.3"}[1h]))
            / sum(rate(prediction_latency_seconds_count[1h]))
          )) > 0.01 * 14
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Бюджет ошибок расходуется в 14 раз быстрее нормы"
          action: "При таком темпе месячный бюджет кончится за двое суток. Смотреть дашборд latency."
```

Множитель 14 означает: расходуем в 14 раз быстрее, чем можем себе
позволить. Допишите в `docs/runbook.md`, что делает дежурный,
когда бюджет израсходован полностью — обычно это заморозка релизов
до восстановления.

## Что сдать

- [ ] `/metrics` отдаёт метрики в формате Prometheus
- [ ] Prometheus видит цель как `UP`
- [ ] Дашборд Grafana из ≥ 5 панелей, JSON в репозитории
- [ ] `monitoring/alerts.yml` с ≥ 2 правилами, у каждого `for` и `action`
- [ ] Продемонстрировано срабатывание алерта
- [ ] Middleware логирует запросы
- [ ] `docs/slo.md` с SLO и обоснованием порога
- [ ] Панель остатка бюджета ошибок и алерт на скорость сжигания

## Домашнее задание (1,5–2 ч)

1. Добавьте алерт на долю ошибок > 5 % за 5 минут. Обоснуйте порог
   письменно: почему 5 %, а не 1 % и не 20 %.
2. Проведите нагрузочный эксперимент: одиночные запросы против батчей
   по 100. Снимите графики, приложите скриншоты в `reports/`
   и объясните разницу в latency.
3. Напишите `docs/runbook.md` — что делает дежурный по каждому алерту:
   как проверить, что смотреть, что сделать, кого звать. По одному
   разделу на алерт.
4. Ответьте письменно: почему `model_loaded == 0` — critical,
   а `p95 > 500ms` — warning? Что изменится, если сервис используется
   в реальном времени в колл-центре?

## Полезное

| Что | Зачем |
|---|---|
| http://localhost:9090/targets | видит ли Prometheus ваш сервис |
| http://localhost:9090/alerts | состояние правил |
| `rate(counter[5m])` | скорость роста счётчика |
| `histogram_quantile(0.95, ...)` | перцентиль из гистограммы |
| Порядок отладки | `/metrics` → Targets → PromQL → дашборд |
