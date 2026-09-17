import json
import os
import requests

from kufar import search_kufar


# ============================================================
# НАСТРОЙКИ
# ============================================================

FEED_FILE = "feed.json"

# URL твоего Mini App сервера
MINIAPP_URL = os.getenv(
    "MINIAPP_URL",
    "https://miniapp-server-production.up.railway.app"
).strip()


# Количество товаров по умолчанию
DEFAULT_LIMIT = 50

# Запрос по умолчанию для /refresh
DEFAULT_QUERY = os.getenv(
    "DEFAULT_QUERY",
    "кроссовки"
).strip()


# ============================================================
# ПОСТРОЕНИЕ FEED
# ============================================================

def build_feed(query=None, limit=DEFAULT_LIMIT):
    """
    Собирает товары из всех подключённых источников.

    Сейчас подключён только Kufar.
    Позже сюда можно добавить:
        - Wildberries
        - Ozon
        - AliExpress
        - другие площадки
    """

    if query is None:
        query = DEFAULT_QUERY

    query = str(query).strip()

    if not query:
        query = DEFAULT_QUERY

    print()
    print("=" * 60)
    print("STYLEFLOW — BUILD FEED")
    print("=" * 60)
    print("Запрос:", query)
    print("Лимит:", limit)

    products = []

    # ========================================================
    # KUFAR
    # ========================================================

    try:
        print()
        print("Получаю товары Kufar...")

        kufar_products = search_kufar(
            query=query,
            limit=limit
        )

        if not isinstance(kufar_products, list):
            kufar_products = []

        print(
            f"Kufar: получено {len(kufar_products)} товаров"
        )

        products.extend(kufar_products)

    except Exception as e:
        print(
            f"Ошибка агрегатора Kufar: {e}"
        )

    # ========================================================
    # ЗДЕСЬ ПОЗЖЕ БУДУТ ДРУГИЕ ИСТОЧНИКИ
    # ========================================================

    # Пример:
    #
    # from wildberries import search_wildberries
    #
    # wb_products = search_wildberries(
    #     query=query,
    #     limit=limit
    # )
    #
    # products.extend(wb_products)


    # ========================================================
    # ОГРАНИЧЕНИЕ КОЛИЧЕСТВА
    # ========================================================

    products = products[:limit]


    # ========================================================
    # ФИНАЛЬНАЯ НОРМАЛИЗАЦИЯ
    # ========================================================

    normalized_products = []

    for product in products:

        if not isinstance(product, dict):
            continue

        # ----------------------------------------------------
        # Унифицированное название
        # ----------------------------------------------------

        title = (
            product.get("title")
            or product.get("name")
            or "Без названия"
        )

        # ----------------------------------------------------
        # Цена
        # ----------------------------------------------------

        price = product.get(
            "price",
            0
        )

        try:
            price = float(price)

            # Если это целое число —
            # сохраняем красивый вид.
            if price.is_integer():
                price = int(price)

        except (
            ValueError,
            TypeError
        ):
            price = 0


        # ----------------------------------------------------
        # Валюта
        # ----------------------------------------------------

        currency = (
            product.get("currency")
            or "BYN"
        )

        currency = str(
            currency
        ).upper()


        # ----------------------------------------------------
        # Ссылка
        # ----------------------------------------------------

        url = (
            product.get("url")
            or product.get("link")
            or ""
        )


        # ----------------------------------------------------
        # Изображение
        # ----------------------------------------------------

        image = (
            product.get("image")
            or ""
        )


        # ----------------------------------------------------
        # Остальные поля
        # ----------------------------------------------------

        normalized_product = {
            "id": product.get(
                "id",
                ""
            ),

            "source": product.get(
                "source",
                ""
            ),

            "external_id": product.get(
                "external_id",
                ""
            ),

            "title": str(
                title
            ).strip(),

            "name": str(
                title
            ).strip(),

            "brand": product.get(
                "brand",
                ""
            ),

            "category": product.get(
                "category",
                ""
            ),

            "price": price,

            "oldPrice": product.get(
                "oldPrice",
                0
            ),

            "currency": currency,

            "rating": product.get(
                "rating",
                0
            ),

            "stock": product.get(
                "stock",
                0
            ),

            "image": image,

            "images": product.get(
                "images",
                []
            ),

            "url": url,

            "link": url,

            "description": product.get(
                "description",
                ""
            ),

            # raw оставляем для отладки.
            # Потом при необходимости его можно убрать,
            # чтобы feed.json был меньше.
            "raw": product.get(
                "raw",
                {}
            )
        }

        normalized_products.append(
            normalized_product
        )


    # ========================================================
    # СОЗДАЁМ FEED
    # ========================================================

    feed = {
        "count": len(
            normalized_products
        ),

        "query": query,

        "items": normalized_products
    }


    print()
    print("=" * 60)
    print("FEED ГОТОВ")
    print("=" * 60)
    print(
        "Товаров:",
        feed["count"]
    )

    return feed


# ============================================================
# СОХРАНЕНИЕ FEED
# ============================================================

def save_feed(feed):
    """
    Сохраняет feed локально в feed.json.
    """

    try:

        if not isinstance(
            feed,
            dict
        ):
            print(
                "save_feed: feed должен быть dict"
            )

            return False


        with open(
            FEED_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                feed,
                f,
                ensure_ascii=False,
                indent=2
            )


        print(
            f"Feed сохранён: {FEED_FILE}"
        )

        return True


    except Exception as e:

        print(
            f"Ошибка сохранения feed: {e}"
        )

        return False


# ============================================================
# ЗАГРУЗКА FEED
# ============================================================

def load_feed():
    """
    Загружает feed из feed.json.
    """

    if not os.path.exists(
        FEED_FILE
    ):

        print(
            "Feed не найден."
        )

        return {
            "count": 0,
            "query": "",
            "items": []
        }


    try:

        with open(
            FEED_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            feed = json.load(f)


        if not isinstance(
            feed,
            dict
        ):

            print(
                "Некорректный формат feed."
            )

            return {
                "count": 0,
                "query": "",
                "items": []
            }


        if not isinstance(
            feed.get("items"),
            list
        ):

            feed["items"] = []


        feed["count"] = len(
            feed["items"]
        )


        return feed


    except (
        json.JSONDecodeError,
        OSError
    ) as e:

        print(
            f"Ошибка загрузки feed: {e}"
        )

        return {
            "count": 0,
            "query": "",
            "items": []
        }


# ============================================================
# ОТПРАВКА FEED В MINI APP
# ============================================================

def send_feed_to_miniapp(feed):
    """
    Отправляет товары в miniapp-server.

    miniapp-server ожидает:
        POST /update_feed

    Body:
        [
            {...},
            {...}
        ]

    То есть отправляем НЕ весь объект feed,
    а только feed["items"].
    """

    try:

        if not isinstance(
            feed,
            dict
        ):

            print(
                "send_feed_to_miniapp: "
                "feed должен быть dict"
            )

            return False


        items = feed.get(
            "items",
            []
        )


        if not isinstance(
            items,
            list
        ):

            print(
                "send_feed_to_miniapp: "
                "items должен быть list"
            )

            return False


        url = (
            MINIAPP_URL.rstrip("/")
            + "/update_feed"
        )


        print()
        print("=" * 60)
        print("ОТПРАВКА В MINI APP")
        print("=" * 60)
        print(
            "URL:",
            url
        )
        print(
            "Товаров:",
            len(items)
        )


        response = requests.post(
            url,
            json=items,
            timeout=30
        )


        print(
            "HTTP:",
            response.status_code
        )


        if response.status_code != 200:

            print(
                "Ошибка Mini App:"
            )

            print(
                response.text[:2000]
            )

            return False


        try:

            result = response.json()

        except ValueError:

            result = {}


        print(
            "Ответ Mini App:",
            result
        )


        if result.get("status") == "ok":

            print(
                "Feed успешно отправлен."
            )

            return True


        print(
            "Mini App вернул неожиданный ответ."
        )

        return False


    except requests.RequestException as e:

        print(
            "Ошибка подключения к Mini App:",
            e
        )

        return False


    except Exception as e:

        print(
            "Ошибка send_feed_to_miniapp:",
            e
        )

        return False


# ============================================================
# ТЕСТ АГРЕГАТОРА
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("STYLEFLOW — ТЕСТ AGGREGATOR")
    print("=" * 60)

    feed = build_feed(
        query="кроссовки",
        limit=10
    )

    print()
    print(
        "Получено:",
        feed["count"]
    )

    if feed["items"]:

        print()
        print("Первые товары:")

        for index, item in enumerate(
            feed["items"],
            start=1
        ):

            print()
            print(
                f"#{index}"
            )

            print(
                "Название:",
                item.get("title")
            )

            print(
                "Цена:",
                item.get("price"),
                item.get("currency")
            )

            print(
                "Источник:",
                item.get("source")
            )

            print(
                "URL:",
                item.get("url")
            )


    # Сохраняем локально
    saved = save_feed(
        feed
    )

    print()
    print(
        "Сохранение:",
        saved
    )


    # Отправляем в Mini App
    if feed["items"]:

        sent = send_feed_to_miniapp(
            feed
        )

        print()
        print(
            "Отправка в Mini App:",
            sent
        )
