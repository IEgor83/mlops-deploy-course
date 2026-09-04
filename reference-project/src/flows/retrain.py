"""Пайплайн автоматического переобучения (занятие 16, бонусная часть).

Логика дежурного, записанная кодом:
    свежие данные -> проверить дрейф -> если дрейфа нет, ничего не делать
                  -> если есть: переобучить, сравнить с текущим прод-качеством,
                     промоутить только если стало лучше, затем дёрнуть /reload.

Главная мысль занятия: автопереобучение — это не «переобучать по расписанию»,
а «переобучать по причине, и только если новая модель действительно лучше».
"""
from __future__ import annotations

import json
import subprocess
import sys

import httpx
from prefect import flow, get_run_logger, task

from src.config import resolve


@task(retries=2, retry_delay_seconds=30)
def collect_fresh_data(out: str = "data/raw/fresh.csv") -> str:
    """В учебном проекте свежие данные генерируются; в реальном — выгружаются из хранилища."""
    subprocess.run(
        [sys.executable, "-m", "src.data.generate", "--drift", "--out", out, "--n", "5000"],
        check=True,
        cwd=resolve("."),
    )
    return out


@task
def check_drift(current_csv: str) -> dict:
    subprocess.run(
        [sys.executable, "-m", "src.monitoring.drift", "--current", current_csv],
        check=True,
        cwd=resolve("."),
    )
    with open(resolve("reports/drift.json"), encoding="utf-8") as f:
        return json.load(f)


@task
def retrain() -> dict:
    subprocess.run(["dvc", "repro"], check=True, cwd=resolve("."))
    with open(resolve("reports/eval_metrics.json"), encoding="utf-8") as f:
        return json.load(f)["metrics"]


@task
def current_production_metrics() -> dict:
    """Качество модели, которая сейчас в проде. В реальности — из Registry;
    здесь читаем сохранённый снимок метрик прошлого релиза."""
    path = resolve("reports/production_metrics.json")
    if not path.exists():
        return {"roc_auc": 0.0}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@task
def promote_and_reload(metrics: dict, service_url: str) -> None:
    with open(resolve("reports/production_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    try:
        httpx.post(f"{service_url}/reload", timeout=30).raise_for_status()
    except Exception as exc:  # noqa: BLE001
        get_run_logger().warning("сервис не ответил на /reload: %s", exc)


@flow(name="churn-retrain")
def retrain_flow(service_url: str = "http://localhost:8000", min_gain: float = 0.005) -> str:
    log = get_run_logger()

    fresh = collect_fresh_data()
    drift = check_drift(fresh)
    if not drift["dataset_drift"]:
        log.info("дрейфа нет — переобучение не требуется")
        return "skipped"

    log.info("обнаружен дрейф в %s признаках: %s", drift["n_drifted_columns"], drift["drifted_columns"])
    new_metrics = retrain()
    old_metrics = current_production_metrics()
    gain = new_metrics["roc_auc"] - old_metrics.get("roc_auc", 0.0)

    if gain < min_gain:
        log.warning("новая модель не лучше (прирост %.4f < %.4f) — прод не трогаем", gain, min_gain)
        return "rejected"

    promote_and_reload(new_metrics, service_url)
    log.info("модель промоутнута, прирост ROC-AUC %.4f", gain)
    return "promoted"


if __name__ == "__main__":
    retrain_flow()
