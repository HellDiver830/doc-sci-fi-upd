# doc-sci-fi-upd

Полнофункциональный прототип системы автоматизации документооборота и управления доступом в корпоративном приложении.

## Описание

Проект состоит из двух основных компонентов:

* **Backend (server.py)** — REST‑API на Flask для:

  * Регистрации и аутентификации пользователей (JWT).
  * Разграничения ролей (`superadmin`, `teacher`, `student`).
  * Управления списком предметов и курсов, чтения/обновления данных JSON.
  * Генерации документов (методичка, сводный отчёт, билеты) в LaTeX формате.
  * Управления пользователями и назначением прав на предметы.

* **Frontend (main.py)** — десктопное приложение на Eel (Python + HTML/JS) для:

  * Ввода логина/пароля и получения токена.
  * Отображения списка доступных предметов.
  * Просмотра и редактирования информации о курсе.
  * Генерации билетов и документации по предмету.
  * Управления пользователями и правами (для `superadmin`).

## Структура репозитория ([github.com](https://github.com/HellDiver830/doc-sci-fi-upd))

```
/design                 # HTML/CSS/JS интерфейса Eel
/docs                   # Пользовательские и технические руководства
/json_output            # Хранимые данные по предметам (JSON-файлы)
/versions               # Архивы старых версий JSON при изменениях
/competence010302.json  # Шаблон компетенций и структуры курса
/users.db               # SQLite база пользователей
main.py                 # Frontend на Eel: клиентские функции (login, register, CRUD)
server.py               # Backend на Flask: обработка API-запросов
```

## Технологии

* Python 3.8+
* Flask, flask-cors (API сервер)
* Eel (Python + HTML/JS десктопный UI)
* SQLite (база пользователей)
* JSON-файлы для хранения данных курсов
* JWT (PyJWT) для аутентификации
* Requests для клиентских HTTP-запросов

## Установка

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/HellDiver830/doc-sci-fi-upd.git
   cd doc-sci-fi-upd
   ```
2. Создайте виртуальное окружение и активируйте:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\\Scripts\\activate # Windows
   ```
3. Установите зависимости:

   ```bash
   pip install flask flask-cors eel requests pyjwt
   ```
4. Инициализация данных:

   * При первом запуске `server.py` создаст новую базу `users.db` и добавит пользователя `superadmin/superadmin`.
   * Папки `json_output`, `versions`, `docs` создаются автоматически.

## Запуск

1. **Backend**:

   ```bash
   python server.py
   ```

   API доступен по адресу `http://0.0.0.0:5000/api/`.

2. **Frontend**:
   В отдельном терминале:

   ```bash
   python main.py
   ```

   Откроется окно приложения (HTML-шаблон в `design/index.html`).

## Пример работы

1. Зарегистрируйтесь или войдите под `superadmin` (пароль `superadmin`).
2. Назначьте роли и предметы через UI.
3. Учитель может просмотреть и изменить содержание курса.
4. Сгенерировать билеты или документы (`methodichka`, `summary`, `bilets`).

## Лицензия

MIT License
