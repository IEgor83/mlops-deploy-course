# 🔧 Методичка по проблемам и решениям

**Для студентов курса MLOps**

Telegram: https://t.me/+3N7q9X1YIWxkN2Iy  
Email: alsu124@mail.ru

---

## 📋 СОДЕРЖАНИЕ

- [ДО ПЕРВОГО ЗАНЯТИЯ](#до-первого-занятия)
- [ЗАНЯТИЕ 1-5: Фундамент](#занятие-1-5-фундамент)
- [ЗАНЯТИЕ 6-9: Качество](#занятие-6-9-качество)
- [ЗАНЯТИЕ 10-13: Production](#занятие-10-13-production)
- [ЗАНЯТИЕ 14-17: Эксплуатация](#занятие-14-17-эксплуатация)
- [Универсальные проблемы](#универсальные-проблемы)

---

## ДО ПЕРВОГО ЗАНЯТИЯ

### ❌ Проблема: "python --version показывает 3.9, но мне нужен 3.11"

**Симптомы:**
```bash
$ python --version
Python 3.9.0

$ python3 --version
Python 3.11.0  ← есть нужная версия!
```

**Причина:**
- На машине установлены две версии Python
- Команда `python` указывает на старую версию
- Нужно использовать `python3` или установить правильную версию

**Решение:**

**Вариант 1: Использовать python3 (быстро)**
```bash
# Везде где видите "python" → используйте "python3"
python3 -m venv .venv  # вместо python -m venv
python3 -m pip install -r requirements.txt
```

**Вариант 2: Переустановить Python (правильно)**
```bash
# На macOS через Homebrew:
brew install python@3.11
brew unlink python@3.9

# На Linux (Ubuntu/Debian):
sudo apt-get install python3.11
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# На Windows:
# Скачайте Python 3.11 с python.org и переустановите
```

**Проверка:**
```bash
python --version  # должно быть 3.11+
python -m venv .venv
```

---

### ❌ Проблема: "make: command not found"

**Симптомы:**
```bash
$ make install
bash: make: command not found
```

**Причина:**
- Make не установлен (обычно на Windows)
- На macOS может быть проблема с PATH

**Решение:**

**На macOS:**
```bash
# Вариант 1: через Homebrew
brew install make

# Вариант 2: через Command Line Tools
xcode-select --install

# Проверка:
make --version
```

**На Linux (Ubuntu/Debian):**
```bash
sudo apt-get install build-essential
# Проверка:
make --version
```

**На Windows:**

Вариант 1: Установить через Chocolatey (Admin PowerShell):
```powershell
choco install make
```

Вариант 2: Использовать Windows Subsystem for Linux (WSL)
```bash
# В WSL терминале:
sudo apt-get install build-essential
```

Вариант 3: Запускать команды напрямую (если make не хочет устанавливаться)
```bash
# Вместо: make train
# Используйте: python -m src.train

# Вместо: make test
# Используйте: python -m pytest bot/tests/
```

---

### ❌ Проблема: "git clone не работает — нужен SSH ключ"

**Симптомы:**
```bash
$ git clone git@github.com:user/repo.git
Permission denied (publickey).
fatal: Could not read from remote repository.
```

**Причина:**
- GitHub требует SSH ключ для приватных репозиториев
- У вас нет SSH ключа или он не установлен в GitHub

**Решение:**

**Шаг 1: Генерируем SSH ключ**
```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
# Нажимаем Enter везде (сохраняет с дефолтным именем и без пароля)

# Проверяем что создалось:
ls ~/.ssh/
# Должны видеть: id_ed25519, id_ed25519.pub
```

**Шаг 2: Добавляем публичный ключ на GitHub**
```bash
# Копируем публичный ключ
cat ~/.ssh/id_ed25519.pub
# Появится строка типа: ssh-ed25519 AAAAC3Nza...

# Переходим на GitHub Settings → SSH and GPG keys → New SSH key
# Вставляем содержимое id_ed25519.pub
```

**Шаг 3: Проверяем что работает**
```bash
ssh -T git@github.com
# Должно вывести: Hi username! You've successfully authenticated...
```

**Альтернатива: Использовать HTTPS вместо SSH**
```bash
# Если SSH не хочет работать, используйте HTTPS:
git clone https://github.com/user/repo.git
# GitHub попросит токен вместо пароля (Generate Personal Access Token)
```

---

### ❌ Проблема: "Что такое venv и зачем он нужен?"

**Симптомы:**
```
Я просто pip install всё что нужно, почему нужен venv?
```

**Объяснение:**

**Без venv (плохо):**
```
System Python 3.11
├─ django 3.2
├─ numpy 1.20
├─ sklearn 0.24
└─ (и ещё 100 пакетов установлено системно)

Проект 1 нужен: sklearn 0.24
Проект 2 нужен: sklearn 1.0
→ КОНФЛИКТ! Одновременно не может быть две версии
```

**С venv (хорошо):**
```
System Python 3.11 (чистая!)
├─ venv_project1/
│  ├─ sklearn 0.24
│  ├─ numpy 1.20
│  └─ requirements.txt ← список что здесь нужно
└─ venv_project2/
   ├─ sklearn 1.0
   ├─ numpy 1.30
   └─ requirements.txt ← другой список
```

**Решение (как правильно):**
```bash
# Создаём venv
python3 -m venv .venv

# Активируем (зависит от OS)
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\Activate

# Проверяем что активировалось (видим (.venv) в начале строки):
# (.venv) $ pip install -r requirements.txt

# Деактивируем (когда закончили работать):
deactivate
```

---

### ❌ Проблема: "make install работает но `make check` падает"

**Симптомы:**
```bash
$ make check
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'pandas'
```

**Причина:**
- pip install запустился не в правильном venv
- Или venv не активирован

**Решение:**
```bash
# Убедитесь что .venv активирован:
# На macOS/Linux: видите (.venv) в начале строки?
# Если нет:
source .venv/bin/activate

# Переустановите зависимости:
pip install -r requirements.txt

# Проверьте:
python -c "import pandas; print('OK')"

# Запустите check:
make check
```

---

## ЗАНЯТИЕ 1-5: Фундамент

### ❌ Проблема: "ROC-AUC очень низкий (0.52) вместо 0.78"

**Симптомы:**
```bash
$ make train
...
ROC-AUC: 0.52  ← Очень низко!
```

**Возможные причины (проверяйте по очереди):**

**Причина 1: Забыли stratify в train_test_split**
```python
# ❌ НЕПРАВИЛЬНО:
train, test = train_test_split(df, test_size=0.2, random_state=42)

# ✅ ПРАВИЛЬНО:
train, test = train_test_split(
    df, test_size=0.2, 
    random_state=42,
    stratify=df["churn"]  ← не забывайте это!
)
```

**Причина 2: customer_id попал в признаки**
```python
# ❌ НЕПРАВИЛЬНО:
X = df[["customer_id", "age", "charges"]]
# customer_id это идентификатор, не признак!
# Модель запомнит конкретных клиентов вместо закономерности

# ✅ ПРАВИЛЬНО:
X = df[["age", "charges", "tenure"]]  # только признаки, без ID!
```

**Причина 3: churn попал в признаки**
```python
# ❌ НЕПРАВИЛЬНО:
X = df[["age", "churn", "charges"]]
y = df["churn"]
# Модель видит ответ в данных!

# ✅ ПРАВИЛЬНО:
X = df[["age", "charges"]]
y = df["churn"]
```

**Причина 4: Неправильная подготовка данных**
```python
# ❌ НЕПРАВИЛЬНО:
# Заполняем пропуски по среднему от всего датасета
df["total_charges"].fillna(df["total_charges"].mean())

# ✅ ПРАВИЛЬНО:
# Заполняем логично (если это first month, то просто monthly_charges):
df["total_charges"] = np.where(
    df["total_charges"].isna(),
    df["monthly_charges"] * df["tenure_months"],
    df["total_charges"]
)
```

**Решение:**
```bash
# 1. Проверьте src/data/prepare.py
python -c "from src.data.prepare import *; print('OK')"

# 2. Посмотрите данные:
python -c "import pandas as pd; df = pd.read_csv('data/processed/train.csv'); print(df.info())"

# 3. Перегенерируйте данные:
make data
make train

# 4. Проверьте метрики:
cat reports/train_metrics.json
```

---

### ❌ Проблема: "make train работает, но второй раз дает РАЗНЫЕ метрики"

**Симптомы:**
```bash
$ make train
ROC-AUC: 0.785

$ make train  ← второй раз
ROC-AUC: 0.782  ← РАЗНЫЕ!
```

**Причина:**
- Где-то в коде есть случайные числа без фиксирования seed

**Решение (проверяйте по очереди):**

**Шаг 1: Добавьте seed в train.py**
```python
# В начале main():
params = load_params()
seed = params["seed"]

# ДОБАВЬТЕ ЭТО:
np.random.seed(seed)  ← фиксируем numpy
tf.random.set_seed(seed)  ← если используете tensorflow

# И убедитесь что все функции используют random_state:
train_test_split(..., random_state=seed)
RandomForest(..., random_state=seed)
```

**Шаг 2: Проверьте prepare.py**
```python
# В prepare.py тоже нужно фиксировать:
train, test = train_test_split(
    df, test_size=0.2,
    random_state=params["seed"],  ← не забыли?
    stratify=df["churn"]
)
```

**Шаг 3: Проверьте features.py**
```python
# OneHotEncoder тоже может быть недетерминирован:
OneHotEncoder(
    handle_unknown="ignore",
    sparse_output=False,
    random_state=seed  ← добавьте если есть параметр
)
```

**Шаг 4: Проверьте что работает**
```bash
# Запустите два раза и сравните метрики:
make train && cat reports/train_metrics.json > /tmp/m1.json
make train && cat reports/train_metrics.json > /tmp/m2.json
diff /tmp/m1.json /tmp/m2.json
# Должно быть ПУСТО (идентичные)
```

---

### ❌ Проблема: "Я не понимаю что такое Pipeline"

**Симптомы:**
```
Почему препроцессор и модель должны быть вместе?
Это же усложняет код!
```

**Объяснение (пример):**

**БЕЗ Pipeline (ПЛОХО):**
```python
# В ноутбуке (обучение):
scaler = StandardScaler().fit(X_train)
X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = RandomForest()
model.fit(X_train_scaled, y_train)

# На сервере (prediction), кто-то забыл scaler:
X_prod = load_data()  # raw данные
predictions = model.predict(X_prod)  # модель видит ненормализованные данные!
# Результат: полный мусор (ROC-AUC = 0.32 вместо 0.85)
```

**С Pipeline (ХОРОШО):**
```python
# Обучение:
pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("model", RandomForest())
])
pipe.fit(X_train, y_train)  # всё вместе

# На сервере:
X_prod = load_data()  # raw данные
predictions = pipe.predict(X_prod)  # scaler + model вместе!
# Результат: правильный (ROC-AUC = 0.85 как и было)
```

**Вывод:**
Pipeline гарантирует что при обучении и prediction используются ОДНИ И ТЕ ЖЕ преобразования.

**Решение (как писать код):**
```python
# ✅ ВСЕГДА используйте Pipeline:
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ("preprocess", build_preprocessor(params)),  # ваша функция
    ("model", build_model(params))               # ваша функция
])

# Обучение:
pipe.fit(X_train, y_train)

# Prediction:
predictions = pipe.predict(X_test)

# Сохранение:
joblib.dump(pipe, "models/model.joblib")
```

---

### ❌ Проблема: "git clone работает но я не знаю как начать"

**Симптомы:**
```bash
$ git clone https://github.com/...
$ cd my-ml-project
$ ls
# Вижу файлы но не знаю что дальше
```

**Решение (пошагово):**

```bash
# Шаг 1: Создаём и активируем venv
python3 -m venv .venv
source .venv/bin/activate  # или .venv\Scripts\Activate на Windows

# Шаг 2: Устанавливаем зависимости
pip install -r requirements.txt

# Шаг 3: Проверяем что всё работает
python -m bot.checker --path . --lesson 1
# Должно быть: 0/X (пока ничего не сделано)

# Шаг 4: Генерируем данные
make data

# Шаг 5: Запускаем первое обучение
make train

# Шаг 6: Проверяем результат
cat reports/train_metrics.json
```

---

### ❌ Проблема: "Я создал feature branch но потом случайно коммитил в main"

**Симптомы:**
```bash
$ git status
On branch main
# Видю свои изменения но я же хотел в feature ветку!
```

**Решение:**

**Вариант 1: Если вы ещё не коммитили**
```bash
# Сохраняем изменения временно
git stash

# Переходим в правильную ветку
git checkout -b lesson-1/my-changes

# Восстанавливаем изменения
git stash pop

# Теперь коммитим в правильной ветке
git add .
git commit -m "Lesson 1: my changes"
git push origin lesson-1/my-changes
```

**Вариант 2: Если вы уже коммитили в main**
```bash
# Смотрим сколько коммитов назад мы были в правильной ветке
git log --oneline | head -5

# Создаём новую ветку от текущей позиции
git checkout -b lesson-1/my-changes

# Возвращаемся в main и откатываем коммиты
git checkout main
git reset --hard origin/main  # откатываем до удалённого main

# Переходим обратно в вашу ветку (там ваши коммиты)
git checkout lesson-1/my-changes

# Пушим
git push origin lesson-1/my-changes
```

---

### ❌ Проблема: "Pre-commit не пускает коммит — ruff error"

**Симптомы:**
```bash
$ git commit -m "Lesson 1"
❌ ruff check failed

ERROR: /Users/me/project/src/train.py:42:80: E501 Line too long
```

**Причина:**
- В коде слишком длинные строки (>88 символов)
- Или другие проблемы стиля кода

**Решение:**

**Вариант 1: Автоматически исправить (быстро)**
```bash
# ruff может автоматически исправить многие ошибки
ruff check --fix src/

# Потом:
git add .
git commit -m "Lesson 1"
```

**Вариант 2: Исправить вручную**
```bash
# Посмотрите ошибку:
ruff check src/train.py

# Если "Line too long", разбейте строку:
# ❌
result = very_long_function_name(parameter1, parameter2, parameter3, parameter4, parameter5)

# ✅
result = very_long_function_name(
    parameter1, parameter2, parameter3,
    parameter4, parameter5
)
```

**Вариант 3: Пропустить pre-commit (не рекомендуется!)**
```bash
git commit -m "Lesson 1" --no-verify
# Но потом CI всё равно упадёт!
```

---

## ЗАНЯТИЕ 6-9: Качество

### ❌ Проблема: "pytest не находит мои тесты"

**Симптомы:**
```bash
$ python -m pytest
collected 0 items
```

**Возможные причины:**

**Причина 1: Файлы не названы правильно**
```
❌ Неправильно:
tests/
├─ check_model.py   ← не начинается с test_
├─ model_check.py   ← не начинается с test_
└─ my_tests.py      ← не начинается с test_

✅ Правильно:
tests/
├─ test_model.py
├─ test_data.py
└─ test_features.py
```

**Причина 2: Функции не названы правильно**
```python
# ❌ НЕПРАВИЛЬНО:
def check_model():
    assert True

# ✅ ПРАВИЛЬНО:
def test_model():
    assert True
```

**Причина 3: Файлы не в папке tests/**
```
❌ Неправильно:
src/
├─ test_train.py   ← тесты не должны быть в src/

✅ Правильно:
tests/
├─ test_train.py
```

**Решение:**
```bash
# Проверьте структуру:
ls -la tests/
# Должны видеть: test_*.py файлы

# Запустите pytest с verbose:
python -m pytest -v

# Если всё равно не видит, проверьте import:
python -c "import sys; print(sys.path)"
# Должна быть текущая папка в пути
```

---

### ❌ Проблема: "Тест проходит локально но падает в CI"

**Симптомы:**
```bash
# Локально:
$ make test
✅ test_data.py PASSED

# На GitHub Actions:
❌ test_data.py FAILED
   FileNotFoundError: data/raw/churn.csv
```

**Причина:**
- Пути отличаются (относительные vs абсолютные)
- Данные не генерируются в CI
- Версии пакетов разные

**Решение:**

**Шаг 1: Используйте относительные пути**
```python
# ❌ НЕПРАВИЛЬНО:
df = pd.read_csv("/Users/me/project/data/raw.csv")

# ✅ ПРАВИЛЬНО:
from src.config import resolve
df = pd.read_csv(resolve("data/raw/churn.csv"))
```

**Шаг 2: Убедитесь что CI генерирует данные**
```yaml
# .github/workflows/tests.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: make data  ← добавьте это!
      - run: make test
```

**Шаг 3: Проверьте что requirements.txt актуален**
```bash
# Обновите requirements.txt:
pip freeze > requirements.txt

# Коммитьте его:
git add requirements.txt
git commit -m "Update dependencies"
```

---

### ❌ Проблема: "MLflow запущен но дашборд пустой"

**Симптомы:**
```bash
$ mlflow ui
# Открываю http://localhost:5000
# Пусто! Нет ни одного эксперимента
```

**Причина:**
- MLflow не логирует метрики
- Tracking URI не правильный

**Решение:**

**Шаг 1: Убедитесь что код логирует**
```python
# В src/train.py должно быть что-то типа:
import mlflow

mlflow.start_run()
mlflow.log_param("learning_rate", 0.01)
mlflow.log_metric("roc_auc", 0.85)
mlflow.end_run()
```

**Шаг 2: Проверьте что MLflow server запущен**
```bash
# Запустите MLflow:
mlflow ui

# Проверьте что он запустился на нужном адресе:
# http://localhost:5000/
```

**Шаг 3: Проверьте что tracking_uri правильный**
```python
# В коде должно быть:
mlflow.set_tracking_uri("http://localhost:5000")

# Или в params.yaml:
mlflow:
  tracking_uri: http://localhost:5000
```

**Шаг 4: Проверьте что experiment создан**
```python
mlflow.set_experiment("churn")  # назовите experiment
```

**Шаг 5: Перезапустите обучение**
```bash
make train

# Проверьте дашборд
# http://localhost:5000/ → должны видеть runs
```

---

### ❌ Проблема: "GitHub Actions workflow не запускается"

**Симптомы:**
```bash
$ git push
# Жду что CI запустится
# Но ничего не происходит
```

**Возможные причины:**

**Причина 1: Файл workflow не в правильной папке**
```
❌ Неправильно:
workflows/
└─ tests.yml

✅ Правильно:
.github/
└─ workflows/
   └─ tests.yml
```

**Причина 2: YAML синтаксис неправильный**
```yaml
# ❌ НЕПРАВИЛЬНО:
jobs:
test:  ← неправильный indent!
  runs-on: ubuntu-latest

# ✅ ПРАВИЛЬНО:
jobs:
  test:  ← 2 пробела!
    runs-on: ubuntu-latest
```

**Причина 3: Триггер не правильный**
```yaml
# ❌ Не запустится если push в main:
on:
  pull_request:  ← только PR!

# ✅ Запустится и на push и на PR:
on:
  push:
  pull_request:
```

**Решение:**

```bash
# Проверьте что файл на месте:
ls -la .github/workflows/

# Проверьте синтаксис YAML:
python -m yaml tests/.github/workflows/tests.yml  # или используйте online validator

# Пушьте и смотрите логи:
git push

# Логи появятся на GitHub → Actions → ваш workflow
```

---

## ЗАНЯТИЕ 10-13: Production

### ❌ Проблема: "Docker image весит 2ГБ вместо 500МБ"

**Симптомы:**
```bash
$ docker build -t my-model .
$ docker images
# my-model    2.0GB  ← ОГРОМНО!
```

**Причина:**
- Не используется multi-stage build
- Все промежуточные слои сохраняются

**Решение:**

**Правильный Dockerfile (multi-stage):**
```dockerfile
# Stage 1: build
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: runtime (маленький!)
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.service.app:app", "--host", "0.0.0.0"]
```

**Проверьте размер:**
```bash
docker build -t my-model .
docker images
# Должно быть < 500MB
```

---

### ❌ Проблема: "docker run падает с ModuleNotFoundError"

**Симптомы:**
```bash
$ docker run my-model
ModuleNotFoundError: No module named 'sklearn'
```

**Причина:**
- requirements.txt не скопирован в Docker
- Или pip install не запустился
- Или забыли добавить в Dockerfile

**Решение:**

**Проверьте Dockerfile:**
```dockerfile
# Должны быть эти строки:
COPY requirements.txt .
RUN pip install -r requirements.txt
```

**Если забыли, добавьте:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Добавьте это:
COPY requirements.txt .
RUN pip install -r requirements.txt

# И потом:
COPY . .
```

**Пересоберите и проверьте:**
```bash
docker build -t my-model .
docker run my-model python -c "import sklearn; print('OK')"
# Должно быть: OK
```

---

### ❌ Проблема: "docker-compose up запустился но контейнеры не видят друг друга"

**Симптомы:**
```bash
$ docker-compose up
# API контейнер запустился но не может подключиться к MLflow:
# ERROR: Cannot reach http://localhost:5000
```

**Причина:**
- Контейнеры используют неправильные hostname'ы
- localhost внутри контейнера это не то же что снаружи

**Решение:**

**Правильный docker-compose.yml:**
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      MLFLOW_TRACKING_URI: http://mlflow:5000  # ← не localhost!
    depends_on:
      - mlflow

  mlflow:
    image: python:3.11-slim
    command: pip install mlflow && mlflow server
    ports:
      - "5000:5000"
```

**Ключевой момент:**
- Внутри Docker сети используйте имя сервиса (mlflow) вместо localhost
- Снаружи используйте localhost или IP машины

---

### ❌ Проблема: "GitHub Actions не может залить образ в GHCR"

**Симптомы:**
```
ERROR: authentication failed
Could not push image ghcr.io/username/myapp:latest
```

**Причина:**
- GitHub token не установлен
- Или token не имеет нужных прав

**Решение:**

**Шаг 1: Создайте Personal Access Token**
```
GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
New token classic
- Выбрать: write:packages, read:packages
- Скопировать токен
```

**Шаг 2: Добавьте токен в GitHub Secrets**
```
Репозиторий Settings → Secrets and variables → Actions
New repository secret
- Name: GITHUB_TOKEN (или GH_TOKEN)
- Value: <ваш токен>
```

**Шаг 3: Используйте в workflow**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build and push
        run: |
          docker build -t ghcr.io/${{ github.repository }}:latest .
          docker push ghcr.io/${{ github.repository }}:latest
```

---

## ЗАНЯТИЕ 14-17: Эксплуатация

### ❌ Проблема: "Prometheus запущен но метрик нет"

**Симптомы:**
```bash
$ prometheus --version
# Запущен на http://localhost:9090
# Но когда запрашиваю метрики → пусто
```

**Причина:**
- Код не экспортирует метрики в формате Prometheus
- Prometheus не знает где взять метрики

**Решение:**

**Шаг 1: Добавьте экспорт метрик в FastAPI**
```python
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from fastapi.responses import Response

# Создаём метрики
request_count = Counter('api_requests_total', 'Total requests')
prediction_time = Histogram('api_prediction_seconds', 'Prediction time')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(REGISTRY), media_type="text/plain")

@app.post("/predict")
async def predict(request: PredictRequest):
    request_count.inc()  # увеличиваем counter
    
    with prediction_time.time():  # отмеряем время
        predictions = model.predict([...])
    
    return {"prediction": predictions}
```

**Шаг 2: Настройте prometheus.yml**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'  ← важно!
```

**Шаг 3: Перезапустите Prometheus**
```bash
prometheus --config.file=prometheus.yml

# Проверьте:
# http://localhost:9090/targets
# Должны видеть ваш API target как "UP"
```

---

### ❌ Проблема: "Grafana красивая но я не знаю как её настроить"

**Симптомы:**
```
Открыл http://localhost:3000
Красивый интерфейс но что дальше?
```

**Решение (пошагово):**

**Шаг 1: Логин**
```
Username: admin
Password: admin
(Измените пароль при первом логине)
```

**Шаг 2: Добавляем Data Source (Prometheus)**
```
Configuration → Data Sources → Add Data Source
- Type: Prometheus
- URL: http://localhost:9090
- Save & Test
```

**Шаг 3: Создаём Dashboard**
```
Dashboards → Create → New Dashboard
- Add Panel
- Выбираем Prometheus в Query
- Выбираем метрику: api_requests_total
- Выбираем visualization: Graph
- Save
```

**Простой пример Grafana dashboard:**
```json
{
  "dashboard": {
    "panels": [
      {
        "title": "Requests per second",
        "targets": [
          {"expr": "rate(api_requests_total[1m])"}
        ],
        "type": "graph"
      },
      {
        "title": "Prediction Time",
        "targets": [
          {"expr": "api_prediction_seconds_bucket"}
        ],
        "type": "graph"
      }
    ]
  }
}
```

---

## УНИВЕРСАЛЬНЫЕ ПРОБЛЕМЫ

### ❌ Проблема: "Я не знаю как дебугить когда что-то сломалось"

**Инструменты отладки:**

**1. Логи — первый друг**
```bash
# Посмотрите логи:
docker logs <container_id>

# Или в Python:
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Variable: {var}")
```

**2. Проверьте типы данных**
```python
# Когда ошибка не ясна:
print(f"Type: {type(var)}, Value: {var}")
print(f"Shape: {var.shape if hasattr(var, 'shape') else 'N/A'}")
```

**3. Используйте debugger в VS Code**
```python
# Добавьте точку останова:
breakpoint()  # или set_trace()

# Потом в терминале:
# Нажмите F5 в VS Code (Debug)
```

**4. Проверьте версии пакетов**
```bash
pip list | grep sklearn
python -c "import sklearn; print(sklearn.__version__)"
```

---

### ❌ Проблема: "Я потратил 2 часа на баг который был в requirements.txt"

**Решение (как избежать):**

**Зафиксируйте версии:**
```bash
# ❌ Неправильно:
pandas
numpy
sklearn

# ✅ Правильно:
pandas==1.5.3
numpy==1.24.1
scikit-learn==1.2.1
```

**Генерируйте правильно:**
```bash
# НИКОГДА просто pip install
pip install pandas numpy sklearn

# ВСЕГДА фиксируйте версии:
pip freeze > requirements.txt
```

**Проверяйте что все зависимости указаны:**
```bash
# Добавьте все что используете:
pip install pandas numpy scikit-learn mlflow fastapi pytest

# Потом:
pip freeze > requirements.txt

# Проверьте:
cat requirements.txt
```

---

### ❌ Проблема: "На GitHub Actions CI падает с ошибкой но я не вижу почему"

**Решение (как читать логи):**

```
GitHub → Actions → ваш workflow run → job → step
→ Посмотрите логи step'а где упало

Ищите красную ошибку ERROR или FAILED
Прочитайте контекст выше неё
```

**Типичные ошибки и как их читать:**

```
ERROR: pip install failed
  Could not find a version that satisfies: numpy==1.999.0
  → Версия неправильная в requirements.txt

ModuleNotFoundError: No module named 'sklearn'
  → sklearn не в requirements.txt

FileNotFoundError: data/raw/churn.csv
  → Нужно запустить make data перед тестами
```

---

### ❌ Проблема: "Я сломал что-то важное в main ветке"

**Решение (как откатить):**

```bash
# Посмотрите последние коммиты:
git log --oneline -10

# Откатитесь на один коммит назад:
git reset --hard HEAD~1

# Или на конкретный коммит:
git reset --hard abc1234

# Пушьте обратно:
git push --force origin main

# ⚠️ --force опасен! Используйте только если вы единственный в ветке
```

**Правильный способ (через новый коммит):**
```bash
# Просто откройте старый коммит, сделайте изменения и создайте новый:
git revert abc1234  # создаёт коммит который отменяет abc1234

git push
```

---

### ❌ Проблема: "Я не знаю зачем всё это нужно если я могу просто jupyter notebook"

**Ответ:**

Jupyter notebook работает для:
- ✅ Экспериментов (пробуем разные идеи)
- ✅ Анализа (смотрим на данные)

Но НЕ работает для:
- ❌ Production (модель должна работать 24/7)
- ❌ Команды (коллега не может запустить мой notebook)
- ❌ Тестирования (как тестировать notebook?)
- ❌ Развёртывания (как запустить notebook на сервере?)
- ❌ Мониторинга (если notebook упал, я узнаю когда клиент позвонит)

**Вывод:**
- Notebook = экспериментирование
- Production code = структурированный, тестируемый, мониторимый

Этот курс учит вас писать production code! 🚀

---

## 📋 ФИНАЛЬНЫЙ ЧЕК-ЛИСТ

### Перед сдачей каждого задания:

- [ ] Я активировал .venv: `source .venv/bin/activate`
- [ ] Я запустил `make check` и результат OK
- [ ] Я запустил `make train` и ROC-AUC адекватный (>0.75)
- [ ] Я запустил `make train` два раза и метрики идентичные
- [ ] Я запустил `make test` и все тесты passed
- [ ] Я запустил `git status` и вижу что коммитится (не data/ и models/)
- [ ] Я создал PR в правильной ветке (не main!)
- [ ] Pre-commit прошёл без ошибок
- [ ] Я запустил `python -m bot.checker --path . --lesson N`
- [ ] Я запушил работу в свой репозиторий (`git push`)

### Если что-то не работает:

1. Прочитайте это troubleshooting guide
2. Посмотрите логи (полный текст ошибки)
3. Напишите в Telegram группу (может кто-то сталкивался)
4. Напишите преподавателю: alsu124@mail.ru

---

**Удачи! И не бойтесь ошибок — это часть обучения! 🚀**

Telegram: https://t.me/+3N7q9X1YIWxkN2Iy
