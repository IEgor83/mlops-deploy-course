# 📚 GIT GUIDE ДЛЯ СТУДЕНТОВ MLOPS КУРСА

Полная инструкция как работать с Git и GitHub для курса.

---

## 🎯 ЧТО НУЖНО СДЕЛАТЬ

1. Создать свой репо на GitHub
2. Клонировать репо курса
3. Выполнять домашние задания
4. Коммитить и пушить код
5. Создавать Pull Requests для сдачи

---

## ⚙️ УСТАНОВКА

### 1. Установи Git

**macOS:**
```bash
brew install git
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install git
```

**Windows:**
Скачай с https://git-scm.com/download/win

### 2. Проверь установку
```bash
git --version
```

Должно вывести версию, например: `git version 2.40.0`

### 3. Настрой Git (один раз)
```bash
git config --global user.name "Твое Имя"
git config --global user.email "твоя@почта.com"
```

Проверь:
```bash
git config --global user.name
git config --global user.email
```

---

## 🚀 БЫСТРЫЙ СТАРТ

### Шаг 1️⃣: Создай свой репо

1. Перейди на https://github.com/new
2. Имя репо: `mlops-ТВОЯ_ФАМИЛИЯ`
   - Пример: `mlops-ivanov`, `mlops-petrov`
3. Описание: "MLOps course assignments"
4. Private или Public - на выбор
5. Нажми **"Create repository"**

### Шаг 2️⃣: Клонируй репо курса

```bash
# Клонируем репо курса
git clone https://github.com/alsu124/mlops-deploy-course.git

# Переходим в папку
cd mlops-deploy-course
```

### Шаг 3️⃣: Создай свою ветку

```bash
# Создаем новую ветку для своих работ
git checkout -b my-work

# Проверяем что мы на новой ветке
git branch
# * my-work
#   main
```

### Шаг 4️⃣: Выполняй задания

Работай в папке `lessons/`:
```bash
# Пример: создаешь файл для ДЗ 1
cd lessons/01-git-basics
touch my-solution.md

# Пишешь решение в файл
echo "# Решение ДЗ 1" > my-solution.md
```

### Шаг 5️⃣: Добавь файлы в Git

```bash
# Посмотреть что изменилось
git status

# Добавить все файлы
git add .

# Или добавить конкретный файл
git add lessons/01-git-basics/my-solution.md
```

### Шаг 6️⃣: Закоммитьте изменения

```bash
# Создаешь коммит с описанием
git commit -m "Решение ДЗ 1: git basics"

# Или подробнее
git commit -m "ДЗ 1: git basics

- Создал файл solution.md
- Описал основные команды git
- Добавил примеры"
```

### Шаг 7️⃣: Загрузи на свой репо

```bash
# Сначала добавляем свой репо как remote
git remote add origin https://github.com/ТВОЙ_НИК/mlops-ФАМИЛИЯ.git

# Заменяем на нужную ветку
git push -u origin my-work

# В следующий раз просто
git push
```

### Шаг 8️⃣: Создай Pull Request

1. Перейди на https://github.com/alsu124/mlops-deploy-course
2. Нажми **"New pull request"**
3. Выбери:
   - **base:** `main` (куда сливаем)
   - **compare:** твоя ветка
4. Напиши описание ДЗ
5. Нажми **"Create pull request"**
6. Учитель проверит и даст оценку!

---

## 📖 ОСНОВНЫЕ КОМАНДЫ GIT

### Просмотр информации

```bash
# Статус репо
git status

# История коммитов
git log

# Подробнее
git log --oneline --graph --all

# Посмотреть изменения в файлах
git diff

# Посмотреть конкретный коммит
git show COMMIT_ID
```

### Работа с ветками

```bash
# Посмотреть все ветки
git branch -a

# Создать новую ветку
git branch homework-01

# Переключиться на ветку
git checkout homework-01

# Или создать и переключиться сразу
git checkout -b homework-01

# Удалить ветку
git branch -d homework-01

# Переименовать ветку
git branch -m homework-01 lesson-01
```

### Работа с remote (GitHub)

```bash
# Посмотреть все remote
git remote -v

# Добавить remote
git remote add origin https://github.com/username/repo.git

# Удалить remote
git remote remove origin

# Загрузить изменения на GitHub
git push origin my-branch

# Загрузить и сделать upstream
git push -u origin my-branch

# Получить изменения с GitHub
git pull

# Получить без merge
git fetch
```

### Отмена изменений

```bash
# Отменить изменения в файле (до add)
git restore FILE.txt

# Или старый способ
git checkout -- FILE.txt

# Убрать файл из staging area
git restore --staged FILE.txt

# Или
git reset FILE.txt

# Отменить последний коммит (сохранит файлы)
git reset --soft HEAD~1

# Отменить коммит и удалить изменения
git reset --hard HEAD~1
```

---

## 🎓 ПРИМЕРЫ

### Пример 1: Выполнить ДЗ 1

```bash
# Клонируем репо
git clone https://github.com/alsu124/mlops-deploy-course.git
cd mlops-deploy-course

# Создаем ветку
git checkout -b lesson-01-solution

# Переходим в папку ДЗ
cd lessons/01-git-basics

# Создаем решение
echo "# Мое решение" > solution.md

# Добавляем файл
git add solution.md

# Коммитим
git commit -m "ДЗ 1: Мое решение по Git"

# Добавляем remote (первый раз)
git remote add origin https://github.com/ТВОЙ_НИК/mlops-ФАМИЛИЯ.git

# Пушим
git push -u origin lesson-01-solution

# Создаем PR на GitHub
# -> New pull request -> Create pull request
```

### Пример 2: Обновить репо из upstream

```bash
# Добавляем upstream (если еще не добавили)
git remote add upstream https://github.com/alsu124/mlops-deploy-course.git

# Получаем обновления из upstream
git fetch upstream

# Переходим на main
git checkout main

# Обновляем свой main
git pull upstream main

# Пушим на свой GitHub
git push origin main
```

### Пример 3: Исправить коммит

```bash
# Если забыл что-то добавить в последний коммит
git add forgotten-file.txt
git commit --amend

# Если хочешь изменить сообщение
git commit --amend -m "Новое сообщение"
```

---

## 📋 WORKFLOW ДЛЯ КУРСА

Рекомендуемый процесс для каждого ДЗ:

```bash
# 1. Создаешь ветку с названием задания
git checkout -b lesson-01

# 2. Выполняешь ДЗ
# (редактируешь файлы)

# 3. Добавляешь все файлы
git add .

# 4. Коммитишь (может быть несколько коммитов)
git commit -m "ДЗ 1: начал"
# ... еще работа ...
git commit -m "ДЗ 1: закончил"

# 5. Пушишь на свой GitHub
git push origin lesson-01

# 6. Создаешь Pull Request на alsu124/mlops-deploy-course
# -> Описываешь что сделал
# -> Учитель проверяет
# -> Получаешь оценку!

# 7. После проверки можешь удалить ветку
git branch -d lesson-01
git push origin --delete lesson-01
```

---

## ⚠️ ЧАСТЫЕ ОШИБКИ

### Ошибка: "fatal: not a git repository"

**Причина:** Ты не в папке с git репо

**Решение:**
```bash
# Проверь что есть папка .git
ls -la | grep git

# Или перейди в нужную папку
cd mlops-deploy-course
```

### Ошибка: "Please tell me who you are"

**Причина:** Не настроен user.name и user.email

**Решение:**
```bash
git config --global user.name "Твое Имя"
git config --global user.email "твоя@почта.com"
```

### Ошибка: "Permission denied (publickey)"

**Причина:** Git не может подключиться к GitHub через SSH

**Решение:**
- Используй HTTPS вместо SSH:
  ```bash
  git remote set-url origin https://github.com/username/repo.git
  ```
- Или настрой SSH ключи: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### Ошибка: "Your branch is ahead of 'origin/main'"

**Причина:** Ты закоммитил локально но не загрузил на GitHub

**Решение:**
```bash
git push origin branch-name
```

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

- **Git документация:** https://git-scm.com/book/ru/v2
- **GitHub Learning Lab:** https://lab.github.com/
- **Интерактивный Git:** https://learngitbranching.js.org/

---

## ✅ ЧЕКЛИСТ

Перед тем как сдавать ДЗ:

- [ ] Клонировал репо курса
- [ ] Создал свой GitHub репо
- [ ] Создал ветку для ДЗ
- [ ] Выполнил задание
- [ ] Закоммитил с описанием
- [ ] Загрузил на свой GitHub
- [ ] Создал Pull Request
- [ ] Описал что сделал в PR

---

## 🎯 ГОТОВО!

Теперь ты знаешь как работать с Git! 

**Главное помни:**
1. `git clone` - скачиваешь репо
2. `git checkout -b` - создаешь ветку
3. `git add .` - добавляешь файлы
4. `git commit -m` - сохраняешь изменения
5. `git push` - загружаешь на GitHub
6. Pull Request - сдаешь ДЗ

Если вопросы - спрашивай! 💪
