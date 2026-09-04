"""Стадия evaluate: честная оценка на отложенном тесте + gate качества.

Отдельная стадия нужна, чтобы тестовая выборка не участвовала в обучении
даже случайно, и чтобы CI мог упасть по метрике, а не только по исключению.
"""
from __future__ import annotations

import json
import sys

import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, roc_curve

from src.config import TARGET, feature_columns, load_params, resolve
from src.logging_setup import setup_logging
from src.train import compute_metrics

log = setup_logging()


def main() -> None:
    params = load_params()
    threshold = params["evaluate"]["threshold"]
    gate = params["evaluate"]["min_roc_auc"]

    pipe = joblib.load(resolve("models/model.joblib"))
    test = pd.read_csv(resolve(params["data"]["processed_dir"]) / "test.csv")
    cols = feature_columns(params)

    proba = pipe.predict_proba(test[cols])[:, 1]
    metrics = compute_metrics(test[TARGET], proba, threshold)
    pred = (proba >= threshold).astype(int)

    report = {
        "metrics": metrics,
        "threshold": threshold,
        "confusion_matrix": confusion_matrix(test[TARGET], pred).tolist(),
        "classification_report": classification_report(
            test[TARGET], pred, output_dict=True, zero_division=0
        ),
    }
    reports = resolve("reports")
    reports.mkdir(parents=True, exist_ok=True)
    with open(reports / "eval_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ROC-кривая в формате, который DVC умеет рисовать сам (dvc plots show).
    fpr, tpr, _ = roc_curve(test[TARGET], proba)
    step = max(1, len(fpr) // 200)
    with open(reports / "roc.json", "w", encoding="utf-8") as f:
        json.dump(
            [{"fpr": float(a), "tpr": float(b)} for a, b in zip(fpr[::step], tpr[::step])],
            f,
            indent=2,
        )

    log.info("тест: %s", metrics)
    if metrics["roc_auc"] < gate:
        log.error("ROC-AUC %.4f ниже порога %.4f — модель не проходит gate", metrics["roc_auc"], gate)
        sys.exit(1)
    log.info("gate пройден: ROC-AUC %.4f >= %.4f", metrics["roc_auc"], gate)


if __name__ == "__main__":
    main()
