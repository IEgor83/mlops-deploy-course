# Занятие 12. Локальный прод-стенд на docker-compose

## Проблема

Ваш сервис живёт в контейнере. Но ему нужны соседи: MLflow — чтобы взять
модель из Registry, MinIO — чтобы хранить артефакты, Postgres — чтобы
MLflow хранил метаданные.

Запускать пять контейнеров руками с флагами `--network`, `--env`, `-p`
можно ровно один раз. Дальше нужен файл.

## Шаг 1. Минимальный стенд

`docker/docker-compose.yml`:

```yaml
name: churn-mlops

services:
  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    image: churn-service:local
    ports:
      - "8000:8000"
    environment:
      LOG_LEVEL: INFO
      MLFLOW_TRACKING_URI: http://mlflow:5000
    volumes:
      - ../models:/app/models:ro
    depends_on:
      mlflow:
        condition: service_started
    restart: unless-stopped

  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.11.3
    ports:
      - "5000:5000"
    command: >
      mlflow server --host 0.0.0.0 --port 5000
      --backend-store-uri sqlite:///mlflow.db
```

```bash
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml ps
```

**Важнее всего здесь одна строка:** `MLFLOW_TRACKING_URI: http://mlflow:5000`.

Внутри сети compose контейнеры видят друг друга **по имени сервиса**.
`localhost` внутри контейнера `api` означает сам контейнер `api`,
а не ваш ноутбук. Это ошибка, которую делают все и по одному разу.

Секция `ports:` — это проброс из хоста внутрь, он нужен **вам**,
чтобы открыть браузер. Сервисам между собой порты пробрасывать не нужно.

## Шаг 2. Postgres и healthcheck

SQLite не годится для нескольких клиентов. Добавьте базу:

```yaml
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: mlflow
      POSTGRES_PASSWORD: mlflow
      POSTGRES_DB: mlflow
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mlflow"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  pgdata:
```

И перенастройте MLflow:

```yaml
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.11.3
    ports:
      - "5000:5000"
    command: >
      mlflow server --host 0.0.0.0 --port 5000
      --backend-store-uri postgresql://mlflow:mlflow@postgres:5432/mlflow
    depends_on:
      postgres:
        condition: service_healthy
```

**Про `condition: service_healthy`.** Обычный `depends_on` ждёт только
запуска контейнера. Postgres стартует за 3 секунды, а принимать соединения
начинает через 8 — MLflow за это время успеет упасть. `healthcheck`
описывает, что значит «готов», а `condition` заставляет ждать именно этого.

## Шаг 3. MinIO для артефактов

```yaml
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - miniodata:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 5s
      timeout: 3s
      retries: 10
```

MLflow нужно сказать, куда складывать артефакты:

```yaml
  mlflow:
    environment:
      MLFLOW_S3_ENDPOINT_URL: http://minio:9000
      AWS_ACCESS_KEY_ID: minioadmin
      AWS_SECRET_ACCESS_KEY: minioadmin
    command: >
      mlflow server --host 0.0.0.0 --port 5000
      --backend-store-uri postgresql://mlflow:mlflow@postgres:5432/mlflow
      --artifacts-destination s3://mlflow/
    depends_on:
      postgres:
        condition: service_healthy
      minio:
        condition: service_healthy
```

Не забудьте создать бакет `mlflow` в консоли MinIO (http://localhost:9001).

Добавьте в `volumes:` в конце файла `miniodata:`.

## Шаг 4. Запуск и проверка

```bash
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f mlflow
```

Что должно открываться:

| Адрес | Что |
|---|---|
| http://localhost:8000/docs | ваш сервис |
| http://localhost:5000 | MLflow |
| http://localhost:9001 | MinIO (minioadmin / minioadmin) |

**Если порт 5000 занят** (на macOS его использует AirPlay Receiver):
поменяйте проброс на `"5001:5000"` — внутри сети порт остаётся 5000,
меняется только дырка наружу.

## Шаг 5. Сквозная проверка

Главная проверка занятия — модель едет из Registry в сервис:

```bash
# обучаем, логируя в MLflow внутри стенда
MLFLOW_TRACKING_URI=http://localhost:5000 python -m src.train

# в UI переводим версию в Production, затем
curl -s -X POST localhost:8000/reload | jq
curl -s localhost:8000/health | jq
```

В `model_version` должно появиться `registry:churn-classifier/Production`.
Если там `local:` — сервис не достучался до MLflow, смотрите
`docker compose logs api`.

## Шаг 6. Профиль для слабых машин

Полный стенд требует около 3 ГБ памяти. Добавьте облегчённый режим:

```yaml
  postgres:
    profiles: ["full"]
  minio:
    profiles: ["full"]
```

Сервисы без `profiles` поднимаются всегда, с профилем — только по запросу:

```bash
docker compose -f docker/docker-compose.yml up -d                  # только api + mlflow
docker compose -f docker/docker-compose.yml --profile full up -d   # всё
```

## Шаг 7. Makefile и уборка

```make
up:              ## Поднять стенд
	docker compose -f docker/docker-compose.yml up -d

down:            ## Погасить стенд
	docker compose -f docker/docker-compose.yml down
```

Разница, которую важно понимать:

| Команда | Что делает |
|---|---|
| `docker compose down` | останавливает и удаляет контейнеры, **тома остаются** |
| `docker compose down -v` | то же плюс удаляет тома — данные MLflow и MinIO пропадут |

## Что сдать

- [ ] `docker/docker-compose.yml` с четырьмя сервисами
- [ ] `docker compose up -d` поднимает стенд одной командой
- [ ] `healthcheck` + `condition: service_healthy` у postgres и minio
- [ ] Сервисы обращаются друг к другу по именам, не по localhost
- [ ] Сервис грузит модель из Registry: `model_version` начинается с `registry:`
- [ ] `make up` / `make down` работают

## Домашнее задание (1,5–2 ч)

1. Добавьте сервис-инициализатор, который сам создаёт бакет `mlflow`
   в MinIO при старте стенда (образ `minio/mc`, команда `mc mb`).
   Стенд должен подниматься на чистой машине без ручных действий.
2. Вынесите пароли из compose-файла в `.env` (файл в `.gitignore`),
   положите рядом `.env.example`. Проверьте, что стенд поднимается.
3. Нарисуйте схему стенда: сервисы, порты, кто с кем общается,
   где тома. Схему (картинкой или в mermaid) вставьте в `README.md`.
4. Проверьте отказоустойчивость: `docker compose stop mlflow`,
   затем запрос в `/predict`. Сервис обязан продолжать работать
   на локальной модели. Опишите результат в `README.md`.

Четвёртый пункт — проверка фолбэка, который вы сделали на занятии 7.

## Полезное

| Команда | Зачем |
|---|---|
| `docker compose up -d` | поднять в фоне |
| `docker compose ps` | статус сервисов |
| `docker compose logs -f имя` | логи одного сервиса |
| `docker compose exec api sh` | шелл внутри сервиса |
| `docker compose restart имя` | перезапустить один |
| `docker compose config` | итоговый конфиг после подстановки переменных |
