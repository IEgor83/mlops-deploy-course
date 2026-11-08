# Занятие 9. CI на GitHub Actions

## Проблема

Вы написали тесты. Вопрос: что заставит вас запустить их перед мержем
в пятницу вечером?

И второй, более важный: ваши тесты проходят на вашей машине,
где лежат данные, сгенерированные месяц назад, стоят библиотеки,
которые вы поставили руками, и есть файлы, которые вы забыли закоммитить.
Это ничего не говорит о проекте.

CI запускает проверки на чистой машине, автоматически, на каждое изменение.

## Шаг 1. Первый workflow

Создайте `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Установить зависимости
        run: |
          python -m pip install -U pip
          pip install -r requirements.txt -r requirements-dev.txt

      - name: Линтер
        run: ruff check src tests

      - name: Тесты
        run: pytest --cov=src --cov-report=term-missing
```

Разберите ключевые места:

| Строка | Смысл |
|---|---|
| `on: pull_request` | запуск на каждый PR — главный сценарий |
| `runs-on: ubuntu-latest` | чистая виртуалка, ничего вашего на ней нет |
| `cache: pip` | кэш зависимостей, экономит ~1,5 минуты |
| Отдельные шаги для линтера и тестов | в интерфейсе видно, что именно упало |

Отправьте через PR:

```bash
git checkout -b ci/github-actions
git add .github && git commit -m "Добавить CI: линтер и тесты"
git push -u origin ci/github-actions
```

Откройте PR и смотрите вкладку Checks.

## Шаг 2. Первое падение — это нормально

Скорее всего, CI покраснеет. Частые причины:

* `ruff` нашёл то, что `pre-commit` у вас исправлял автоматически;
* тест читает файл, которого нет в репозитории (данные же в `.gitignore`);
* забыт `__init__.py` в каком-то пакете.

Читайте лог сверху вниз, находите первую красную строку. Чините локально,
пушьте в ту же ветку — CI перезапустится сам.

**Это самая ценная часть занятия.** То, что сейчас падает, — реальные
проблемы вашего проекта, которые были не видны, потому что у вас на машине
всё «как-то работало».

## Шаг 3. Пайплайн отдельным job

Добавьте второй job:

```yaml
  pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - run: pip install -r requirements.txt

      - name: Воспроизвести пайплайн
        run: |
          python -m src.data.generate --n 4000
          python -m src.data.prepare
          python -m src.train --no-mlflow
          python -m src.evaluate

      - name: Опубликовать метрики
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: metrics
          path: reports/
```

Три решения, которые нужно понимать:

**Почему отдельный job.** Он идёт параллельно с тестами, и по красному
чек-боксу сразу видно, что сломалось: код или пайплайн.

**Почему `--n 4000`.** В CI проверяется, что пайплайн жив, а не что модель
хороша. Обучение на 20 000 строк добавит минуты к каждому PR без пользы.

**Почему `--no-mlflow`.** В раннере нет вашего трекинг-сервера.
Флаг вы сделали на занятии 6 ровно для этого случая.

Обратите внимание: `python -m src.evaluate` завершится с кодом 1,
если ROC-AUC ниже `min_roc_auc` из `params.yaml`. То есть **CI падает
по деградации модели**, а не только по ошибке в коде. Это и есть
quality gate, который вы сделали на занятии 3.

## Шаг 4. Проверить, что gate работает

Временно поставьте в `params.yaml` заведомо недостижимый порог:

```yaml
evaluate:
  min_roc_auc: 0.99
```

Запушьте в ветку PR. CI должен покраснеть на шаге воспроизведения пайплайна.
Верните `0.75` обратно.

## Шаг 5. Защита ветки

Settings → Branches → Edit rule для `main`:

- [x] Require a pull request before merging
- [x] Require status checks to pass before merging
  - выберите `quality` и `pipeline`
- [x] Require branches to be up to date before merging

Теперь красный CI физически блокирует кнопку Merge. Это не про недоверие
к себе — это про то, чтобы `main` всегда был в рабочем состоянии.

## Шаг 6. Бейдж

В `README.md`, первой строкой после заголовка:

```markdown
![CI](https://github.com/ВАШ_ЛОГИН/ВАШ_РЕПО/actions/workflows/ci.yml/badge.svg)
```

## Шаг 7. Как в CI попадают настоящие данные

В учебном проекте данные генерируются. В реальном — лежат в облаке,
и CI нужно дать к ним доступ.

Механика: Settings → Secrets and variables → Actions → New repository secret.
Затем в workflow:

```yaml
      - name: Получить данные
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: dvc pull
```

Значения секретов GitHub маскирует в логах — но только те, что пришли
из Secrets. Ключ, вписанный в код, будет виден в логе целиком.

Реализовывать это сейчас не нужно (ваш MinIO живёт на localhost
и раннеру недоступен), но понимать механику — обязательно: вопрос будет на зачёте.

## Шаг 8. Метрики прямо в Pull Request

Сейчас, чтобы узнать метрики после изменения, нужно открыть вкладку
Actions, найти прогон, скачать артефакт и распаковать. Ревьюер этого
не сделает. Значит, решение о мерже принимается вслепую.

Пусть CI сам пишет метрики комментарием в PR.

Добавьте в job `pipeline`, после шага воспроизведения:

```yaml
      - name: Опубликовать метрики в PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const m = JSON.parse(fs.readFileSync('reports/eval_metrics.json')).metrics;
            const body = [
              '## Метрики этого PR',
              '',
              '| Метрика | Значение |',
              '|---|---|',
              `| ROC-AUC | ${m.roc_auc.toFixed(4)} |`,
              `| PR-AUC | ${m.pr_auc.toFixed(4)} |`,
              `| F1 | ${m.f1.toFixed(4)} |`,
            ].join('\n');
            await github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body,
            });
```

Понадобится разрешение на запись в PR:

```yaml
permissions:
  contents: read
  pull-requests: write
```

**Что здесь важно понять.** Это не украшение. Ревьюер видит цифры,
не покидая страницу PR, и может спросить «почему ROC-AUC просел
на 0.02» — до мержа, а не через месяц.

**Если успели раньше:** добавьте сравнение с метриками из `main`,
чтобы в комментарии была дельта, а не абсолютное значение.
Абсолютное число мало о чём говорит, изменение — говорит обо всём.

## Что сдать

- [ ] `.github/workflows/ci.yml` с двумя job
- [ ] CI зелёный на PR
- [ ] Показано, что CI краснеет при завышенном `min_roc_auc`
- [ ] Защита `main` с обязательными проверками включена
- [ ] Бейдж в README
- [ ] CI публикует метрики комментарием в PR
- [ ] Показан PR с таким комментарием

## Домашнее задание (1,5–2 ч)

1. Добавьте в `quality` шаг проверки формата: `ruff format --check src tests`.
2. Настройте кэширование так, чтобы повторный прогон был быстрее первого.
   Замерьте оба и запишите цифры в `README.md`.
3. Сделайте PR, который намеренно ломает поведенческий тест
   (например, инвертируйте знак в одном месте). Убедитесь, что CI покраснел
   и мерж заблокирован. Приложите скриншот в `reports/`. PR закройте без мержа.
4. Ответьте письменно в `README.md`: почему проверка `pytest` в CI полезнее,
   чем та же проверка в `pre-commit`, хотя команда одна и та же?

## Полезное

* Вкладка **Actions** в репозитории — все прогоны и логи
* `if: always()` — шаг выполнится даже после падения предыдущего
  (нужно, чтобы забрать артефакты с упавшего прогона)
* `runs-on: ubuntu-latest` бесплатен для публичных репозиториев
* Правило: если проверку можно автоматизировать — её нельзя оставлять человеку
