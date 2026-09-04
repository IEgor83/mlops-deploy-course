# Единая точка входа во все операции проекта.
# Правило курса: если команду нужно помнить наизусть — она должна быть здесь.
.PHONY: help install data prepare train eval pipeline test lint format serve docker-build docker-run up down drift clean all

PY := python

help:            ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:         ## Установить зависимости
	$(PY) -m pip install -U pip
	$(PY) -m pip install -r requirements.txt -r requirements-dev.txt

data:            ## Сгенерировать сырой датасет
	$(PY) -m src.data.generate

prepare:         ## Подготовить train/val/test
	$(PY) -m src.data.prepare

train:           ## Обучить модель
	$(PY) -m src.train

train-local:     ## Обучить без MLflow (для CI и работы офлайн)
	$(PY) -m src.train --no-mlflow

eval:            ## Оценить модель на тесте и проверить gate качества
	$(PY) -m src.evaluate

pipeline:        ## Воспроизвести пайплайн через DVC
	dvc repro

test:            ## Прогнать тесты
	pytest

lint:            ## Проверить стиль
	ruff check src tests

format:          ## Отформатировать код
	ruff check --fix src tests
	ruff format src tests

serve:           ## Запустить сервис локально
	uvicorn src.service.app:app --host 0.0.0.0 --port 8000 --reload

docker-build:    ## Собрать образ
	docker build -f docker/Dockerfile -t churn-service:local .

docker-run:      ## Запустить контейнер
	docker run --rm -p 8000:8000 -v $(PWD)/models:/app/models:ro churn-service:local

up:              ## Поднять стенд (api + mlflow + minio + prometheus + grafana)
	docker compose -f docker/docker-compose.yml up -d

down:            ## Погасить стенд
	docker compose -f docker/docker-compose.yml down -v

drift:           ## Отчёт о дрейфе на данных 'следующего квартала'
	$(PY) -m src.data.generate --drift --out data/raw/fresh.csv --n 5000
	$(PY) -m src.monitoring.drift --current data/raw/fresh.csv

clean:           ## Удалить артефакты
	rm -rf models/*.joblib models/*.json reports/* data/processed/* data/raw/*.csv
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

all: data prepare train-local eval test lint  ## Полный прогон без внешних сервисов
