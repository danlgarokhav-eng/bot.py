import json
import os
import requests

from kufar import search_kufar


# ============================================================
# НАСТРОЙКИ
# ============================================================

FEED_FILE = "feed.json"

MINIAPP_URL = os.getenv(
    "MINIAPP_URL",
    "https://miniapp-server-production.up.railway.app"
).strip()

DEFAULT_LIMIT = 50

DEFAULT_QUERY = os.getenv(
    "DEFAULT_QUERY",
    "кроссовки"
).strip()


# ============================================================
# BUILD FEED
# ============================================================

def build_feed(query=None, limit=DEFAULT_LIMIT):

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
        print("=" * 60)
        print("ИСТОЧНИК: KUFAR")
        print("=" * 60)

        kufar_products = search_kufar(
            query=query,
            limit=limit
        )

        if not isinstance(
            kufar_products,
            list
        ):
            kufar_products = []

        print(
            "Kufar получено:",
            len(kufar_products)
        )

        products.extend(
            kufar_products
        )

    except Exception as e:

        print(
            "❌ Ошибка Kufar:",
            e
        )


    # ========================================================
    # БУДУЩИЕ ИСТОЧНИКИ
    # ========================================================
    #
    # Здесь позже подключим:
    #
    # Wildberries
    # Ozon
    # AliExpress
    # Steam
    # билеты
    # услуги
    #
    # Каждый источник будет добавлять
    # свои товары в products.
    #
    # Например:
    #
    # from wildberries import search_wildberries
    #
    # wb_products = search_wildberries(
    #     query=query,
    #     limit=limit
    # )
    #
    # products.extend(wb_products)
    #
    # ========================================================


    # ========================================================
    # ОБЩИЙ ЛИМИТ
    # ========================================================

    products = products[:limit]


    print()
    print("=" * 60)
    print("ВСЕ ИСТОЧНИКИ")
    print("=" * 60)

    print(
        "Всего товаров:",
        len(products)
    )


    # ========================================================
    # НОРМАЛИЗАЦИЯ
    # ========================================================

    normalized_products = []

    for product in products:

        if not isinstance(
            product,
            dict
        ):
            continue


        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = (
            product.get("title")
            or product.get("name")
            or "Без названия"
        )


        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        price = product.get(
            "price",
            0
        )

        try:

            price = float(price)

            if price.is_integer():
                price = int(price)

        except (
            ValueError,
            TypeError
        ):

            price = 0


        # ----------------------------------------------------
        # CURRENCY
        # ----------------------------------------------------

        currency = product.get(
            "currency",
            "BYN"
        )

        currency = str(
            currency
        ).upper()


        # ----------------------------------------------------
        # URL
        # ----------------------------------------------------

        url = (
            product.get("url")
            or product.get("link")
            or ""
        )


        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        image = product.get(
            "image",
            ""
        )


        # ----------------------------------------------------
        # SOURCE
        # ----------------------------------------------------

        source = product.get(
            "source",
            ""
        )

        source = str(
            source
        ).lower()


        # ----------------------------------------------------
        # EXTERNAL ID
        # ----------------------------------------------------

        external_id = product.get(
            "external_id",
            ""
        )


        # ----------------------------------------------------
        # PRODUCT
        # ----------------------------------------------------

        normalized_product = {

            "id": product.get(
                "id",
                ""
            ),

            "source": source,

            "external_id": external_id,

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

            "raw": product.get(
                "raw",
                {}
            )
        }


        normalized_products.append(
            normalized_product
        )


    # ========================================================
    # ПРОВЕРКА ПОСЛЕ НОРМАЛИЗАЦИИ
    # ========================================================

    print()
    print("=" * 60)
    print("ПРОВЕРКА ПОСЛЕ НОРМАЛИЗАЦИИ")
    print("=" * 60)

    for item in normalized_products[:10]:

        print(
            "TITLE:",
            item.get("title")
        )

        print(
            "PRICE:",
            item.get("price")
        )

        print(
            "CURRENCY:",
            item.get("currency")
        )

        print(
            "SOURCE:",
            item.get("source")
        )

        print("-" * 40)


    # ========================================================
    # FEED
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
    print("FEED СОЗДАН")
    print("=" * 60)

    print(
        "Количество:",
        feed["count"]
    )

    return feed


# ============================================================
# SAVE FEED
# ============================================================

def save_feed(feed):

    try:

        if not isinstance(
            feed,
            dict
        ):

            print(
                "save_feed: неправильный формат"
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
            "Feed сохранён:",
            FEED_FILE
        )

        return True


    except Exception as e:

        print(
            "Ошибка сохранения:",
            e
        )

        return False


# ============================================================
# LOAD FEED
# ============================================================

def load_feed():

    if not os.path.exists(
        FEED_FILE
    ):

        print(
            "feed.json не найден"
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


    except Exception as e:

        print(
            "Ошибка загрузки feed:",
            e
        )

        return {
            "count": 0,
            "query": "",
            "items": []
        }


# ============================================================
# SEND TO MINI APP
# ============================================================

def send_feed_to_miniapp(feed):

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


        # ====================================================
        # ПРОВЕРКА ПЕРЕД ОТПРАВКОЙ
        # ====================================================

        print()
        print("=" * 60)
        print("ПРЯМО ПЕРЕД ОТПРАВКОЙ В MINI APP")
        print("=" * 60)

        for item in items[:10]:

            print(
                "TITLE:",
                item.get("title")
            )

            print(
                "PRICE:",
                item.get("price")
            )

            print(
                "CURRENCY:",
                item.get("currency")
            )

            print(
                "SOURCE:",
                item.get("source")
            )

            print("-" * 40)


        # ====================================================
        # URL
        # ====================================================

        url = (
            MINIAPP_URL.rstrip("/")
            + "/update_feed"
        )


        print()
        print(
            "POST:",
            url
        )

        print(
            "Товаров:",
            len(items)
        )


        # ====================================================
        # ОТПРАВКА
        # ====================================================

        response = requests.post(
            url,
            json=items,
            timeout=30
        )


        print(
            "HTTP:",
            response.status_code
        )


        print(
            "Ответ сервера:",
            response.text[:2000]
        )


        if response.status_code != 200:

            print(
                "❌ ОШИБКА MINI APP"
            )

            return False


        try:

            result = response.json()

        except ValueError:

            result = {}


        if result.get(
            "status"
        ) == "ok":

            print(
                "Feed успешно отправлен "
                "в Mini App."
            )

            return True


        print(
            "Mini App вернул "
            "неожиданный ответ."
        )

        return False


    except requests.RequestException as e:

        print(
            "Ошибка подключения "
            "к Mini App:",
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
# TEST
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
        "ИТОГО:",
        feed["count"]
    )


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    save_feed(
        feed
    )


    # --------------------------------------------------------
    # SEND
    # --------------------------------------------------------

    if feed["items"]:

        send_feed_to_miniapp(
            feed
        )
