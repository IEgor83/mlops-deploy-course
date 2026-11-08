# 💻 УСТАНОВКА GIT ПО ОПЕРАЦИОННЫМ СИСТЕМАМ

Выбери свою ОС и следуй инструкциям.

---

## 🍎 macOS

### Вариант 1: Через Homebrew (рекомендуется)

```bash
# Если нет Homebrew, установи сначала
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установи Git
brew install git

# Проверь
git --version
```

### Вариант 2: Через Xcode Command Line Tools

```bash
# Установка
xcode-select --install

# Проверка
git --version
```

### Вариант 3: Скачать инсталлер

Перейди на https://git-scm.com/download/mac и скачай .dmg файл

---

## 🐧 Linux (Ubuntu/Debian)

```bash
# Обнови пакеты
sudo apt-get update

# Установи Git
sudo apt-get install git

# Проверь
git --version
```

### Для других дистрибутивов

**Fedora/RHEL:**
```bash
sudo dnf install git
```

**Arch:**
```bash
sudo pacman -S git
```

---

## 🪟 Windows

### Вариант 1: Git for Windows (рекомендуется)

1. Перейди на https://git-scm.com/download/win
2. Скачай инсталлер (обычно `Git-2.x.x-64-bit.exe`)
3. Запусти инсталлер
4. Выбирай настройки по умолчанию (просто нажимай Next)
5. Закончи установку

Проверь:
```bash
# Открой PowerShell или Command Prompt
git --version
```

### Вариант 2: Через Windows Package Manager

```bash
# Если установлен winget
winget install Git.Git
```

### Вариант 3: Через Chocolatey

```bash
# Если установлен Chocolatey
choco install git
```

---

## ⚙️ ПЕРВАЯ НАСТРОЙКА (ВСЕ ОС)

Эти команды нужно выполнить один раз:

```bash
# Открой терминал/PowerShell
# И выполни:

git config --global user.name "Твое Имя Фамилия"
git config --global user.email "твоя.почта@example.com"

# Проверь что всё установлено правильно
git config --global user.name
git config --global user.email
git --version
```

Должно вывести:
```
Твое Имя Фамилия
твоя.почта@example.com
git version 2.x.x (or higher)
```

---

## 🔧 IDE/РЕДАКТОРЫ С ВСТРОЕННЫМ GIT

Если хочешь использовать GUI вместо команд:

### VS Code
1. Скачай: https://code.microsoft.com/
2. Установи
3. Git встроен в VS Code
4. Используй Source Control панель (Ctrl+Shift+G)

### GitHub Desktop
1. Скачай: https://desktop.github.com/
2. Установи
3. Удобное GUI для Git и GitHub

### Sublime Merge
1. Скачай: https://www.sublimemerge.com/
2. Платный, но удобный

### Git Kraken
1. Скачай: https://www.gitkraken.com/
2. Визуальный Git клиент

---

## ✅ ПРОВЕРКА УСТАНОВКИ

Когда установил Git, выполни:

```bash
git --version
```

Должно вывести версию, например:
```
git version 2.42.0
```

Если видишь это - **всё установлено правильно!** ✅

---

## 🆘 ПРОБЛЕМЫ ПРИ УСТАНОВКЕ

### "git: command not found"

**Причина:** Git не установлен или не в PATH

**Решение:**
- Переустанови Git (скачай с https://git-scm.com/)
- Перезагрузи компьютер после установки

### "permission denied" на macOS

**Причина:** Нет прав на установку

**Решение:**
```bash
sudo chown -R $(whoami) /usr/local
brew install git
```

### Git установлен но не работает в PowerShell

**Причина:** Path не обновлена

**Решение:**
- Перезагрузи PowerShell (закрой и открой заново)
- Или перезагрузи компьютер

---

## 🎓 ГОТОВО!

После установки переходи к [`STUDENT_GIT_GUIDE.md`](./STUDENT_GIT_GUIDE.md) или используй [`GIT_CHEATSHEET.md`](./GIT_CHEATSHEET.md)

**Удачи! 🚀**
