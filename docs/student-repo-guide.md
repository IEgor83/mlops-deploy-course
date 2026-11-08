# 🚀 Практический guide: как начать работу с репозиторием

**Для студентов, которые никогда не работали с ML-проектами**

---

## Этап 1: Подготовка (до первого занятия)

### Шаг 1.1: Установка инструментов

Убедитесь что установлены:

```bash
# Проверяем Python
python3 --version
# Нужен Python 3.11 или выше

# Проверяем Git
git --version
# Нужен Git 2.0+

# На Windows: установите Make (чтобы make-команды работали)
# Опция 1: Через Chocolatey
choco install make

# Опция 2: Через WSL (рекомендуется для ML-разработки)
# https://learn.microsoft.com/en-us/windows/wsl/install
```

### Шаг 1.2: Клонируем репозиторий

```bash
# Клонируем шаблон
git clone https://github.com/instructor/mlops-template.git
cd mlops-template

# Посмотрим что там
ls -la
# Видим: src/, data/, models/, params.yaml, Makefile, README.md ...
```

### Шаг 1.3: Создаём вашу личную ветку

**ВАЖНО:** Работайте только в своей ветке, никогда не в `main`!

```bash
# Проверяем какая ветка сейчас
git branch -a
# Видим: * main (звёздочка = текущая ветка)

# Создаём свою ветку от main
git checkout -b lesson-1/setup

# Проверяем что мы в правильной ветке
git branch -a
# Видим: lesson-1/setup ← звёздочка здесь

# Готово! Теперь вся работа в этой ветке
```

### Шаг 1.4: Подготавливаем Python окружение

```bash
# Создаём виртуальное окружение
python3 -m venv .venv

# Активируем его
# На macOS / Linux:
source .venv/bin/activate

# На Windows:
.venv\Scripts\Activate.ps1
# Если ошибка "не разрешены скрипты" → запустите PowerShell как Admin:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Проверяем что окружение активно (видим (.venv) в начале строки):
# (.venv) $ python --version
# Python 3.11.x
```

### Шаг 1.5: Устанавливаем зависимости

```bash
# Убедитесь что .venv активно!
# Установливаем пакеты
make install

# Или если make не работает:
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Шаг 1.6: Проверяем что всё готово

```bash
# Запускаем проверку окружения
make check

# Ожидаемый результат:
# environment: OK ✅

# Если ошибка → обратитесь к преподавателю с полным выводом ошибки
```

---

## Этап 2: Первое занятие (рабочий процесс)

### Шаг 2.1: Загружаем задание

```bash
# Преподаватель назвал занятие — открываете lessons/01-*/handout.md
# Или вы читаете instructions в lessons/01-intro-project-setup/handout.md

# Также важно прочитать теорию:
# /theory 1 или docs/theory/01-what-is-mlops.md
```

### Шаг 2.2: Убеждаемся что вы в правильной ветке

```bash
git branch
# Должно быть: * lesson-1/setup
# Если нет → git checkout lesson-1/setup
```

### Шаг 2.3: Выполняем задание пошагово

**Пример: Заполняем params.yaml (Шаг 1 из handout)**

```yaml
# params.yaml

seed: 42  # ваш персональный сид (скажет преподаватель)

data:
  n_samples: 20000
  raw_path: data/raw/churn.csv
  processed_dir: data/processed
  test_size: 0.2
  val_size: 0.1

features:
  numeric:
    - tenure_months
    - monthly_charges
    - total_charges
    - num_support_calls
    - avg_monthly_gb
  categorical:
    - contract_type
    - internet_service
    - payment_method
  binary:
    - has_tech_support
    - is_senior

train:
  model: logreg  # Меняем здесь какую модель использовать!
  logreg:
    C: 1.0
    max_iter: 1000
  random_forest:
    n_estimators: 300
    max_depth: 12
  gradient_boosting:
    n_estimators: 200
    learning_rate: 0.05
```

**Проверяем что конфиг читается:**
```bash
python -c "from src.config import load_params, feature_columns; print(feature_columns(load_params()))"
# Ожидаемый результат:
# ['tenure_months', 'monthly_charges', ... все признаки]
```

### Шаг 2.4: Реализуем функции

**Пример: src/data/prepare.py**

```python
# Файл: src/data/prepare.py
"""Очистка данных и сплит на train/val/test."""

import pandas as pd
from sklearn.model_selection import train_test_split
from src.config import load_params, resolve, TARGET

def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Минимальная очистка."""
    df = df.copy()
    # Пропуски в total_charges → заполняем логически
    missing = df["total_charges"].isna()
    df.loc[missing, "total_charges"] = (
        df.loc[missing, "monthly_charges"] * 
        df.loc[missing, "tenure_months"]
    )
    return df

def main() -> None:
    params = load_params()
    
    # Читаем сырые данные
    df = pd.read_csv(resolve(params["data"]["raw_path"]))
    print(f"Прочитано {len(df)} строк")
    
    # Очищаем
    df = clean(df)
    
    # Двухшаговый сплит: сначала тест, потом валидация
    train_val, test = train_test_split(
        df,
        test_size=params["data"]["test_size"],
        random_state=params["seed"],
        stratify=df[TARGET]  # ← важно для баланса классов!
    )
    
    # Пересчитываем валидацию в доле от остатка
    val_ratio = params["data"]["val_size"] / (1.0 - params["data"]["test_size"])
    train, val = train_test_split(
        train_val,
        test_size=val_ratio,
        random_state=params["seed"],
        stratify=train_val[TARGET]
    )
    
    # Сохраняем
    out_dir = resolve(params["data"]["processed_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    
    train.to_csv(out_dir / "train.csv", index=False)
    val.to_csv(out_dir / "val.csv", index=False)
    test.to_csv(out_dir / "test.csv", index=False)
    
    print(f"train: {len(train)} строк, churn rate {train[TARGET].mean():.2%}")
    print(f"val:   {len(val)} строк, churn rate {val[TARGET].mean():.2%}")
    print(f"test:  {len(test)} строк, churn rate {test[TARGET].mean():.2%}")

if __name__ == "__main__":
    main()
```

**Запускаем:**
```bash
make data
# Или: python -m src.data.prepare
# Ожидаемый результат:
# train: 14000 строк, churn rate 26.54%
# val:   2000 строк, churn rate 26.58%
# test:  4000 строк, churn rate 26.51%
# ← Если rate совпадает = stratify сработал ✅
```

### Шаг 2.5: Реализуем препроцессор

**Пример: src/features.py**

```python
# Файл: src/features.py
"""Построение препроцессора признаков."""

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

def build_preprocessor(params):
    """Создаём цепочку обработки признаков."""
    f = params["features"]
    
    # Числовые признаки: заполнить пропуски медианой, потом масштабировать
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler())
    ])
    
    # Категориальные: заполнить пропуски модой, потом one-hot кодировать
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])
    
    # Объединяем всё в один ColumnTransformer
    return ColumnTransformer([
        ("num", numeric, f["numeric"]),
        ("cat", categorical, f["categorical"]),
        ("bin", "passthrough", f["binary"]),  # Бинарные не меняем
    ], remainder="drop")
```

### Шаг 2.6: Реализуем обучение модели

**Пример: src/train.py (основное)**

```python
# Файл: src/train.py
"""Обучение модели."""

import json
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, f1_score
import joblib

from src.config import load_params, feature_columns, resolve, TARGET
from src.features import build_preprocessor

def build_model(params):
    """Выбираем модель по конфигу."""
    model_name = params["train"]["model"]
    seed = params["seed"]
    config = params["train"].get(model_name, {})
    
    if model_name == "logreg":
        return LogisticRegression(random_state=seed, **config)
    elif model_name == "random_forest":
        return RandomForestClassifier(random_state=seed, **config)
    elif model_name == "gradient_boosting":
        return GradientBoostingClassifier(random_state=seed, **config)
    else:
        raise ValueError(f"Неизвестная модель: {model_name}")

def main():
    params = load_params()
    
    # Читаем данные
    train_df = pd.read_csv(resolve(params["data"]["processed_dir"]) / "train.csv")
    val_df = pd.read_csv(resolve(params["data"]["processed_dir"]) / "val.csv")
    cols = feature_columns(params)
    
    # ✅ Препроцессор и модель в одном Pipeline!
    pipe = Pipeline([
        ("preprocess", build_preprocessor(params)),
        ("model", build_model(params))
    ])
    
    # Обучаем
    print(f"Обучаем {params['train']['model']} на {len(train_df)} строках...")
    pipe.fit(train_df[cols], train_df[TARGET])
    
    # Оцениваем на валидации
    y_pred = pipe.predict(val_df[cols])
    y_proba = pipe.predict_proba(val_df[cols])[:, 1]
    
    metrics = {
        "roc_auc": float(roc_auc_score(val_df[TARGET], y_proba)),
        "f1": float(f1_score(val_df[TARGET], y_pred))
    }
    print(f"Валидация: ROC-AUC={metrics['roc_auc']:.4f}, F1={metrics['f1']:.4f}")
    
    # Сохраняем модель
    model_path = resolve("models/model.joblib")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_path)
    print(f"Модель сохранена в {model_path}")
    
    # Сохраняем метрики в JSON (не в консоль!)
    metrics_path = resolve("reports/train_metrics.json")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

if __name__ == "__main__":
    main()
```

**Запускаем:**
```bash
make train
# Ожидаемый результат:
# Обучаем random_forest на 14000 строках...
# Валидация: ROC-AUC=0.7823, F1=0.3945
# Модель сохранена в models/model.joblib

# Проверяем что метрики сохранились
cat reports/train_metrics.json
# {"roc_auc": 0.7823, "f1": 0.3945}
```

### Шаг 2.7: Проверяем воспроизводимость

**ВАЖНО:** Один из главных признаков правильного кода — он воспроизводится!

```bash
# Запускаем обучение
make train
# Сохраняем метрики
cp reports/train_metrics.json /tmp/metrics_first.json

# Запускаем ещё раз
make train

# Сравниваем
diff /tmp/metrics_first.json reports/train_metrics.json

# Если diff ничего не показал → ✅ ВОСПРОИЗВОДИТСЯ!
# Если показал разницу → ❌ где-то незафиксированный random
```

---

## Этап 3: Сдача работы

### Шаг 3.1: Коммитим изменения

```bash
# Видим какие файлы изменились
git status

# Выглядит примерно так:
# On branch lesson-1/setup
# Changes not staged for commit:
#   modified:   params.yaml
#   modified:   src/data/prepare.py
#   modified:   src/features.py
#   modified:   src/train.py
# Untracked files:
#   reports/train_metrics.json
#   data/processed/

# Добавляем только нужные файлы (NOT данные и модели!)
git add params.yaml
git add src/data/prepare.py
git add src/features.py
git add src/train.py
git add reports/train_metrics.json
git add notebooks/PROBLEMS.md  # (если была)

# Проверяем что добавили правильное
git status
# Должны видеть: Changes to be committed

# Коммитим
git commit -m "Lesson 1: Implement ML pipeline (prepare, features, train)"

# Проверяем логи
git log -1 --oneline
```

### Шаг 3.2: Локальная проверка перед сдачей

```bash
# Запускаем локальный чекер (как это делает бот)
python -m bot.checker --path . --lesson 1

# Ожидаемый результат:
# ✅ Feature columns loaded
# ✅ Data prepared (train/val/test)
# ✅ Model trained
# ✅ Metrics recorded
# ✅ Reproducible
# Score: 2/2 (100%)
```

### Шаг 3.3: Пушим в репозиторий

```bash
# Загружаем вашу ветку
git push origin lesson-1/setup

# GitHub показывает сообщение:
# "Compare & pull request"
# Кликаем на кнопку

# Или вручную создаём PR:
# На GitHub.com → Pull requests → New pull request
# base: main ← compare: lesson-1/setup
# Создаём PR с описанием "Lesson 1: Complete"
```

### Шаг 3.4: Пушим — и всё

Отдельно сдавать занятие не нужно. Работа копится в репозитории,
весь проект сдаётся лично в конце семестра.

```bash
git push
```

Проверьте себя по разделу «Что сдать» в конце методички —
это те же критерии, по которым проект будут оценивать.

---

## 🐛 Типичные проблемы и как их решать

### Проблема 1: "ModuleNotFoundError: No module named 'pandas'"

```bash
# Проверяем активно ли виртуальное окружение
python -c "import sys; print(sys.prefix)"
# Должно показать path с .venv

# Если нет → активируем
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\Activate  # Windows

# Переустанавливаем пакеты
make install
```

### Проблема 2: "FileNotFoundError: data/raw/churn.csv"

```bash
# Нужно сгенерировать данные
make data

# Проверяем что они появились
ls -la data/raw/
ls -la data/processed/
```

### Проблема 3: "Метрики отличаются при перезапуске"

Причина: `random_state` не установлен везде.

```python
# В начале train.py добавьте:
import numpy as np

params = load_params()
np.random.seed(params["seed"])

# Это фиксирует random для numpy
# sklearn использует random_state параметр в моделях
```

### Проблема 4: "make: command not found"

На Windows Makefile может не работать.

**Решение 1:** Установить make
```bash
# Через Chocolatey (нужен Admin)
choco install make

# Или через WSL (рекомендуется для ML)
# Используйте встроенный Linux в Windows
```

**Решение 2:** Запускать команды напрямую
```bash
# Вместо: make train
# Используйте: python -m src.train
```

### Проблема 5: "git push rejected"

```bash
# Обычно это значит что вы пытались пушить в main
# Проверяем текущую ветку
git branch

# Если * main → меняем
git checkout -b lesson-1/setup

# Пушим правильную ветку
git push origin lesson-1/setup
```

---

## ✅ Чек-лист перед сдачей

Перед тем как пушить, убедитесь:

- [ ] Вы в правильной ветке (`lesson-1/setup`)
- [ ] `make check` показывает `environment: OK`
- [ ] `make data` создаёт файлы в `data/processed/`
- [ ] `make train` успешно завершается
- [ ] `reports/train_metrics.json` существует и содержит метрики
- [ ] `python -m bot.checker --path . --lesson 1` показывает 2/2
- [ ] Коммиты добавлены в git
- [ ] Ветка запушена на GitHub
- [ ] PR создан
- [ ] Бот ответил "Accepted"

**Если что-то не работает:** Не ждите что пройдёт в следующий раз — пишите преподавателю с полным текстом ошибки!

---

## 📞 Когда просить помощь

Напишите преподавателю, если:

- ❌ Ошибка и вы не понимаете что означает
- ❌ `make install` не работает на вашей OS
- ❌ Git / GitHub не работает как ожидается
- ❌ Непонятны требования задания

**Как писать:**
```
Тема: Помощь: Lesson 1 ошибка при make train

Текст полностью error:
...скопировать весь текст ошибки...

Вывод: git log -1 (последний коммит)
...скопировать...

Шаги которые я сделал:
1. Клонировал репо
2. Создал .venv
3. make install
4. make data
5. make train ← ошибка здесь
```

Преподаватель значительно быстрее ответит если увидит:
- Полный текст ошибки (не "не работает")
- Вывод `git log` и `git status`
- Шаги которые вы делали
- Python версию (`python --version`)
- OS (Windows/macOS/Linux)

---

**Готовы? Тогда вперёд! 🚀**

Следующее: прочитайте `/theory 1` и придите на занятие!
