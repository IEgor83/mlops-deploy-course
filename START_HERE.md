# 🚀 НАЧНИ ОТСЮДА

Привет! Ты на курсе MLOps. Вот что нужно знать чтобы начать.

---

## 📋 ЧТО ДЕЛАТЬ (в порядке)

### Шаг 1: Прочитай эту страницу (ты здесь!) ✅

### Шаг 2: Настрой окружение
- Открой [docs/setup.md](docs/setup.md)
- Установи Python 3.11+
- Создай виртуальное окружение `.venv`

### Шаг 3: Изучи как работать с заданиями
- Открой [HOW_TO_SUBMIT_LABS.md](HOW_TO_SUBMIT_LABS.md)
- Там полная инструкция как сдавать лабы

### Шаг 4: Начни первую лабу
```bash
# 1. Прочитай задание
cat lessons/01-intro-project-setup/handout.md

# 2. Выполни все 5 шагов в папке template/
cd template
```

### Шаг 5: Сохраняй работу в своём репозитории
- Создай свой GitHub репо
- Пушь туда свои изменения после каждого занятия
- Один раз пришли ссылку на репо преподавателю в личные сообщения

Отдельно сдавать каждую лабу не нужно: весь проект сдаётся лично
в конце семестра.

---

## 🏗️ СТРУКТУРА РЕПОЗИТОРИЯ

```
mlops-deploy-course/
├── START_HERE.md                      ← Ты сейчас здесь
├── HOW_TO_SUBMIT_LABS.md              ← Полная инструкция
├── STUDENT_GIT_GUIDE.md               ← Учебник Git
├── GIT_CHEATSHEET.md                  ← Git шпаргалка
│
├── docs/
│   ├── setup.md                       ← Установка Python
│   ├── syllabus.md                    ← План 18 занятий
│   └── theory/                        ← Теория курса
│
├── lessons/                           ← 18 занятий
│   ├── 01-intro-project-setup/
│   │   └── handout.md                 ← ТВОЁ ЗАДАНИЕ
│   └── ... (остальные)
│
└── template/                          ← СТАРТОВЫЙ СКЕЛЕТ
    ├── notebooks/baseline_notebook.py
    ├── src/
    │   ├── prepare.py                 ← TODO: заполни
    │   ├── features.py                ← TODO: заполни
    │   └── train.py                   ← TODO: заполни
    └── params.yaml                    ← TODO: заполни
```

---

## ❓ ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ

**Где найти задание?**
→ `lessons/01-intro-project-setup/handout.md`

**Где писать код?**
→ В папке `template/src/` и других местах из handout.md

**Как сдать работу?**
→ [HOW_TO_SUBMIT_LABS.md](HOW_TO_SUBMIT_LABS.md)

**Нужен ли мне бот?**
→ Нет, бот не используется.

**Как я буду сдавать?**
→ Промежуточной сдачи нет. Работа копится в твоём репозитории,
в конце семестра показываешь весь проект лично. Подробно —
в [HOW_TO_SUBMIT_LABS.md](HOW_TO_SUBMIT_LABS.md)

---

## 🚀 БЫСТРЫЙ СТАРТ

```bash
git clone https://github.com/alsu124/mlops-deploy-course.git
cd mlops-deploy-course
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cat lessons/01-intro-project-setup/handout.md
```

---

## ✅ ЧЕК-ЛИСТ

- [ ] Python 3.11+ установлен
- [ ] Virtual environment активен (видишь `(.venv)` в терминале)
- [ ] Зависимости установлены
- [ ] Git установлен и конфигурирован
- [ ] Создал свой GitHub репо
- [ ] Прочитал HOW_TO_SUBMIT_LABS.md

**Готов? Начинай первую лабу! 💪**
