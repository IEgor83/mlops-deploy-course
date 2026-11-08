# ⚡ Quick Start: шпаргалка на одной странице

**Распечатайте это и положите на стол! 📋**

---

## 🏗️ Структура проекта (5 мин)

```
my-project/
├── params.yaml           ← ВСЕ параметры здесь! 🎯
├── Makefile             ← make install, make train, make test
├── src/                 ← Ваш код
│   ├── train.py         ← Обучение
│   ├── features.py      ← Препроцессор
│   └── data/prepare.py  ← Очистка данных
├── data/                ← Данные (НЕ коммитим!)
├── models/              ← Модели (НЕ коммитим!)
└── tests/               ← pytest тесты
```

**Правило:** Параметры → `params.yaml`, код → в `src/`, данные/модели → `.gitignore`

---

## 🚀 Первый запуск (10 мин)

```bash
# 1. Клонируем
git clone https://github.com/instructor/mlops-template.git
cd mlops-template

# 2. Окружение
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# Или: .venv\Scripts\Activate  (Windows)

# 3. Установка пакетов
make install

# 4. Проверка
make check
# ✅ Должно быть: environment: OK
```

---

## 📝 Git workflow (работаем с веткам!)

```bash
# Перед каждым занятием:
git checkout -b lesson-N/description

# В конце дня:
git add .                          # (но не data/ и models/!)
git commit -m "Lesson N: complete"
git push origin lesson-N/description

```

**ВАЖНО:** Отдельно сдавать лабу не нужно — достаточно запушить.
Весь проект сдаётся лично в конце семестра.

---

## 🎯 Основные команды

| Команда | Что делает |
|---------|-----------|
| `make install` | Установить зависимости |
| `make check` | Проверить окружение |
| `make data` | Сгенерировать/подготовить данные |
| `make train` | Обучить модель |
| `make test` | Запустить pytest |
| `make lint` | Проверить качество кода (ruff) |
| `make format` | Автоматически отформатировать код |
| `make help` | Список всех команд |

---

## 🔧 Параметры (params.yaml)

```yaml
seed: 42                    # Фиксируем случайность

data:
  raw_path: data/raw/churn.csv
  test_size: 0.2            # 20% на тест
  val_size: 0.1             # 10% на валидацию

features:
  numeric: [tenure_months, monthly_charges, ...]
  categorical: [contract_type, ...]
  binary: [has_tech_support, ...]

train:
  model: random_forest      # logreg | random_forest | gradient_boosting
  random_forest:
    n_estimators: 300
    max_depth: 12
```

**Правило:** Меняете параметр? → только в params.yaml, не в коде!

---

## 💡 Типичный код на занятии

### Файл: `src/data/prepare.py`

```python
from src.config import load_params, resolve, TARGET
from sklearn.model_selection import train_test_split

def main():
    params = load_params()
    
    # Читаем
    df = pd.read_csv(resolve(params["data"]["raw_path"]))
    
    # Чистим (если нужно)
    df = clean(df)
    
    # Сплитим с stratify
    train, test = train_test_split(
        df, test_size=params["data"]["test_size"],
        random_state=params["seed"],
        stratify=df[TARGET]  ← не забыть!
    )
    
    # Сохраняем
    train.to_csv(resolve(params["data"]["processed_dir"]) / "train.csv", index=False)
    test.to_csv(resolve(params["data"]["processed_dir"]) / "test.csv", index=False)

if __name__ == "__main__":
    main()
```

### Файл: `src/train.py`

```python
from sklearn.pipeline import Pipeline

def main():
    params = load_params()
    train_df = pd.read_csv("data/processed/train.csv")
    
    # ✅ Препроцессор и модель вместе!
    pipe = Pipeline([
        ("preprocess", build_preprocessor(params)),
        ("model", build_model(params))
    ])
    pipe.fit(train_df[features], train_df[TARGET])
    
    # Оцениваем
    y_proba = pipe.predict_proba(val_df[features])[:, 1]
    auc = roc_auc_score(val_df[TARGET], y_proba)
    
    # Сохраняем
    joblib.dump(pipe, "models/model.joblib")
    # И метрики в JSON!
    json.dump({"roc_auc": auc}, open("reports/metrics.json", "w"))
```

---

## ✅ Проверка перед сдачей

```bash
# 1. Локальная проверка
make test
python -m bot.checker --path . --lesson 1

# 2. Git проверка
git status              # Всё ли закоммичено?
git log -3 --oneline    # Видны ваши коммиты?

# 3. Тест воспроизводимости
make train && cp reports/metrics.json /tmp/m1.json
make train && diff /tmp/m1.json reports/metrics.json
# Если ничего → ✅ воспроизводится!

# 4. Git push
git push origin lesson-N/description

```

---

## 🐛 Быстрые решения ошибок

| Ошибка | Решение |
|--------|---------|
| `ModuleNotFoundError: No module 'pandas'` | `source .venv/bin/activate` → `make install` |
| `FileNotFoundError: data/raw/churn.csv` | `make data` генерирует данные |
| `make: command not found` | На Windows: `choco install make` или используйте `python -m src.train` |
| `permission denied: .venv/bin/activate` | Windows: используйте `.venv\Scripts\Activate.ps1` |
| Разные метрики при повторе | Добавить `np.random.seed(params["seed"])` в начало main |
| `git push rejected` | Проверить что вы в правильной ветке (`git branch`) |

---

## 📚 Важные файлы

| Файл | Когда нужен |
|------|-----------|
| `docs/student-guide.md` | Полная памятка студента |
| `docs/student-repo-guide.md` | Как работать с git и репо |
| `docs/theory/01-what-is-mlops.md` | Теория перед Lesson 1 |
| `lessons/01-intro-project-setup/handout.md` | Что сдать на Lesson 1 |

---

## 🎯 Что делать каждую неделю

```
ПЕРЕД ЗАНЯТИЕМ (вечер перед, 30 мин)
├─ Читаете конспект docs/theory/
└─ Смотрите lessons/NN-*/handout.md (что делать)

НА ЗАНЯТИИ (2 часа)
├─ Делаете основную работу по методичке
└─ Преподаватель помогает если застряли

ДОМА ПОСЛЕ ЗАНЯТИЯ (1.5-2 часа)
├─ Доделываете домашнее задание
├─ Сверяетесь с разделом «Что сдать» в методичке
└─ Коммитите и пушите

В КОНЦЕ СЕМЕСТРА
└─ Показываете весь проект лично на зачёте
```

---

## 📞 SOS кнопка

```bash
# Что-то не работает? Выполните:

# 1. Покажите ошибку
python -m bot.checker --path . --lesson 1

# 2. Статус проекта
git status
git log -1 --oneline

# 3. Версии
python --version
git --version

# 4. Скопируйте ВСЕ ВЫ ВЫШЕ и напишите преподавателю
```

Преподаватель поймёт проблему если вы покажете полный вывод, а не просто "не работает" 😊

---

## 🌟 Pro tips

- 💾 **Часто коммитьте** (`git commit`) → легче откатываться
- 📝 **Читайте error-ы** → первая строка обычно говорит что не так
- 🔧 **Спросите в группе или у преподавателя** → когда не понимаете как сделать
- ❓ **Спрашивайте рано** → лучше на первый день, чем в последний
- 🧪 **Тестируйте локально** → перед тем как пушить в github
- 📊 **Смотрите метрики** → они говорят работает ли модель
- 🚀 **Ускоритесь** → каждое занятие немного сложнее предыдущего

---

**Сохраните этот файл как закладку! Вы вернётесь сюда много раз 📌**

Удачи! 🍀
