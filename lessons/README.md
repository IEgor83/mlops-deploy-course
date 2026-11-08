# Занятия

По папке на занятие. В каждой два файла:

* `plan.md` — **преподавателю**: тайминг пары, сценарий демо, типовые ошибки,
  что делать с теми, кто успел раньше. Студентам не выдаётся.
* `handout.md` — **студенту**: самодостаточная методичка. По ней можно
  пройти занятие самостоятельно, если пропустил пару.

| № | Занятие | Тема | Артефакт |
|---|---|---|---|
| 1 | [01-intro-project-setup](01-intro-project-setup/) | Введение в MLOps, структура проекта | `make train` работает |
| 2 | [02-git-workflow](02-git-workflow/) | Git для ML-команды, pre-commit | Смерженный PR с ревью |
| 3 | [03-config-and-determinism](03-config-and-determinism/) | Конфигурация и детерминизм | Два прогона = одни метрики |
| 4 | [04-dvc-data-versioning](04-dvc-data-versioning/) | Версионирование данных: DVC | `dvc push`/`pull` работают |
| 5 | [05-dvc-pipelines](05-dvc-pipelines/) | Пайплайны DVC | `dvc repro` воспроизводит всё |
| 6 | [06-mlflow-tracking](06-mlflow-tracking/) | MLflow Tracking | 5+ прогонов в UI |
| 7 | [07-mlflow-registry](07-mlflow-registry/) | MLflow Model Registry | Модель в Production |
| 8 | [08-testing-ml](08-testing-ml/) | Тестирование ML-систем | 8+ тестов, `make test` зелёный |
| 9 | [09-ci-github-actions](09-ci-github-actions/) | CI на GitHub Actions | Зелёный CI, защита `main` |
| 10 | [10-fastapi-service](10-fastapi-service/) | Инференс-сервис на FastAPI | Сервис отвечает на `curl` |
| 11 | [11-docker](11-docker/) | Контейнеризация | Образ < 500 МБ |
| 12 | [12-compose-stack](12-compose-stack/) | Локальный прод-стенд | `docker compose up` |
| 13 | [13-cd-and-releases](13-cd-and-releases/) | CD и релизы | Образ в GHCR, релиз `v1.0.0` |
| 14 | [14-service-monitoring](14-service-monitoring/) | Мониторинг сервиса | Дашборд + алерты |
| 15 | [15-data-drift](15-data-drift/) | Мониторинг данных и модели | Отчёт о дрейфе |
| 16 | [16-orchestration-retraining](16-orchestration-retraining/) | Оркестрация и автопереобучение | Flow переобучения (бонус) |
| 17 | [17-final-assembly](17-final-assembly/) | Сборка проекта, репетиция | Проект готов к зачёту |
| 18 | [18-exam](18-exam/) | Зачёт | Защита проекта |

## Развилки курса

* **Занятие 10** — контрольная точка: без работающего пайплайна DVC
  дальше проект не собрать. Отстающим преподаватель выдаёт эталонное состояние
  из приватного репозитория как точку старта.
* **Занятия 3, 7, 17** — сжимаемые: проводятся за 45–60 минут,
  остаток отдаётся на приём долгов, если пара потеряна из-за праздника.
* **Занятие 16** — необязательное: снимается первым, даёт бонусные баллы.
