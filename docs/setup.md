# 💻 Установка окружения Python

Это руководство для студентов курса по MLOps. Выбери свою операционную систему.

---

## 🍎 macOS

### Проверь что у тебя установлен Python 3.11+

```bash
python3 --version
```

Должно вывести `Python 3.11.0` или выше.

Если нет - установи через Homebrew:
```bash
brew install python@3.11
```

### Создай виртуальное окружение

```bash
# Перейди в папку проекта
cd ~/Desktop/mlops-homework

# Создай venv
python3 -m venv .venv

# Активируй
source .venv/bin/activate

# Установи зависимости
pip install -r requirements.txt
```

Когда виртуальное окружение активно, слева в терминале должно появиться `(.venv)`.

---

## 🐧 Linux (Ubuntu/Debian)

### Установи Python 3.11+

```bash
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3-pip
```

### Создай виртуальное окружение

```bash
cd ~/Desktop/mlops-homework
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Для других дистрибутивов

**Fedora/RHEL:**
```bash
sudo dnf install python3.11 python3.11-venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Arch:**
```bash
sudo pacman -S python python-virtualenv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🪟 Windows

### Установи Python 3.11+

1. Скачай с https://www.python.org/downloads/ версию 3.11 или выше
2. При установке **обязательно** отметь галочку "Add Python to PATH"
3. Нажми "Install Now"

### Создай виртуальное окружение

Открой PowerShell или Command Prompt:

```bash
# Перейди в папку проекта
cd C:\Users\ВашИмя\Desktop\mlops-homework

# Создай venv
python -m venv .venv

# Активируй (PowerShell)
.venv\Scripts\Activate.ps1

# Или активируй (Command Prompt)
.venv\Scripts\activate.bat

# Установи зависимости
pip install -r requirements.txt
```

**Если не работает Activate.ps1:**
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Потом попробуй снова активировать.

---

## ✅ Проверка установки

После активации вenv должно работать:

```bash
python --version    # Python 3.11+
pip --version       # pip 23.0+
which python        # Должно быть в .venv
```

Проверь что видишь путь с `.venv`:
```
/Users/admin/Desktop/mlops-homework/.venv/bin/python
```

Или на Windows:
```
C:\Users\ВашИмя\Desktop\mlops-homework\.venv\Scripts\python.exe
```

---

## 📦 Установка зависимостей

Когда venv активировано:

```bash
pip install -r requirements.txt
```

Основные пакеты:
- `pandas` — работа с данными
- `scikit-learn` — машинное обучение
- `dvc` — версионирование данных
- `pytest` — тестирование
- `pre-commit` — проверки перед коммитом

---

## 🔄 Каждый раз когда открываешь терминал

Нужно активировать виртуальное окружение:

**macOS / Linux:**
```bash
source .venv/bin/activate
```

**Windows (PowerShell):**
```bash
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```bash
.venv\Scripts\activate.bat
```

Когда активировано, слева в терминале должно быть `(.venv)`.

---

## 🆘 Проблемы

### "python: command not found"

**Решение:**
- На macOS/Linux используй `python3` вместо `python`
- На Windows используй `python` (если установлен через python.org)

### "venv: command not found"

**Решение:**
```bash
# macOS / Linux
python3 -m venv .venv

# Windows
python -m venv .venv
```

### "pip install" падает с ошибкой

**Решение:**
```bash
# Обнови pip
pip install --upgrade pip

# Потом пробуй снова
pip install -r requirements.txt
```

---

## 🎯 Готово!

Теперь переходи к [HOW_TO_SUBMIT_LABS.md](../HOW_TO_SUBMIT_LABS.md) и начинай первую лабу!
