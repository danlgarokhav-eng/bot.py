```python
import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from aggregator import (
    build_feed,
    save_feed,
    load_feed,
    send_feed_to_miniapp
)


# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    ""
).strip()


ADMIN_IDS = set()

admin_ids = os.getenv(
    "ADMIN_IDS",
    ""
).strip()


if admin_ids:

    for admin_id in admin_ids.split(","):

        try:

            ADMIN_IDS.add(
                int(admin_id.strip())
            )

        except ValueError:

            pass


# =========================
# TELEGRAM BOT
# =========================

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


# =========================
# /start
# =========================

@dp.message(Command("start"))
async def start(message: Message):

    await message.answer(
        "👋 Привет!\n\n"
        "Я тестовый агрегатор товаров.\n\n"
        "Команды:\n"
        "/search кроссовки — поиск товаров\n"
        "/feed — показать сохранённый фид\n"
        "/refresh — обновить фид"
    )


# =========================
# /search
# =========================

@dp.message(Command("search"))
async def search_command(
    message: Message
):

    parts = message.text.split(
        maxsplit=1
    )

    if len(parts) < 2:

        await message.answer(
            "Напиши запрос.\n\n"
            "Например:\n"
            "/search shoes"
        )

        return


    query = parts[1].strip()


    await message.answer(
        f"🔎 Ищу: {query}..."
    )


    # Получаем товары
    feed = build_feed(
        query
    )


    # Если товаров нет
    if not feed["items"]:

        await message.answer(
            "❌ Товары не найдены."
        )

        return


    # Сохраняем локально
    save_feed(
        feed
    )


    # Отправляем товары на Mini App
    send_feed_to_miniapp(
        feed
    )


    # Показываем первый товар в Telegram
    await show_product(
        message,
        feed["items"],
        0
    )


# =========================
# ПОКАЗ ТОВАРА
# =========================

async def show_product(
    message,
    items,
    index
):

    if not items:
        return


    if index >= len(items):

        index = 0


    item = items[index]


    text = (
        f"👕 {item['name']}\n\n"

        f"🏷 Бренд: "
        f"{item['brand']}\n"

        f"💰 Цена: "
        f"{item['price']}$\n"

        f"⭐ Рейтинг: "
        f"{item['rating']}\n"

        f"📦 Осталось: "
        f"{item['stock']}\n\n"

        f"{item['description']}"
    )


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [

                InlineKeyboardButton(
                    text="❌ Пропустить",
                    callback_data=f"next:{index}"
                ),

                InlineKeyboardButton(
                    text="❤️ Нравится",
                    callback_data=f"like:{index}"
                )

            ],

            [

                InlineKeyboardButton(
                    text="🔗 Открыть товар",
                    url=item["link"]
                )

            ]

        ]
    )


    await message.answer_photo(
        photo=item["image"],
        caption=text[:1024],
        reply_markup=keyboard
    )


# =========================
# NEXT
# =========================

@dp.callback_query(
    lambda c: c.data.startswith("next:")
)
async def next_product(
    callback: CallbackQuery
):

    index = int(
        callback.data.split(":")[1]
    )


    feed = load_feed()


    items = feed.get(
        "items",
        []
    )


    if not items:

        await callback.answer(
            "Фид пуст"
        )

        return


    next_index = index + 1


    if next_index >= len(items):

        next_index = 0


    try:

        await callback.message.delete()

    except Exception:

        pass


    await show_product(
        callback.message,
        items,
        next_index
    )


    await callback.answer()


# =========================
# LIKE
# =========================

@dp.callback_query(
    lambda c: c.data.startswith("like:")
)
async def like_product(
    callback: CallbackQuery
):

    index = int(
        callback.data.split(":")[1]
    )


    feed = load_feed()


    items = feed.get(
        "items",
        []
    )


    if not items:

        await callback.answer(
            "Фид пуст"
        )

        return


    if index >= len(items):

        await callback.answer(
            "Товар не найден"
        )

        return


    item = items[index]


    await callback.answer(
        f"❤️ {item['name']}",
        show_alert=False
    )


# =========================
# /feed
# =========================

@dp.message(Command("feed"))
async def feed_command(
    message: Message
):

    feed = load_feed()


    items = feed.get(
        "items",
        []
    )


    if not items:

        await message.answer(
            "Фид пуст.\n"
            "Используй /search shoes"
        )

        return


    await show_product(
        message,
        items,
        0
    )


# =========================
# /refresh
# =========================

@dp.message(Command("refresh"))
async def refresh_command(
    message: Message
):

    # Проверяем администратора
    if message.from_user.id not in ADMIN_IDS:

        await message.answer(
            "⛔ Эта команда доступна только администратору."
        )

        return


    await message.answer(
        "🔄 Обновляю каталог..."
    )


    # Получаем товары
    feed = build_feed()


    if not feed["items"]:

        await message.answer(
            "❌ Не удалось получить товары."
        )

        return


    # Сохраняем локально
    save_feed(
        feed
    )


    # Отправляем в Mini App
    send_feed_to_miniapp(
        feed
    )


    await message.answer(
        f"✅ Каталог обновлён.\n"
        f"Товаров: {feed['count']}"
    )


# =========================
# ЗАПУСК
# =========================

async def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "Не задан BOT_TOKEN.\n"
            "Добавь переменную BOT_TOKEN в Railway."
        )


    print(
        "================================="
    )

    print(
        "Telegram-бот запускается..."
    )

    print(
        f"Администраторов: {len(ADMIN_IDS)}"
    )

    print(
        "Mini App: "
        "https://miniapp-server-production.up.railway.app"
    )

    print(
        "================================="
    )


    await dp.start_polling(
        bot
    )


# =========================
# START
# =========================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
```

Но **одного этого файла недостаточно**. В `aggregator.py` обязательно должна быть функция `send_feed_to_miniapp()`, потому что этот бот её импортирует.

И главное: **сначала не меняй Start Command наугад**. У тебя сейчас Railway пытается запустить `/app/bot.py`, но такого файла по факту не находит. Покажи мне содержимое папки `bot` в GitHub — и я дам точную команду запуска для Railway.

После этого мы уже проверим, появились ли товары на:

`miniapp-server-production.up.railway.app`
