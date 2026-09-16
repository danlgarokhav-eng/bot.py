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
# TELEGRAM
# =========================

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


# =========================
# START
# =========================

@dp.message(Command("start"))
async def start(
    message: Message
):

    await message.answer(
        "👋 Привет!\n\n"
        "Я тестовый агрегатор товаров.\n\n"

        "Команды:\n"
        "/search кроссовки — поиск товаров\n"
        "/feed — показать сохранённый фид\n"
        "/refresh — обновить фид"
    )


# =========================
# SEARCH
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

    # Проверяем результат
    if not feed.get("items"):

        await message.answer(
            "❌ Товары не найдены."
        )

        return

    # Сохраняем локальный фид
    saved = save_feed(
        feed
    )

    if not saved:

        await message.answer(
            "⚠️ Товары найдены, "
            "но не удалось сохранить фид."
        )

    # =========================
    # ОТПРАВКА В MINI APP
    # =========================

    print(
        f"Mini App: отправляю "
        f"{feed['count']} товаров..."
    )

    miniapp_sent = send_feed_to_miniapp(
        feed
    )

    if miniapp_sent:

        await message.answer(
            f"✅ Найдено товаров: "
            f"{feed['count']}\n"
            f"🌐 Фид отправлен в Mini App."
        )

    else:

        await message.answer(
            f"⚠️ Найдено товаров: "
            f"{feed['count']}\n"
            f"❌ Не удалось отправить "
            f"фид в Mini App."
        )

    # Показываем первый товар
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

    if index < 0:
        index = 0

    item = items[index]

    name = item.get(
        "name",
        "Без названия"
    )

    brand = item.get(
        "brand",
        "Без бренда"
    )

    price = item.get(
        "price",
        0
    )

    rating = item.get(
        "rating",
        0
    )

    stock = item.get(
        "stock",
        0
    )

    description = item.get(
        "description",
        ""
    )

    image = item.get(
        "image",
        ""
    )

    link = item.get(
        "link",
        ""
    )

    text = (
        f"👕 {name}\n\n"

        f"🏷 Бренд: "
        f"{brand}\n"

        f"💰 Цена: "
        f"{price}$\n"

        f"⭐ Рейтинг: "
        f"{rating}\n"

        f"📦 Осталось: "
        f"{stock}\n\n"

        f"{description}"
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
                    url=link
                )
            ]

        ]
    )

    # Если изображения нет,
    # отправляем обычное сообщение
    if image:

        await message.answer_photo(
            photo=image,
            caption=text[:1024],
            reply_markup=keyboard
        )

    else:

        await message.answer(
            text[:4096],
            reply_markup=keyboard
        )


# =========================
# СЛЕДУЮЩИЙ ТОВАР
# =========================

@dp.callback_query(
    lambda c: (
        c.data
        and c.data.startswith("next:")
    )
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
# ЛАЙК
# =========================

@dp.callback_query(
    lambda c: (
        c.data
        and c.data.startswith("like:")
    )
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

    name = item.get(
        "name",
        "Товар"
    )

    await callback.answer(
        f"❤️ {name}",
        show_alert=False
    )


# =========================
# FEED
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
# REFRESH
# =========================

@dp.message(Command("refresh"))
async def refresh_command(
    message: Message
):

    if message.from_user.id not in ADMIN_IDS:

        await message.answer(
            "⛔ Эта команда доступна "
            "только администратору."
        )

        return

    await message.answer(
        "🔄 Обновляю каталог..."
    )

    # Получаем новый фид
    feed = build_feed()

    if not feed.get("items"):

        await message.answer(
            "❌ Не удалось получить товары."
        )

        return

    # Сохраняем
    save_feed(
        feed
    )

    # =========================
    # ОТПРАВКА В MINI APP
    # =========================

    print(
        f"Mini App: отправляю "
        f"{feed['count']} товаров..."
    )

    miniapp_sent = send_feed_to_miniapp(
        feed
    )

    if miniapp_sent:

        await message.answer(
            f"✅ Каталог обновлён.\n"
            f"Товаров: {feed['count']}\n"
            f"🌐 Mini App обновлён."
        )

    else:

        await message.answer(
            f"⚠️ Каталог обновлён.\n"
            f"Товаров: {feed['count']}\n"
            f"❌ Mini App не удалось обновить."
        )


# =========================
# ЗАПУСК
# =========================

async def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "Не задан BOT_TOKEN.\n"
            "В Railway добавь переменную "
            "BOT_TOKEN."
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


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
```
