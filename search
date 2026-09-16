@dp.message(Command("search"))
async def search_command(message: Message):

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        await message.answer(
            "Напиши запрос.\n\n"
            "Например:\n"
            "/search shoes"
        )
        return

    query = parts[1].strip()

    await message.answer(
        f"🔎 Ищу товары: {query}..."
    )

    # Получаем товары
    feed = build_feed(query)

    # Проверяем результат
    if not feed.get("items"):
        await message.answer(
            "❌ Товары не найдены."
        )
        return

    # Сохраняем фид
    save_feed(feed)

    # Отправляем фид в Mini App
    miniapp_sent = send_feed_to_miniapp(feed)

    if miniapp_sent:
        await message.answer(
            f"✅ Найдено товаров: {feed['count']}\n"
            f"🌐 Фид отправлен в Mini App."
        )
    else:
        await message.answer(
            f"⚠️ Найдено товаров: {feed['count']}\n"
            f"❌ Не удалось отправить фид в Mini App."
        )

    # Показываем первый товар в Telegram
    await show_product(
        message,
        feed["items"],
        0
    )
