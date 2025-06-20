# Oil Spill AI Backend

Backend-сервис для автоматизированной обработки спутниковых изображений с целью выделения разливов нефти. Реализован на FastAPI, поддерживает асинхронную обработку через Celery и взаимодействует с ML микросервисом для сегментации изображений.

---

## Архитектура

- **FastAPI** — REST API для загрузки архивов, скачивания результатов и проверки статуса задач.
- **Celery** — асинхронная очередь задач для фоновой обработки изображений.
- **Redis** — брокер и backend для Celery.
- **ML микросервис** — отдельный сервис для сегментации изображений (см. папку `ml`).

---

## Как устроен модуль

### Основные компоненты

- **FastAPI-приложение (`app/main.py`)**  
  Реализует REST API для загрузки архивов изображений, проверки статуса задач и скачивания результатов.  
  - `/api/upload` — принимает zip-архив, извлекает изображения, инициирует асинхронную задачу обработки через Celery.
  - `/api/status/{job_id}` — возвращает статус задачи Celery.
  - `/api/download/{user_hash}` — позволяет скачать архив с результатами.
  - `/api/archive_time_left/{user_hash}` — сообщает, сколько времени архив будет доступен для скачивания.

- **Celery worker (`app/celery_worker.py`, `app/tasks.py`)**  
  Обрабатывает задачи в фоне:
  - `process_archive_task` — для каждого изображения вызывает ML микросервис, сохраняет результаты, формирует итоговый архив.
  - Использует Redis как брокер и backend.

- **Вспомогательные функции (`app/utils.py`)**  
  - Сохраняют и извлекают архивы, генерируют уникальные идентификаторы пользователей.
  - Отправляют изображения в ML микросервис (`send_to_ml_service`), принимают и сохраняют результаты.
  - Формируют итоговые архивы с результатами, инициируют их автоматическое удаление через Celery.

- **Удаление временных файлов (`app/delete_tasks.py`)**  
  - Автоматически удаляет архивы и все временные файлы пользователя спустя заданное время (по умолчанию 10 минут после создания архива).

### Жизненный цикл задачи

1. **Пользователь загружает zip-архив** через `/api/upload`.
2. Архив сохраняется, изображения извлекаются и переименовываются.
3. Для каждого изображения создаётся асинхронная задача Celery:
   - Изображение отправляется в ML микросервис.
   - Результат сохраняется.
4. После обработки всех файлов формируется zip-архив с результатами.
5. Архив доступен для скачивания по `/api/download/{user_hash}` в течение ограниченного времени.
6. По истечении времени архив и все временные файлы автоматически удаляются.

### Хранение данных

- Все временные и итоговые файлы хранятся в папке `results/`, для каждого пользователя создаётся отдельная подпапка.
- Для каждого архива создаётся meta-файл с временем создания для отслеживания времени жизни архива.

### Конфигурация

- Все параметры (пути, адрес ML сервиса, параметры Redis) задаются через переменные окружения или `.env` файл.
- По умолчанию ML сервис ожидается на `http://localhost:8002/segment`, Redis — на `localhost:6379`.

---

## Быстрый старт

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Запустите FastAPI сервер:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. Запустите Celery worker (убедитесь, что Redis уже запущен):
   ```bash
   celery -A app worker --loglevel=info
   ```

4. (Опционально) Запустите Redis через Docker:
   ```bash
   docker run --name redis-container -p 6379:6379 -d redis
   ```

---

## API

- `POST /api/upload` — загрузка zip-архива с изображениями, возвращает `job_id` и `user_hash`.
- `GET /api/status/{job_id}` — проверка статуса задачи.
- `GET /api/download/{user_hash}` — скачивание zip-архива с результатами.
- `GET /api/archive_time_left/{user_hash}` — время жизни архива в секундах.

---

## Структура проекта

```
backend/
├── app/
│   ├── main.py           # FastAPI-приложение, основные эндпоинты
│   ├── celery_worker.py  # Инициализация Celery
│   ├── tasks.py          # Celery задачи для обработки архивов
│   ├── utils.py          # Вспомогательные функции, взаимодействие с ML сервисом
│   ├── delete_tasks.py   # Задачи для удаления временных файлов
├── requirements.txt      # Зависимости Python
├── Dockerfile            # Docker-образ (опционально)
├── .env                  # Переменные окружения (опционально)
└── README.md             # Документация (этот файл)
```

---

## Зависимости

- fastapi
- uvicorn
- celery[redis]
- redis
- requests
- aiofiles
- python-multipart
- python-dotenv
- httpx

Установите все зависимости командой:
```bash
pip install -r requirements.txt
```

---

## Примечания

- Для работы требуется запущенный ML микросервис (см. папку `ml`).
- Для настройки CORS и переменных окружения используйте `.env`.
- Все временные и итоговые файлы хранятся в директории `results/`.
- В случае вопросов — смотрите исходный код или обращайтесь к разработчику.
