# Занятие 11. Контейнеризация

## Проблема

Ваш сервис работает. Теперь передайте его в эксплуатацию.
Что нужно рассказать администратору? Версию Python, список пакетов,
переменные окружения, откуда брать модель, какой командой запускать,
что должно быть в системе (компилятор? libgomp?).

Всё это можно не рассказывать, а упаковать.

## Шаг 1. Сначала .dockerignore

Создайте его **до** Dockerfile — иначе первая же сборка отправит
демону гигабайты.

```
.git
.venv
venv
.dvc/cache
.dvc/tmp
data
reports
notebooks
tests
mlruns
mlartifacts
__pycache__
*.pyc
.pytest_cache
.ruff_cache
.github
*.md
```

Docker перед сборкой отправляет демону всю папку целиком —
это «контекст сборки». `.dockerignore` работает на этом шаге,
ещё до любых `COPY`.

## Шаг 2. Зависимости только для инференса

Создайте `docker/requirements-service.txt`. Сравните с основным
`requirements.txt` — сюда **не** попадают mlflow, dvc, prefect, evidently:

```
numpy>=1.26,<3.0
pandas>=2.1,<3.0
scikit-learn>=1.4,<2.0
scipy>=1.11,<2.0
joblib>=1.3,<2.0
PyYAML>=6.0,<7.0
fastapi>=0.110,<1.0
uvicorn[standard]>=0.27,<1.0
pydantic>=2.6,<3.0
prometheus-client>=0.20,<1.0
httpx>=0.27,<1.0
```

Зачем: инструменты обучения и экспериментов в проде не нужны.
Это минус сотни мегабайт и минус поверхность атаки — каждая
лишняя библиотека в проде это потенциальная уязвимость,
которую придётся закрывать.

## Шаг 3. Dockerfile

`docker/Dockerfile`:

```dockerfile
# ---------- стадия сборки ----------
FROM python:3.11-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY docker/requirements-service.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-service.txt

# ---------- финальный образ ----------
FROM python:3.11-slim AS runtime

RUN useradd --create-home --uid 10001 appuser

WORKDIR /app
COPY --from=builder /install /usr/local

COPY src/ ./src/
COPY params.yaml ./params.yaml
COPY models/ ./models/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import httpx,sys; sys.exit(0 if httpx.get('http://localhost:8000/health').json()['model_loaded'] else 1)"

CMD ["uvicorn", "src.service.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Разберите каждое решение:

| Строка | Зачем |
|---|---|
| `python:3.11-slim` | базовый `python:3.11` весит ~1 ГБ, slim — ~130 МБ |
| Две стадии `FROM` | компилятор нужен для сборки колёс, но не в финальном образе |
| `COPY requirements` до `COPY src/` | правка кода не должна инвалидировать кэш установки пакетов |
| `--no-cache-dir` | pip не хранит скачанные архивы внутри образа |
| `useradd` + `USER appuser` | процесс не работает от root |
| `PYTHONUNBUFFERED=1` | логи не буферизуются и видны в `docker logs` сразу |
| `--host 0.0.0.0` | без этого снаружи контейнера сервис недоступен |
| `HEALTHCHECK` | Docker сам понимает, жив ли сервис по существу, а не по факту процесса |

**Про порядок слоёв.** Проверьте на себе: соберите образ, поменяйте одну
строку в `src/service/app.py`, соберите снова. Если пересборка заняла
секунды — порядок правильный. Если минуты — вы скопировали код до установки
зависимостей.

## Шаг 4. Сборка и запуск

```bash
docker build -f docker/Dockerfile -t churn-service:local .
docker images churn-service
```

Цель — меньше 500 МБ.

```bash
docker run --rm -p 8000:8000 churn-service:local
```

В другом терминале:

```bash
curl -s localhost:8000/health | jq
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
  -d @examples/request.json | jq
```

## Шаг 5. Проблема модели

Обратите внимание на `COPY models/`. Модель попала **внутрь** образа.
Это работает, но означает: новая модель = пересборка образа.

Второй вариант — монтировать томом:

```bash
docker run --rm -p 8000:8000 -v $(pwd)/models:/app/models:ro churn-service:local
```

Обсудите оба подхода — на зачёте спросят:

| | Модель в образе | Модель томом |
|---|---|---|
| Плюс | образ самодостаточен, воспроизводим по тегу | обновление без пересборки |
| Минус | новая модель = новая сборка | образ бесполезен без внешнего файла |
| Где применяют | релизные выкаты, CD | разработка, частое переобучение |

Промышленный третий вариант вы уже видели на занятии 7: образ грузит
модель из MLflow Registry по стадии. Тогда обновление модели не требует
ни пересборки, ни монтирования.

## Шаг 6. Диагностика

Полезно уметь заглянуть внутрь:

```bash
docker logs <container_id>                       # логи
docker exec -it <container_id> sh                # шелл внутри
docker inspect <container_id> | jq '.[0].State'  # состояние и healthcheck
docker history churn-service:local               # размер по слоям — видно, что раздуло образ
```

`docker history` — главный инструмент оптимизации: он показывает,
какой слой сколько весит.

## Шаг 7. Цели в Makefile

```make
docker-build:    ## Собрать образ
	docker build -f docker/Dockerfile -t churn-service:local .

docker-run:      ## Запустить контейнер
	docker run --rm -p 8000:8000 -v $(PWD)/models:/app/models:ro churn-service:local
```

## Шаг 8. Воспроизводимый образ и проверка уязвимостей

### Тег — не версия

`FROM python:3.11-slim` сегодня и через месяц дадут **разные** образы:
тег перевешивают при каждом патче. Сборка перестаёт быть воспроизводимой
ровно там, где вы её чинили весь курс.

Зафиксируйте базовый образ по digest:

```bash
docker pull python:3.11-slim
docker inspect --format='{{index .RepoDigests 0}}' python:3.11-slim
```

```dockerfile
FROM python:3.11-slim@sha256:<ваш digest> AS builder
```

Теперь образ собирается из ровно тех байтов, что и вчера.

**Обратная сторона, и её нужно понимать:** патчи безопасности базового
образа сами к вам не приедут. Digest придётся обновлять руками.
Это осознанный размен воспроизводимости на своевременность,
и в реальных проектах его закрывают ботом вроде Dependabot.

### Что внутри образа

```bash
docker scout cves churn-service:local --only-severity critical,high
```

Если `docker scout` недоступен:

```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image --severity HIGH,CRITICAL churn-service:local
```

Запишите в `README.md`, сколько уязвимостей нашлось и что вы с ними
сделали. Правильный ответ не обязательно «починил все» — часть живёт
в системных библиотеках базового образа. Правильный ответ:
«знаю про них, вот эти неприменимы, потому что мы не используем такой-то
компонент».

## Что сдать

- [ ] `.dockerignore`, контекст сборки < 5 МБ
- [ ] `docker/Dockerfile`: multi-stage, non-root, healthcheck
- [ ] `docker/requirements-service.txt` без инструментов обучения
- [ ] Образ < 500 МБ (`docker images`)
- [ ] `docker run` → `/predict` отвечает
- [ ] Правка кода пересобирает образ за секунды, не минуты
- [ ] Базовый образ зафиксирован по digest, в README объяснён размен
- [ ] Отчёт сканера в README: что найдено и что с этим сделано

## Домашнее задание (1,5–2 ч)

1. Оптимизируйте образ. Зафиксируйте в `README.md` таблицу:
   исходный размер → после `.dockerignore` → после slim → после multi-stage →
   после отдельных requirements. С цифрами.
2. Разберите `docker history churn-service:local`: какой слой самый тяжёлый
   и почему. Напишите вывод в `README.md`.
3. Проверьте, что контейнер действительно работает не от root:
   ```bash
   docker run --rm churn-service:local whoami
   ```
   Должно вывести `appuser`.
4. Добавьте в `.github/workflows/ci.yml` job, который собирает образ
   на каждый PR (пока без публикации).

## Полезное

| Команда | Зачем |
|---|---|
| `docker build -f путь -t имя:тег .` | собрать |
| `docker images` | список образов и размеры |
| `docker history образ` | размер по слоям |
| `docker ps -a` | контейнеры, включая остановленные |
| `docker logs -f id` | логи в реальном времени |
| `docker system prune -a` | удалить всё неиспользуемое (осторожно) |
