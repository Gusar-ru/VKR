# IlyaBot — Matrix-бот с интеграцией GLPI

Бот для Matrix на основе [matrix-nio](https://github.com/poljar/matrix-nio) с поддержкой E2EE (olm) и интеграцией с GLPI API для работы с тикетами.

## Установка (локально)

1. Клонирование и создание окружения:
   ```powershell
   git clone <ваш-репозиторий>
   cd ilyabot
   py -3.13 -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. Установка зависимостей:
   ```powershell
   pip install -r requirements.txt
   ```
3. Установка olm (Windows, если требуется):
   ```powershell
   pip install .\install_olm\python-olm-3.2.15
   ```
4. Конфигурация:
   ```powershell
   Copy-Item .\config\sample.config.yaml .\config\config.yaml
   notepad .\config\config.yaml
   ```
5. Запуск:
   ```powershell
   python .\main.py
   ```

## Docker

- Build and run:
  ```sh
  docker-compose up --build -d
  ```
- Volumes:
  - `./config` → `/opt/config` (файл `config.yaml`)
  - `./store` → `/opt/store` (состояние E2EE/БД)
  
- Образ: `python:3.13-slim`, установлены `build-essential`, `cmake`, `ninja-build`, `libffi-dev`, `pkg-config` для сборки `python-olm`.

## Структура проекта

### `main.py`

Инициализирует конфигурацию, хранилище бота и `AsyncClient` библиотеки `nio` (используется для получения и отправки событий на homeserver Matrix). Также регистрирует колбэки для `AsyncClient`, чтобы вызывать определенные функции при получении событий (например, приглашение в комнату или новое сообщение).

Также запускает цикл синхронизации. Клиенты Matrix "синхронизируются" с homeserver, постоянно запрашивая новые события. Каждый раз клиент получает токен синхронизации (поле `next_batch` в ответе). Если клиент передает этот токен при следующем запросе (параметр `since` в методе `AsyncClient.sync`), homeserver вернет только новые события, произошедшие *после* этого момента.

Токен сохраняется в базе данных (`storage.py`), поэтому даже после перезапуска бот продолжит синхронизацию с того места, где остановился.

### `config.py`

Читает файл конфигурации (по умолчанию `config.yaml`), обрабатывает его и предоставляет значения остальной части кода. Большинство опций имеют значения по умолчанию. Обязательные параметры: URL homeserver, user_id, access_token.

### `storage.py`

Управляет базой данных SQLite3. Создает таблицы (в `_initial_setup`) и выполняет миграции (`_run_migrations`).
Таблица `sync_token` хранит прогресс синхронизации.

### `sync_token.py`

Класс для сохранения и загрузки токена синхронизации из базы данных.

### `callbacks.py`

Содержит методы обратного вызова (колбэки), запускаемые при получении событий.
- `message`: проверяет, адресовано ли сообщение боту и является ли оно командой. Если да — вызывает обработку команды.
- `invite`: автоматически принимает приглашения и вступает в комнаты.

### `bot_commands.py`

Определения команд бота. Новые команды добавляются в метод `process`.
Объект `Command` создается при получении команды (по префиксу или в ЛС).

### `message_responses.py`

Обработка сообщений, не являющихся командами. Позволяет боту реагировать на ключевые слова или паттерны в чате (например, упоминание номера тикета).

### `chat_functions.py`

Вспомогательные функции для отправки сообщений (например, `send_text_to_room`).

### `errors.py`

Пользовательские классы ошибок (например, ошибки конфигурации).

### `sample.config.yaml`

Пример конфигурационного файла. Скопируйте его в `config.yaml` и заполните своими данными. Не добавляйте `config.yaml` в репозиторий!
## Требования

- Python 3.13 рекомендован (совместим с собранным `python-olm` под Windows)
- Установленный компоновщик/библиотеки для Windows не требуются при использовании локального пакета `install_olm/python-olm-3.2.15`
- Доступ к Matrix homeserver и учетные данные бота
- Доступ к GLPI API: `url`, `user`, `password`, `app_token` (user_token не нужен)

## Установка (локально)

1. Клонируйте репозиторий и создайте виртуальное окружение:
   ```powershell
   git clone https://github.com/theforcer/vision-nio
   cd vision-nio
   py -3.13 -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. Установите зависимости:
   ```powershell
   pip install -r requirements.txt
   ```

## Установка olm (Windows)

На Windows сборка `python-olm` через pip может быть затруднена. В проект включен рабочий пакет `python-olm-3.2.15`.

- Вариант A. Установка из вложенной папки:
  ```powershell
  pip install .\install_olm\python-olm-3.2.15
  ```
- Вариант B. Установка из архива:
  ```powershell
  pip install .\install_olm\python-olm-3.2.15.tar.gz
  ```

Если команда проходит успешно, модуль установился и шифрование (E2EE) будет корректно работать.

### Примечание о сборке из исходников

Если вы устанавливаете `python-olm` не из поставляемого пакета, а из PyPI/исходников, на Windows потребуются инструменты сборки:
- Microsoft Visual C++ Build Tools (компонент MSVC, можно через Visual Studio Build Tools)
- CMake
- (опционально) Ninja, либо используйте MSBuild из Developer PowerShell

При использовании поставляемого пакета из `install_olm/` сборка не требуется — C++ Build Tools не нужны.

### Проверка установки olm

```powershell
python -c "import olm, sys; print('olm', getattr(olm, '__version__', 'unknown'), 'python', sys.version)"
```

Если импорт завершился без ошибок, все готово. При ошибке совместимости используйте тот же минорный Python, под который собран `_libolm.pyd` (рекомендуется 3.13).

## Конфигурация

Скопируйте пример конфига и отредактируйте:
```powershell
Copy-Item .\config\sample.config.yaml .\config\config.yaml
notepad .\config\config.yaml
```

- Обязательные параметры Matrix:
  - `homeserver` — URL homeserver
  - `user_id` — учетная запись бота
  - `access_token` — токен доступа
  - при использовании E2EE убедитесь, что `python-olm` установлен

### GLPI интеграция

В секции `glpi` укажите доступ к API:
```yaml
glpi:
  url: "https://<your-glpi>/apirest.php"
  user: "<glpi-user>"
  password: "<glpi-password>"
  app_token: "<glpi-app-token>"
```

- Используется связка `app_token` + базовая аутентификация (`user`/`password`)
- `user_token` не требуется

## Запуск

- Локально:
  ```powershell
  .\venv\Scripts\Activate.ps1
  python .\main.py
  ```
- Через Docker Compose (по желанию):
  ```powershell
  docker-compose up
  ```
  Добавьте `-d` для фонового запуска.

## Команды бота

- `!help` — показывает справку по доступным командам и примеры
- `!tickets` — выводит последние тикеты GLPI
  - Формат: `#<id> - <name> (<status>)`
  - Пример: `!tickets`
- `!create <title> | <content>` — создает тикет в GLPI
  - Пример: `!create Не работает принтер | Не печатает со вчера, ошибка бумага`

## Диагностика

- Предупреждение `Error validating response: 'one_time_key_counts' is a required property` может появляться при первом запуске E2EE. Это не критично:
  - убедитесь, что установлен `python-olm`
  - дождитесь завершения первоначальной синхронизации ключей
  - проверьте, что бот состоит в комнатах без обязательного E2EE, если тестируете без шифрования

При проблемах с GLPI авторизацией:
- проверьте корректность `glpi.url` (должен оканчиваться на `/apirest.php`)
- убедитесь, что `app_token` активен и соответствует серверу GLPI
- проверьте логин/пароль пользователя GLPI
