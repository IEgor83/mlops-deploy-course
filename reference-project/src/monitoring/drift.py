"""Отчёт о дрейфе данных и качества (занятие 15).

Сравниваем reference (данные, на которых учили) с current (то, что реально
приходит в сервис). Скрипт выдаёт HTML для человека и JSON для автоматики:
именно JSON читает пайплайн переобучения на занятии 16.

ВАЖНО про версии: API Evidently менялся между минорными релизами.
Здесь код под evidently 0.4.x, версия зафиксирована в requirements.txt.
Если поставили другую — сначала выровняйте версию, а не правьте импорты.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.config import TARGET, feature_columns, load_params, resolve
from src.logging_setup import setup_logging

log = setup_logging()


def build_report(reference: pd.DataFrame, current: pd.DataFrame, columns: list):
    from evidently.metric_preset import DataDriftPreset, TargetDriftPreset
    from evidently.report import Report

    presets = [DataDriftPreset()]
    if TARGET in reference.columns and TARGET in current.columns:
        presets.append(TargetDriftPreset())

    keep = [c for c in columns + [TARGET] if c in reference.columns and c in current.columns]
    report = Report(metrics=presets)
    report.run(reference_data=reference[keep], current_data=current[keep])
    return report


def summarize(report) -> dict:
    """Достаём из отчёта то немногое, по чему принимается решение."""
    payload = report.as_dict()
    drift_result = payload["metrics"][0]["result"]
    by_column = drift_result.get("drift_by_columns", {})
    drifted = sorted(
        (name for name, info in by_column.items() if info.get("drift_detected")),
    )
    return {
        "dataset_drift": bool(drift_result.get("dataset_drift", False)),
        "share_of_drifted_columns": float(drift_result.get("share_of_drifted_columns", 0.0)),
        "n_drifted_columns": int(drift_result.get("number_of_drifted_columns", 0)),
        "drifted_columns": drifted,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Отчёт о дрейфе данных")
    parser.add_argument("--reference", default=None, help="эталонный CSV (по умолчанию train)")
    parser.add_argument("--current", required=True, help="текущий CSV (свежие данные)")
    parser.add_argument("--out-html", default="reports/drift.html")
    parser.add_argument("--out-json", default="reports/drift.json")
    args = parser.parse_args()

    params = load_params()
    ref_path = Path(args.reference) if args.reference else resolve(params["data"]["processed_dir"]) / "train.csv"
    reference = pd.read_csv(ref_path)
    current = pd.read_csv(args.current)
    log.info("reference=%s строк, current=%s строк", len(reference), len(current))

    report = build_report(reference, current, feature_columns(params))

    out_html = resolve(args.out_html)
    out_json = resolve(args.out_json)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    report.save_html(str(out_html))

    summary = summarize(report)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log.info("дрейф датасета: %s, признаков с дрейфом: %s %s",
             summary["dataset_drift"], summary["n_drifted_columns"], summary["drifted_columns"])
    log.info("отчёт: %s", out_html)


if __name__ == "__main__":
    main()
