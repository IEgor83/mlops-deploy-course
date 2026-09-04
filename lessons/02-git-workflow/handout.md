# Занятие 2. Git для ML-команды

## Зачем это занятие

В ML-проекте Git ломается не так, как в обычной разработке: сюда норовят
попасть датасеты на сотни мегабайт, модели, токены к облаку и ноутбуки
с выводом на 20 000 строк. Сегодня ставим защиту от этого — автоматическую,
а не «я буду внимательным».

## Шаг 1. Что уже не так в вашем репозитории

```bash
git count-objects -vH
git status --short
```

Если в `git status` видны `__pycache__`, `.venv`, `data/`, `models/` —
они не игнорируются. Проверьте `.gitignore` (в шаблоне он уже настроен).

Если файлы **уже закоммичены**, `.gitignore` их не уберёт — нужно явно:

```bash
git rm -r --cached data models __pycache__
git commit -m "Убрать данные и модели из индекса"
```

Важно понимать: из истории они при этом не исчезнут. Репозиторий останется
тяжёлым. Реальная чистка истории (`git filter-repo`) — операция болезненная,
поэтому дешевле не допускать.

## Шаг 2. Правило о секретах

```bash
git log -p --all -S "TOKEN" | head -40
```

Если что-то нашлось — этот токен нужно **отозвать**, а не удалить.
Файл, попавший в историю Git, остаётся в ней у всех, кто уже склонировал
репозиторий.

Правило проекта: секреты живут в `.env` (он в `.gitignore`), а в репозиторий
кладётся `.env.example` с именами переменных без значений.

Создайте его:

```bash
cat > .env.example <<'EOT'
MLFLOW_TRACKING_URI=http://localhost:5000
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
EOT
git add .env.example
```

## Шаг 3. pre-commit

Хуки запускаются перед каждым коммитом и не дают закоммитить мусор.
Создайте `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=1000]
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Установка и первый прогон:

```bash
pre-commit install
pre-commit run --all-files
```

Первый прогон почти наверняка что-то исправит и завершится с ошибкой.
**Это нормально:** хук не «упал», он внёс правки и остановил коммит,
чтобы вы их посмотрели. Добавьте изменения и коммитьте снова.

Проверьте, что защита работает:

```bash
make data && git add -f data/raw/churn.csv && git commit -m "проба"
```

`check-added-large-files` должен заблокировать коммит. Отмените: `git reset`.

## Шаг 4. Ветки и Pull Request

Работа в `main` напрямую с этого момента запрещена.

```bash
git checkout -b feature/model-selection
# ... правки ...
git add -u
git commit -m "Добавить выбор модели через params.yaml"
git push -u origin feature/model-selection
```

Дальше на GitHub: Compare & pull request.

**Как писать описание PR.** Не «изменения», а ответ на три вопроса:

```markdown
## Что
Добавлен выбор алгоритма через params.yaml: logreg, random_forest, gradient_boosting.

## Зачем
Сравнение моделей требовало правки кода — это ломало воспроизводимость:
непонятно, какой версией кода получена метрика в отчёте.

## Как проверить
Поменять train.model в params.yaml, запустить make train,
метрики меняются без правок кода.
```

**Как писать коммиты.** Одно изменение — один коммит. Сообщение отвечает
на «зачем», а не «что»: `git diff` и так покажет что.

Плохо: `фикс`, `работает`, `правки после ревью`
Хорошо: `Заполнить пропуски total_charges вместо dropna`

## Шаг 5. Ревью в паре

Добавьте напарника в коллабораторы: Settings → Collaborators.
Он ревьюит ваш PR, вы — его. Требование: **минимум один содержательный
комментарий** с привязкой к строке и предложением, что сделать.

Примеры содержательных замечаний:
* «Здесь `0.2` — вынеси в `params.yaml`, иначе значение продублируется в evaluate»
* «`except: pass` проглотит любую ошибку, включая опечатку в имени колонки»
* «Список признаков задан второй раз, он уже есть в `feature_columns()`»

После аппрува — Squash and merge, ветку удалить.

## Шаг 6. Защита main

Settings → Branches → Add branch protection rule для `main`:

- [x] Require a pull request before merging
- [x] Require approvals: 1

На занятии 9 сюда добавится обязательная проверка CI.

## Что сдать

- [ ] `.pre-commit-config.yaml`, `pre-commit run --all-files` без ошибок
- [ ] `.env.example` в репозитории, `.env` — нет
- [ ] Один смерженный PR с ревью напарника
- [ ] Защита `main` включена

## Домашнее задание (1,5–2 ч)

1. Оформите вторым PR домашнее задание занятия 1 (выбор модели + `EXPERIMENTS.md`),
   если ещё не сделали. Полный цикл: ветка → PR с описанием → ревью → мерж.
2. Приведите историю в порядок: заполните `README.md` своего репозитория —
   задача, как запустить, что уже сделано.
3. Проверьте, что чистый клон работает:
   ```bash
   git clone <ваш-репо> /tmp/check && cd /tmp/check
   python -m venv .venv && source .venv/bin/activate
   make install && make data && make prepare && make train
   ```
   Если что-то упало — вы что-то не закоммитили. Это главная проверка занятия.

## Полезное

| Команда | Зачем |
|---|---|
| `git switch -c имя` | создать ветку (современный аналог `checkout -b`) |
| `git log --oneline --graph --all` | увидеть картину веток |
| `git diff --staged` | что именно уйдёт в коммит |
| `git restore --staged файл` | убрать из индекса, не теряя правок |
| `pre-commit run --all-files` | прогнать хуки вручную |
| `git count-objects -vH` | размер репозитория |
