# ✅ ЧЕК-ЛИСТ ДЛЯ СТУДЕНТА: Установка и начало работы

**Что установить перед первым занятием**

Telegram группа: https://t.me/+3N7q9X1YIWxkN2Iy

---

## 📋 ОСНОВНОЕ (обязательно!)

### ШАГ 1: Установить Python 3.11+

**На macOS:**
```bash
# Вариант 1: через Homebrew (если установлен)
brew install python@3.11

# Вариант 2: скачать с python.org
# https://www.python.org/downloads/
# → Download Python 3.11 (или новее)
# → Запустить installer

# Проверка:
python3 --version
# Должно быть: Python 3.11.X или выше
```

**На Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3.11 python3-pip

# Проверка:
python3 --version
```

**На Windows:**
```
1. Перейти на https://www.python.org/downloads/
2. Скачать Python 3.11 (или новее)
3. Запустить installer
4. ⚠️ ВАЖНО: поставить галочку "Add Python to PATH"
5. Нажать "Install Now"

# Проверка в PowerShell:
python --version
```

---

### ШАГ 2: Установить Git

**На macOS:**
```bash
# Вариант 1: через Homebrew
brew install git

# Вариант 2: скачать с git-scm.com
# https://git-scm.com/download/mac
```

**На Linux:**
```bash
sudo apt-get install git
```

**На Windows:**
```
1. Перейти на https://git-scm.com/download/win
2. Скачать и запустить installer
3. Везде нажимать "Next" (дефолтные параметры ОК)
```

**Проверка:**
```bash
git --version
# Должно быть: git version 2.X.X
```

---

### ШАГ 3: Установить VS Code (опционально, но рекомендуется)

```
https://code.visualstudio.com/
→ Download для вашей OS
→ Установить

Потом в VS Code:
Extensions → Python (Microsoft)
→ Install
```

---

## 📁 КЛОНИРОВАНИЕ РЕПОЗИТОРИЯ

### ВАРИАНТ A: Если репо на GitHub (чаще всего)

**Шаг 1: Скопируйте ссылку репозитория**

Преподаватель даст вам ссылку типа:
```
https://github.com/username/mlops-template.git
```

**Шаг 2: Клонируйте**

```bash
# Перейдите в папку где хотите проект
cd ~/Documents  # или другая папка

# Клонируйте репо
git clone https://github.com/username/mlops-template.git

# Перейдите в папку проекта
cd mlops-template
```

**Шаг 3: Проверьте что клонировалось**

```bash
ls -la
# Должны видеть: src/, tests/, data/, models/, params.yaml, Makefile, README.md
```

---

### ВАРИАНТ B: Если вам дали ZIP файл

**Шаг 1: Распакуйте**
```bash
unzip mlops-template.zip
cd mlops-template
```

**Шаг 2: Инициализируйте git** (чтобы потом отправлять PR)
```bash
git init
git add .
git commit -m "Initial commit"
```

---

## 🐍 СОЗДАНИЕ И АКТИВАЦИЯ VIRTUAL ENVIRONMENT

**Шаг 1: Создайте venv**

```bash
# Убедитесь что вы в папке проекта:
pwd
# Должно вывести: /Users/you/Documents/mlops-template

# Создайте venv
python3 -m venv .venv
```

**Шаг 2: Активируйте venv**

**На macOS/Linux:**
```bash
source .venv/bin/activate

# Проверка: в начале строки должно быть (.venv)
# (.venv) $ ← так выглядит активированное окружение
```

**На Windows (PowerShell):**
```powershell
.venv\Scripts\Activate

# Проверка: в начале строки должно быть (.venv)
# PS (.venv) > ← так выглядит активированное окружение
```

**На Windows (cmd.exe):**
```cmd
.venv\Scripts\activate.bat
```

---

## 📦 УСТАНОВКА ЗАВИСИМОСТЕЙ

**Шаг 1: Убедитесь что venv активирован** (видите (.venv) в начале строки?)

**Шаг 2: Установите requirements**

```bash
# Если есть Makefile:
make install

# Если нет make (на Windows обычно):
pip install -r requirements.txt
```

**Шаг 3: Проверьте что всё установилось**

```bash
make check

# Должно быть:
# environment: OK ✅
```

---

## 🎯 ПЕРВЫЙ ЗАПУСК

**Шаг 1: Генерируйте данные**

```bash
make data

# Если работает:
# ✅ data/raw/churn.csv создан
# ✅ data/processed/train.csv создан
```

**Шаг 2: Запустите обучение**

```bash
make train

# Если работает:
# ✅ Видите ROC-AUC метрики
# ✅ models/model.joblib создан
# ✅ reports/train_metrics.json создан
```

**Шаг 3: Запустите тесты** (если есть)

```bash
make test

# Если работает:
# ✅ Все тесты PASSED
```

---

## 🔍 КАК ПРОВЕРИТЬ ЧТО ВСЁ РАБОТАЕТ

**Все ОК если:**
- ✅ `make check` выводит "environment: OK"
- ✅ `make data` создал файлы в data/processed/
- ✅ `make train` вывел метрики (ROC-AUC > 0.5)
- ✅ `make test` показал что тесты прошли
- ✅ VS Code может открыть проект

**Что-то не так если:**
- ❌ "command not found: make" → нужно установить make
- ❌ "ModuleNotFoundError" → venv не активирован
- ❌ "FileNotFoundError" → данные не сгенерированы (запустите `make data`)
- ❌ "git: command not found" → нужно установить git

---

## 📞 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

**Шаг 1: Проверьте что установилось**

```bash
# Python:
python3 --version

# Git:
git --version

# Make (macOS/Linux):
make --version
```

**Шаг 2: Проверьте что venv активирован**

```bash
# Видите (.venv) в начале строки? Если нет:
source .venv/bin/activate  # macOS/Linux
# или
.venv\Scripts\Activate  # Windows
```

**Шаг 3: Переустановите зависимости**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Шаг 4: Напишите в Telegram**

Если ничего не помогло:
https://t.me/+3N7q9X1YIWxkN2Iy

Напишите:
- Вашу OS (macOS / Linux / Windows)
- Полный текст ошибки
- Команду которую вы запустили

---

## 🆘 ТИПИЧНЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ

### Проблема: "python3 не найден"

**На Windows:**
```
❌ python3 --version
python3 : The term 'python3' is not recognized

Решение: используйте python без 3
✅ python --version
```

### Проблема: "venv не активирован"

```bash
# Если в начале строки НЕ видите (.venv):

# macOS/Linux:
source .venv/bin/activate

# Windows PowerShell:
.venv\Scripts\Activate

# Теперь должно быть: (.venv) $
```

### Проблема: "make: command not found"

**На macOS:**
```bash
brew install make
```

**На Linux:**
```bash
sudo apt-get install build-essential
```

**На Windows:**
```powershell
choco install make
# или просто используйте:
pip install -r requirements.txt  # вместо make install
python -m src.data.prepare      # вместо make data
python -m pytest                 # вместо make test
```

### Проблема: "pip install не работает"

```bash
# Убедитесь что venv активирован (видите (.venv)?)
# Если да:
pip install --upgrade pip
pip install -r requirements.txt

# Если всё равно не работает:
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 📋 ФИНАЛЬНЫЙ ЧЕК-ЛИСТ ПЕРЕД ПЕРВЫМ ЗАНЯТИЕМ

Отметьте что готово:

### Установлено:
- [ ] Python 3.11+ установлен (`python3 --version`)
- [ ] Git установлен (`git --version`)
- [ ] VS Code установлен (опционально)

### Репо готово:
- [ ] Репо клонировано или распакован ZIP
- [ ] Перешли в папку проекта (`cd mlops-template`)
- [ ] Создан venv (`python3 -m venv .venv`)
- [ ] venv активирован (видите (.venv) в начале строки)

### Зависимости:
- [ ] Установлены requirements (`make install` или `pip install -r requirements.txt`)
- [ ] Проверка прошла (`make check` выводит "environment: OK")

### Первый запуск:
- [ ] Данные сгенерированы (`make data` работает)
- [ ] Обучение работает (`make train` показывает метрики)
- [ ] Тесты проходят (`make test` показывает PASSED)

### Готовность:
- [ ] Присоединились к Telegram группе: https://t.me/+3N7q9X1YIWxkN2Iy
- [ ] Прочитали START_HERE.md
- [ ] Готовы к первому занятию!

---

## 🎯 ПРЯМО ПЕРЕД ПЕРВЫМ ЗАНЯТИЕМ

**За день до занятия:**

```bash
# 1. Активируйте venv
source .venv/bin/activate

# 2. Обновите код если нужно
git pull

# 3. Перегенерируйте данные
make data

# 4. Запустите обучение один раз
make train

# 5. Проверьте что всё работает
make check
```

Если всё ОК → вы готовы! 🚀

---

## 💬 ВОПРОСЫ?

**Telegram группа:** https://t.me/+3N7q9X1YIWxkN2Iy  
**Email:** alsu124@mail.ru

Напишите если:
- Что-то не установилось
- Что-то не клонировалось
- Что-то не запустилось
- Общие вопросы про курс

---

**Успехов! Видимся на первом занятии! 🎓**
