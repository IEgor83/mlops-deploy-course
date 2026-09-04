"""Стадия prepare: сырой CSV -> train/val/test.

Всё, что здесь происходит, должно быть детерминировано: один и тот же
raw-файл и один и тот же seed обязаны дать побайтово одинаковые сплиты.
Именно это проверяет тест test_data.py::test_split_is_deterministic.
"""
from __future__ import annotations

import json

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import TARGET, load_params, resolve
from src.logging_setup import setup_logging

log = setup_logging()


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Минимальная очистка. Правило: никаких неявных решений.

    total_charges пропущен у клиентов первого месяца — это не «шум»,
    а известное свойство выгрузки, поэтому заполняем осмысленно,
    а не медианой по всей выборке.
    """
    df = df.copy()
    missing = df["total_charges"].isna()
    df.loc[missing, "total_charges"] = df.loc[missing, "monthly_charges"] * df.loc[missing, "tenure_months"]
    df = df.drop_duplicates(subset=["customer_id"])
    return df


def main() -> None:
    params = load_params()
    seed = params["seed"]
    d = params["data"]

    raw = pd.read_csv(resolve(d["raw_path"]))
    log.info("прочитано %s строк из %s", len(raw), d["raw_path"])

    df = clean(raw)

    # Двухшаговый сплит: сначала отделяем тест, затем валидацию от остатка.
    # stratify обязателен — классы несбалансированы.
    train_val, test = train_test_split(
        df, test_size=d["test_size"], random_state=seed, stratify=df[TARGET]
    )
    val_ratio = d["val_size"] / (1.0 - d["test_size"])
    train, val = train_test_split(
        train_val, test_size=val_ratio, random_state=seed, stratify=train_val[TARGET]
    )

    out_dir = resolve(d["processed_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, part in (("train", train), ("val", val), ("test", test)):
        part.to_csv(out_dir / f"{name}.csv", index=False)
        log.info("%-5s: %6s строк, churn rate %.4f", name, len(part), part[TARGET].mean())

    stats = {
        name: {"rows": int(len(part)), "churn_rate": round(float(part[TARGET].mean()), 5)}
        for name, part in (("train", train), ("val", val), ("test", test))
    }
    (resolve("reports") / "data_stats.json").parent.mkdir(parents=True, exist_ok=True)
    with open(resolve("reports/data_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
