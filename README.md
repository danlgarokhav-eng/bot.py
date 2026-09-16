# Telegram WB Aggregator

Проект получает товары из поиска Wildberries и отдаёт их Telegram-боту.

## Главное изменение

Telegram-бот НЕ делает запрос к WB при запуске.

Результаты кэшируются в `wb_cache.json`.

При повторном поиске того же запроса в течение 15 минут новый запрос к WB не выполняется.

При HTTP 429 программа:
1. читает `X-Ratelimit-Retry` / `Retry-After`, если они есть;
2. ждёт;
3. повторяет запрос;
4. использует старый кэш, если WB всё равно недоступен.

## Установка

```text
py -m pip install -r requirements.txt
```

## Запуск

В CMD из папки проекта:

```text
set BOT_TOKEN=ТОКЕН_ОТ_BOTFATHER
set ADMIN_IDS=123456789
py wb_bot.py
```

Если нужен только тест поиска без Telegram:

```text
py search.py
```

Или:

```text
py admin.py
```

## Команды Telegram

```text
/start
/search кроссовки
```

Для администратора:

```text
/admin
/refresh кроссовки
/feed
```

## Как узнать Telegram ID

Можно временно написать боту `/start`, а затем добавить свой ID в `ADMIN_IDS`.

Например:

```text
set ADMIN_IDS=123456789
```

Несколько:

```text
set ADMIN_IDS=123456789,987654321
```

## Важно

`google_script.gs` специально не обращается к WB напрямую.

Не запускай несколько копий `wb_bot.py` одновременно с одного IP, иначе можно снова получить 429.
