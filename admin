from aggregator import build_feed, save_feed


def admin_generate(query=""):

    print(
        f"Админ: создаём фид. "
        f"Запрос: {query or 'все товары'}"
    )

    feed = build_feed(query)

    if not feed["items"]:

        print(
            "Админ: товары не получены."
        )

        return False

    save_feed(feed)

    print(
        f"Админ: фид создан. "
        f"Товаров: {feed['count']}"
    )

    return True
