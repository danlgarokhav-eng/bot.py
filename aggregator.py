import requests
import json
import os
import time


# ==========================================
# MINI APP
# ==========================================

MINIAPP_URL = (
    "https://miniapp-server-production.up.railway.app/update_feed"
)


# ==========================================
# DUMMYJSON
# ==========================================

API_URL = "https://dummyjson.com/products"


HEADERS = {
    "User-Agent": "TelegramClothingAggregator/1.0"
}


# ==========================================
# ПОЛУЧЕНИЕ ТОВАРОВ
# ==========================================

def search_products(
    query="",
    limit=100
):

    try:

        if query:

            url = (
                "https://dummyjson.com/products/search"
            )

            params = {
                "q": query,
                "limit": limit
            }

        else:

            url = API_URL

            params = {
                "limit": limit
            }


        print(
            f"DummyJSON: запрос '{query}'"
        )


        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=15
        )


        response.raise_for_status()


        data = response.json()


        products = data.get(
            "products",
            []
        )


        print(
            f"DummyJSON: получено товаров: "
            f"{len(products)}"
        )


        return products


    except requests.RequestException as e:

        print(
            f"Ошибка DummyJSON: {e}"
        )

        return []


    except ValueError:

        print(
            "DummyJSON вернул некорректный JSON"
        )

        return []


# ==========================================
# ПРЕОБРАЗОВАНИЕ ТОВАРА
# ==========================================

def convert_product(product):

    price = product.get(
        "price",
        0
    )


    discount = product.get(
        "discountPercentage",
        0
    )


    if discount:

        old_price = round(
            price /
            (
                1 -
                discount / 100
            ),
            2
        )

    else:

        old_price = price


    product_id = product.get(
        "id"
    )


    return {

        "id": product_id,

        "name": product.get(
            "title",
            "Без названия"
        ),

        "brand": product.get(
            "brand",
            "Без бренда"
        ),

        "price": price,

        "old_price": old_price,

        "discount": discount,

        "rating": product.get(
            "rating",
            0
        ),

        "stock": product.get(
            "stock",
            0
        ),

        "category": product.get(
            "category",
            ""
        ),

        "description": product.get(
            "description",
            ""
        ),

        "image": product.get(
            "thumbnail",
            ""
        ),

        "images": product.get(
            "images",
            []
        ),

        "link": (
            "https://dummyjson.com/products/"
            f"{product_id}"
        )
    }


# ==========================================
# СОЗДАНИЕ ФИДА
# ==========================================

def build_feed(
    query=""
):

    products = search_products(
        query=query,
        limit=100
    )


    items = []


    for product in products:

        items.append(
            convert_product(
                product
            )
        )


    feed = {

        "source": "DummyJSON",

        "query": query,

        "count": len(items),

        "updated_at": time.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "items": items

    }


    return feed


# ==========================================
# СОХРАНЕНИЕ ФИДА
# ==========================================

def save_feed(
    feed,
    filename="feed.json"
):

    if not feed.get(
        "items"
    ):

        print(
            "Товары отсутствуют. "
            "Старый feed.json не изменён."
        )

        return False


    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                feed,
                file,
                ensure_ascii=False,
                indent=2
            )


        print(
            f"Фид сохранён: "
            f"{len(feed['items'])} товаров"
        )


        return True


    except Exception as e:

        print(
            f"Ошибка сохранения фида: {e}"
        )

        return False


# ==========================================
# ОТПРАВКА ФИДА В MINI APP
# ==========================================

def send_feed_to_miniapp(
    feed
):

    items = feed.get(
        "items",
        []
    )


    if not items:

        print(
            "Mini App: нечего отправлять."
        )

        return False


    try:

        print(
            f"Mini App: отправляю "
            f"{len(items)} товаров..."
        )


        response = requests.post(

            MINIAPP_URL,

            json=items,

            headers={
                "Content-Type":
                "application/json"
            },

            timeout=20
        )


        response.raise_for_status()


        result = response.json()


        print(
            "Mini App: фид успешно отправлен."
        )


        print(
            f"Ответ сервера: {result}"
        )


        return True


    except requests.RequestException as e:

        print(
            f"Mini App: ошибка отправки: {e}"
        )

        return False


    except ValueError:

        print(
            "Mini App: сервер вернул "
            "некорректный ответ."
        )

        return False


# ==========================================
# ЗАГРУЗКА ФИДА
# ==========================================

def load_feed(
    filename="feed.json"
):

    if not os.path.exists(
        filename
    ):

        return {

            "source": "DummyJSON",

            "query": "",

            "count": 0,

            "items": []

        }


    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )


    except Exception as e:

        print(
            f"Ошибка чтения feed.json: {e}"
        )


        return {

            "source": "DummyJSON",

            "query": "",

            "count": 0,

            "items": []

        }
```
