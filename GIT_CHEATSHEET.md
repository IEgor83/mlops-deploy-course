# 🔖 GIT ШПАРГАЛКА - КРАТКАЯ ВЕРСИЯ

Самые нужные команды на одной странице.

---

## 🚀 БЫСТРЫЙ СТАРТ (5 КОМАНД)

```bash
# 1. Клонируй репо
git clone https://github.com/alsu124/mlops-deploy-course.git
cd mlops-deploy-course

# 2. Создай свою ветку
git checkout -b my-homework

# 3. Работай с файлами...
# (редактируешь, создаешь файлы)

# 4. Коммитьте свои изменения
git add .
git commit -m "ДЗ 1: Готово"

# 5. Загрузи на GitHub
git push origin my-homework
```

---

## 📋 САМЫЕ НУЖНЫЕ КОМАНДЫ

| Команда | Что делает |
|---------|-----------|
| `git clone URL` | Скачать репо |
| `git checkout -b NAME` | Создать и перейти на ветку |
| `git status` | Посмотреть статус |
| `git add .` | Добавить все файлы |
| `git commit -m "TEXT"` | Закоммитить с описанием |
| `git push` | Загрузить на GitHub |
| `git pull` | Скачать обновления |
| `git log --oneline` | История коммитов |

---

## 🔄 ДЛЯ КАЖДОГО ДЗ

```bash
# Шаг 1: Создать ветку
git checkout -b lesson-01

# Шаг 2: Работать с файлами
# (создаешь, редактируешь)

# Шаг 3: Добавить файлы
git add .

# Шаг 4: Коммитить
git commit -m "ДЗ 1: решение готово"

# Шаг 5: Пушить
git push origin lesson-01

# Шаг 6: Pull Request на GitHub
# -> Новый PR -> Create PR
```

---

## 🐛 ЕСЛИ ЧТО-ТО ПОШЛО НЕ ТАК

| Проблема | Решение |
|----------|---------|
| Забыл что-то в коммите | `git add FILE` + `git commit --amend` |
| Не туда добавил файл | `git restore --staged FILE` |
| Отменить последний коммит | `git reset --soft HEAD~1` |
| Посмотреть что изменилось | `git diff` |
| Вернуться на ветку main | `git checkout main` |

---

## 📝 ХОРОШИЙ КОММИТ

```bash
# ✅ ХОРОШО:
git commit -m "ДЗ 1: git basics

- Создал файл solution.md
- Описал основные команды
- Добавил примеры"

# ❌ ПЛОХО:
git commit -m "fix"
git commit -m "asdf"
git commit -m "changes"
```

---

## 🎯 СДАТЬ ДЗ

1. Создать ветку: `git checkout -b lesson-01`
2. Работать в ветке
3. Коммитить: `git commit -m "ДЗ 1: готово"`
4. Пушить: `git push origin lesson-01`
5. На GitHub нажать "New Pull Request"
6. Описать что сделал
7. Создать PR
8. Учитель проверит и даст оценку

---

## 💾 СОХРАНИТЬ ШПАРГАЛКУ

```bash
# Это один раз, и готово!
git config --global user.name "Твое Имя"
git config --global user.email "твоя@почта.com"
```

---

## 🔗 ПОЛНАЯ ИНСТРУКЦИЯ

Более подробная версия: [`STUDENT_GIT_GUIDE.md`](./STUDENT_GIT_GUIDE.md)

---

**Помни: `add → commit → push` 💪**
