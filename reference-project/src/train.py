"""Стадия train: обучение модели с трекингом в MLflow.

Точка входа одна и та же и локально, и в CI, и в пайплайне переобучения.
MLflow отключается флагом --no-mlflow (или mlflow.enabled: false):
в CI трекинг-сервера нет, а тесты обучение всё равно прогоняют.
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline

from src.config import TARGET, feature_columns, load_params, resolve
from src.features import build_preprocessor
from src.logging_setup import setup_logging

log = setup_logging()


def build_model(params: dict[str, Any]):
    """Выбор алгоритма по конфигу. Добавление модели = правка params.yaml."""
    name = params["train"]["model"]
    seed = params["seed"]
    cfg = params["train"].get(name, {})

    if name == "logreg":
        return LogisticRegression(random_state=seed, **cfg)
    if name == "random_forest":
        return RandomForestClassifier(random_state=seed, n_jobs=-1, **cfg)
    if name == "gradient_boosting":
        return GradientBoostingClassifier(random_state=seed, **cfg)
    raise ValueError(f"неизвестная модель: {name!r} (см. params.yaml -> train.model)")


def build_pipeline(params: dict[str, Any]) -> Pipeline:
    return Pipeline(
        [("preprocess", build_preprocessor(params)), ("model", build_model(params))]
    )


def compute_metrics(y_true, y_proba, threshold: float) -> dict[str, float]:
    y_pred = (y_proba >= threshold).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "pr_auc": float(average_precision_score(y_true, y_proba)),
        "f1": float(f1_score(y_true, y_pred)),
    }


def git_sha() -> str:
    """Привязка модели к коммиту кода: без неё нельзя воспроизвести прогон."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="Обучить модель оттока")
    parser.add_argument("--no-mlflow", action="store_true", help="не логировать в MLflow")
    args = parser.parse_args()

    params = load_params()
    seed = params["seed"]
    np.random.seed(seed)

    processed = resolve(params["data"]["processed_dir"])
    train_df = pd.read_csv(processed / "train.csv")
    val_df = pd.read_csv(processed / "val.csv")
    cols = feature_columns(params)

    pipe = build_pipeline(params)
    log.info("обучаем %s на %s строках", params["train"]["model"], len(train_df))
    pipe.fit(train_df[cols], train_df[TARGET])

    val_proba = pipe.predict_proba(val_df[cols])[:, 1]
    metrics = compute_metrics(val_df[TARGET], val_proba, params["evaluate"]["threshold"])
    log.info("валидация: %s", metrics)

    model_path = resolve("models/model.joblib")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_path)

    meta = {
        "model": params["train"]["model"],
        "git_sha": git_sha(),
        "python": platform.python_version(),
        "features": cols,
        "val_metrics": metrics,
    }
    with open(resolve("models/model_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    with open(resolve("reports/train_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    if params["mlflow"]["enabled"] and not args.no_mlflow:
        log_to_mlflow(params, pipe, metrics, train_df[cols].head(5))

    log.info("модель сохранена: %s", model_path)


def log_to_mlflow(params, pipe, metrics, input_example) -> None:
    """Логирование прогона. Импорт внутри функции — чтобы обучение
    работало в окружении без mlflow (например, в лёгком CI-джобе)."""
    import mlflow
    import mlflow.sklearn

    cfg = params["mlflow"]
    mlflow.set_tracking_uri(cfg["tracking_uri"])
    mlflow.set_experiment(cfg["experiment_name"])

    name = params["train"]["model"]
    with mlflow.start_run() as run:
        mlflow.log_params({"model": name, "seed": params["seed"]})
        mlflow.log_params({f"{name}.{k}": v for k, v in params["train"].get(name, {}).items()})
        mlflow.log_metrics(metrics)
        mlflow.set_tag("git_sha", git_sha())
        mlflow.log_artifact(str(resolve("params.yaml")))
        mlflow.sklearn.log_model(
            pipe,
            artifact_path="model",
            input_example=input_example,
            registered_model_name=cfg.get("registered_model_name"),
        )
        log.info("MLflow run: %s", run.info.run_id)


if __name__ == "__main__":
    main()
