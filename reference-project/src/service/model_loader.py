"""Загрузка модели для инференса.

Порядок источников важен и отражает реальную эксплуатацию:
  1. MLflow Model Registry, стадия Production — источник правды на проде;
  2. локальный joblib — запасной путь для разработки, CI и демо без стенда.

Сервис не обучает модель и никогда не тренирует её на старте:
инференс и обучение разведены по разным процессам.
"""
from __future__ import annotations

import json
from typing import Any, Optional

import joblib

from src.config import load_params, resolve
from src.logging_setup import setup_logging

log = setup_logging()


class ModelHolder:
    """Держит модель и её версию. Позволяет перезагрузить модель
    без рестарта контейнера (endpoint /reload)."""

    def __init__(self) -> None:
        self.model: Optional[Any] = None
        self.version: str = "not-loaded"

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
            uri = f"models:/{name}/{stage}"
            self.model = mlflow.sklearn.load_model(uri)
            self.version = f"registry:{name}/{stage}"
            log.info("модель загружена из MLflow Registry: %s", uri)
            return True
        except Exception as exc:  # noqa: BLE001
            # Не падаем: недоступный трекинг-сервер не должен ронять инференс.
            log.warning("MLflow Registry недоступен (%s), берём локальный файл", exc)
            return False

    def _load_local(self, params) -> None:
        path = resolve(params["service"]["model_path"])
        self.model = joblib.load(path)
        meta_path = resolve("models/model_meta.json")
        if meta_path.exists():
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            self.version = f"local:{meta.get('model')}@{meta.get('git_sha', 'unknown')}"
        else:
            self.version = "local:unknown"
        log.info("модель загружена локально: %s (%s)", path, self.version)


holder = ModelHolder()
