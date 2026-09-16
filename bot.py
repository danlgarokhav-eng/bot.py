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
    load_feed
)


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


bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


# -------------------------
# Старт
# -------------------------

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


# -------------------------
# Поиск
# -------------------------

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

    query = parts[1]

    await message.answer(
        f"🔎 Ищу: {query}..."
    )

    feed = build_feed(query)

    if not feed["items"]:

        await message.answer(
            "❌ Товары не найдены."
        )

        return

    save_feed(feed)

    await show_product(
        message,
        feed["items"],
        0
    )


# -------------------------
# Показ товара
# -------------------------

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


# -------------------------
# Следующий товар
# -------------------------

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

    await callback.message.delete()

    await show_product(
        callback.message,
        items,
        next_index
    )

    await callback.answer()


# -------------------------
# Лайк
# -------------------------

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

    item = items[index]

    await callback.answer(
        f"❤️ {item['name']}",
        show_alert=False
    )


# -------------------------
# Показ сохранённого фида
# -------------------------

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


# -------------------------
# Обновление фида
# -------------------------

@dp.message(Command("refresh"))
async def refresh_command(
    message: Message
):

    if message.from_user.id not in ADMIN_IDS:

        await message.answer(
            "⛔ Эта команда доступна только администратору."
        )

        return

    await message.answer(
        "🔄 Обновляю каталог..."
    )

    feed = build_feed()

    if not feed["items"]:

        await message.answer(
            "❌ Не удалось получить товары."
        )

        return

    save_feed(feed)

    await message.answer(
        f"✅ Каталог обновлён.\n"
        f"Товаров: {feed['count']}"
    )


# -------------------------
# Запуск
# -------------------------

async def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "Не задан BOT_TOKEN.\n"
            "В CMD:\n"
            "set BOT_TOKEN=ТОКЕН_БОТА"
        )

    print(
        "Telegram-бот запускается..."
    )

    print(
        f"Администраторов: "
        f"{len(ADMIN_IDS)}"
    )

    await dp.start_polling(
        bot
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )
