# Настройка окружения

Пройдите этот документ **до первого занятия**. На паре времени на установку не будет.

## Что должно быть установлено

| Инструмент | Версия | Проверка |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Git | 2.30+ | `git --version` |
| Docker Desktop / Docker Engine | 24+ | `docker run hello-world` |
| Аккаунт GitHub | — | вход выполнен |
| Редактор | VS Code (рекомендуется) | расширения Python, Docker |

Docker понадобится с занятия 11, но поставьте заранее: именно он ломается чаще всего.

## Установка по платформам

### Windows

Питон — **только** с python.org (не из Microsoft Store: он ломает пути к venv).
При установке отметьте «Add python.exe to PATH».

```powershell
winget install --id Git.Git -e
winget install --id Docker.DockerDesktop -e
```

Docker Desktop требует включённого WSL 2. Если `docker run hello-world` падает —
включите виртуализацию в BIOS и выполните `wsl --install` от администратора.

Все команды курса выполняйте в **PowerShell**, а не в cmd.

### macOS

```bash
brew install python@3.11 git
brew install --cask docker   # затем запустите Docker.app один раз вручную
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv git make
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER   # перелогиньтесь после этого
```

## Проверка окружения

Клонируйте учебный репозиторий и запустите скелет:

```bash
git clone <ссылка-на-репозиторий-курса>
cd MLOPS/template
python -m venv .venv
```

Активация виртуального окружения:

```bash
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\Activate.ps1       # Windows PowerShell
```

Дальше:

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m src.smoke_check
```

Скрипт должен напечатать `environment: OK` и версии ключевых библиотек.
Если что-то падает — принесите **текст ошибки целиком** на первое занятие.

## Настройка Git

```bash
git config --global user.name "Фамилия Имя"
git config --global user.email "ваш@email"
git config --global init.defaultBranch main
git config --global core.autocrlf input    # Windows: true
```

Последняя строка важна: без неё Windows подставит CRLF, и скрипты внутри
Docker-образа не запустятся с ошибкой `bad interpreter`.

### Доступ к GitHub по SSH

```bash
ssh-keygen -t ed25519 -C "ваш@email"
cat ~/.ssh/id_ed25519.pub
```

Скопируйте вывод в GitHub → Settings → SSH and GPG keys → New SSH key.
Проверка: `ssh -T git@github.com` должен поздороваться по имени.

## Про `make`

В методичках команды даны через `make` (`make train`, `make test`).
На Windows `make` не установлен — есть два пути:

1. Поставить: `winget install ezwinports.make`
2. Или открывать `Makefile` и выполнять команду из нужной цели вручную —
   там всегда одна-две строки.

## Частые проблемы

| Симптом | Причина | Решение |
|---|---|---|
| `pip` ставит пакеты «мимо» проекта | venv не активирован | активируйте, проверьте `which python` / `where python` |
| `ModuleNotFoundError: src` | запуск из другой папки | запускайте из корня проекта, через `python -m src.train` |
| Docker: `permission denied` | пользователь не в группе docker (Linux) | `sudo usermod -aG docker $USER`, перелогиниться |
| Docker Desktop не стартует (Windows) | выключен WSL 2 / виртуализация | `wsl --install`, включить VT-x в BIOS |
| `dvc push` виснет | нет доступа к remote | занятие 4, раздел про локальный remote |
| Долгая установка `mlflow` | тянет много зависимостей | это нормально, 3–5 минут в первый раз |
