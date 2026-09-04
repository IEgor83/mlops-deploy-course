# Занятие 4. Версионирование данных: DVC

## Проблема

Git хранит каждую версию бинарного файла целиком. Датасет на 200 МБ,
изменённый пять раз, — это гигабайт в репозитории навсегда: история
не чистится обычными средствами.

Но и не версионировать данные нельзя: метрика 0.79 без ответа на вопрос
«на каких данных» — бесполезное число.

DVC решает это так: в Git едет маленький файл с хешем и размером,
а сами данные лежат в отдельном хранилище (remote).

## Шаг 1. Инициализация

```bash
pip install "dvc>=3.48,<4.0"
dvc init
git status
```

`dvc init` создал `.dvc/` и уже прописал нужные исключения в `.gitignore`.
Закоммитьте это:

```bash
git add .dvc .dvcignore .gitignore
git commit -m "Инициализировать DVC"
```

## Шаг 2. Данные под контроль

Если данные уже были закоммичены в Git — сначала уберите их из индекса:

```bash
git rm -r --cached data/ models/ 2>/dev/null; git commit -m "Убрать данные из Git" || true
```

Теперь:

```bash
make data
dvc add data/raw/churn.csv
```

Посмотрите, что получилось:

```bash
cat data/raw/churn.csv.dvc
cat data/raw/.gitignore
```

В `.dvc`-файле — хеш (`md5`), размер и путь. Это и есть то, что едет в Git.
DVC заодно дописал сам CSV в `.gitignore`, чтобы вы случайно его не закоммитили.

```bash
git add data/raw/churn.csv.dvc data/raw/.gitignore
git commit -m "Добавить сырые данные под DVC"
```

## Шаг 3. Локальный remote

Remote — это место, где физически лежат данные. Начнём с папки на диске.

**Важно:** папка должна быть **вне** вашего репозитория. Иначе данные
вернутся в Git через чёрный ход.

```bash
dvc remote add -d localremote ~/dvcstore
git add .dvc/config && git commit -m "Настроить локальный DVC remote"

dvc push
ls -R ~/dvcstore | head
```

В хранилище файлы лежат по хешу, разложенные по подпапкам — это тот же
принцип, что у объектной базы Git.

Проверьте, что восстановление работает:

```bash
rm data/raw/churn.csv
dvc pull
ls -lh data/raw/churn.csv
```

## Шаг 4. Модель тоже артефакт

```bash
make prepare && make train
dvc add models/model.joblib
git add models/model.joblib.dvc models/.gitignore
git commit -m "Добавить модель под DVC"
dvc push
```

Теперь у вас связка: коммит кода ↔ версия данных ↔ версия модели.

## Шаг 5. Главный эксперимент занятия

Убедитесь, что связка работает. Измените данные:

```bash
python -m src.data.generate --n 5000
dvc add data/raw/churn.csv
git add data/raw/churn.csv.dvc && git commit -m "Уменьшить датасет до 5000"
dvc push
wc -l data/raw/churn.csv        # 5001
```

Вернитесь к предыдущей версии:

```bash
git checkout HEAD~1
dvc checkout
wc -l data/raw/churn.csv        # 20001 — данные вернулись!
```

Вернитесь обратно:

```bash
git checkout -
dvc checkout
```

Вот ради этого всё и делалось: `git checkout` возвращает код,
`dvc checkout` — соответствующие ему данные.

## Шаг 6. S3-совместимое хранилище (MinIO)

Локальная папка не работает для команды. Поднимем настоящее хранилище:

```bash
docker run -d --name minio -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

Откройте http://localhost:9001 (minioadmin / minioadmin) и создайте
бакет `mlops`.

Настройте DVC:

```bash
pip install "dvc-s3>=3.0,<4.0"
dvc remote add -d minio s3://mlops/churn
dvc remote modify minio endpointurl http://localhost:9000

# Ключи — НЕ в .dvc/config: он коммитится в Git.
dvc remote modify --local minio access_key_id minioadmin
dvc remote modify --local minio secret_access_key minioadmin

dvc push
```

Обратите внимание на `--local`: эта настройка пишется в `.dvc/config.local`,
который в `.gitignore`. Секреты в Git не попадают — то же правило, что на занятии 2.

Проверьте в веб-консоли MinIO: в бакете появились объекты.

## Что сдать

- [ ] `dvc init` выполнен, `.dvc/` в Git
- [ ] `data/raw/churn.csv` и `models/model.joblib` под DVC
- [ ] Remote настроен, `dvc push` отработал
- [ ] Показан откат: `git checkout HEAD~1 && dvc checkout` возвращает старые данные
- [ ] Секреты remote — в `.dvc/config.local`, не в Git

## Домашнее задание (1,5–2 ч)

1. Проверьте полное восстановление с нуля:
   ```bash
   git clone <ваш-репо> /tmp/fresh && cd /tmp/fresh
   dvc remote modify --local minio access_key_id minioadmin
   dvc remote modify --local minio secret_access_key minioadmin
   dvc pull
   ls -lh data/raw models
   ```
   Если данные не подтянулись — вы не сделали `dvc push`. Это самая частая
   ошибка, и на зачёте она означает нерабочий проект.

2. Опишите в `README.md` раздел «Данные»: где лежит remote, как получить
   данные, что делать новому участнику проекта. Пишите для человека,
   который видит ваш проект впервые.

3. Ответьте письменно в `README.md`: почему `.dvc`-файл нужно коммитить,
   а сам датасет — нет? Что сломается, если сделать наоборот?

## Полезное

| Команда | Зачем |
|---|---|
| `dvc status` | что изменилось в рабочей копии |
| `dvc status -c` | что расходится с remote |
| `dvc pull` / `dvc push` | скачать / загрузить данные |
| `dvc checkout` | привести данные в соответствие с `.dvc`-файлами |
| `dvc remote list -v` | какие remote настроены |
| `dvc doctor` | диагностика при непонятных ошибках |
