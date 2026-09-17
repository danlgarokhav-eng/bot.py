import json
import os
import random

import requests

from kufar import search_kufar
from wildberries import search_wildberries


# ============================================================
# НАСТРОЙКИ
# ============================================================

FEED_FILE = "feed.json"

MINIAPP_URL = os.getenv(
    "MINIAPP_URL",
    "https://miniapp-server-production.up.railway.app"
).strip()

DEFAULT_QUERY = os.getenv(
    "DEFAULT_QUERY",
    "товары"
).strip()

DEFAULT_LIMIT = int(
    os.getenv("DEFAULT_LIMIT", "100")
)


# ============================================================
# НОРМАЛИЗАЦИЯ ТОВАРА
# ============================================================

def normalize_product(product, source):
    """
    Приводит товар к единому формату StyleFlow.
    """

    if not isinstance(product, dict):
        return None

    external_id = (
        product.get("external_id")
        or product.get("id")
        or ""
    )

    title = (
        product.get("title")
        or product.get("name")
        or "Товар"
    )

    price = product.get("price")

    old_price = (
        product.get("oldPrice")
        if product.get("oldPrice") is not None
        else product.get("old_price")
    )

    image = (
        product.get("image")
        or ""
    )

    images = product.get("images")

    if not isinstance(images, list):
        images = []

    if not images and image:
        images = [image]

    url = (
        product.get("url")
        or product.get("link")
        or ""
    )

    normalized = {
        # ====================================================
        # ОСНОВНЫЕ
        # ====================================================

        "id": f"{source}_{external_id}",

        "source": source,

        "external_id": str(external_id),

        # ====================================================
        # НАЗВАНИЕ
        # ====================================================

        "title": title,

        "name": title,

        # ====================================================
        # ТОВАР
        # ====================================================

        "brand": product.get("brand") or "",

        "category": product.get("category") or "",

        # ====================================================
        # ЦЕНА
        # ====================================================

        "price": price,

        "oldPrice": old_price,

        "currency": (
            product.get("currency")
            or "BYN"
        ),

        # ====================================================
        # РЕЙТИНГ
        # ====================================================

        "rating": product.get("rating"),

        "reviews": (
            product.get("reviews")
            if product.get("reviews") is not None
            else product.get("review_count", 0)
        ),

        # ====================================================
        # НАЛИЧИЕ
        # ====================================================

        "stock": (
            product.get("stock")
            if product.get("stock") is not None
            else product.get("stock_quantity", 0)
        ),

        "available": product.get(
            "available",
            True
        ),

        # ====================================================
        # ФОТО
        # ====================================================

        "image": image,

        "images": images,

        # ====================================================
        # ССЫЛКА
        # ====================================================

        "url": url,

        "link": url,

        # ====================================================
        # ОПИСАНИЕ
        # ====================================================

        "description": (
            product.get("description")
            or ""
        ),

        # ====================================================
        # ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ
        # ====================================================

        "seller": product.get(
            "seller",
            ""
        ),

        "seller_rating": product.get(
            "seller_rating"
        ),

        "discount_percent": product.get(
            "discount_percent"
        ),

        "delivery_hours": product.get(
            "delivery_hours"
        ),

        "colours": product.get(
            "colours",
            []
        ),

        "size_count": product.get(
            "size_count",
            0
        ),

        # ====================================================
        # ОРИГИНАЛ
        # ====================================================

        "raw": product,
    }

    return normalized


# ============================================================
# УДАЛЕНИЕ ДУБЛЕЙ
# ============================================================

def remove_duplicates(products):
    """
    Удаляет дубли товаров.

    Главный ключ:
        source + external_id

    Если такого ключа нет, используется id.
    """

    unique = []

    seen = set()

    for product in products:

        if not isinstance(product, dict):
            continue

        source = product.get(
            "source",
            ""
        )

        external_id = product.get(
            "external_id"
        )

        if external_id:
            key = (
                str(source),
                str(external_id)
            )
        else:
            key = (
                str(source),
                str(product.get("id", ""))
            )

        if key in seen:
            continue

        seen.add(key)
        unique.append(product)

    return unique


# ============================================================
# СОЗДАНИЕ ЛЕНТЫ
# ============================================================

def build_feed(
    query=None,
    limit=DEFAULT_LIMIT
):
    """
    Собирает общую ленту:

        Kufar
        +
        Wildberries

    и возвращает единый feed.
    """

    if not query:
        query = DEFAULT_QUERY

    print()
    print("=" * 70)
    print("STYLEFLOW — СОЗДАНИЕ ОБЩЕЙ ЛЕНТЫ")
    print("=" * 70)

    print(f"🔎 Запрос: {query}")
    print(f"📦 Максимум товаров: {limit}")

    all_products = []

    # ========================================================
    # KUFAR
    # ========================================================

    print()
    print("🟢 KUFAR")
    print("-" * 70)

    try:
        kufar_products = search_kufar(
            query=query,
            limit=limit
        )

        if not isinstance(kufar_products, list):
            kufar_products = []

        print(
            f"Получено Kufar: "
            f"{len(kufar_products)}"
        )

        for product in kufar_products:

            normalized = normalize_product(
                product,
                "kufar"
            )

            if normalized:
                all_products.append(
                    normalized
                )

    except Exception as e:

        print(
            f"❌ Ошибка Kufar: {e}"
        )

    # ========================================================
    # WILDBERRIES
    # ========================================================

    print()
    print("🟣 WILDBERRIES")
    print("-" * 70)

    try:
        wb_products = search_wildberries(
            query=query,
            country="by",
            page=1,
            limit=limit
        )

        if not isinstance(wb_products, list):
            wb_products = []

        print(
            f"Получено Wildberries: "
            f"{len(wb_products)}"
        )

        for product in wb_products:

            normalized = normalize_product(
                product,
                "wildberries"
            )

            if normalized:
                all_products.append(
                    normalized
                )

    except Exception as e:

        print(
            f"❌ Ошибка Wildberries: {e}"
        )

    # ========================================================
    # ДУБЛИ
    # ========================================================

    before_duplicates = len(
        all_products
    )

    all_products = remove_duplicates(
        all_products
    )

    after_duplicates = len(
        all_products
    )

    removed = (
        before_duplicates
        - after_duplicates
    )

    print()
    print(
        f"🧹 Удалено дублей: {removed}"
    )

    # ========================================================
    # ПЕРЕМЕШИВАНИЕ
    # ========================================================

    random.shuffle(
        all_products
    )

    # ========================================================
    # ОГРАНИЧЕНИЕ
    # ========================================================

    if limit and limit > 0:

        all_products = all_products[
            :limit
        ]

    # ========================================================
    # FEED
    # ========================================================

    feed = {
        "count": len(all_products),

        "query": query,

        "items": all_products
    }

    print()
    print("=" * 70)
    print("ИТОГ")
    print("=" * 70)

    print(
        f"🛍 Всего товаров: "
        f"{len(all_products)}"
    )

    kufar_count = sum(
        1
        for item in all_products
        if item.get("source") == "kufar"
    )

    wb_count = sum(
        1
        for item in all_products
        if item.get("source") == "wildberries"
    )

    print(
        f"🟢 Kufar: "
        f"{kufar_count}"
    )

    print(
        f"🟣 Wildberries: "
        f"{wb_count}"
    )

    print("=" * 70)

    return feed


# ============================================================
# СОХРАНЕНИЕ FEED.JSON
# ============================================================

def save_feed(feed):
    """
    Сохраняет feed.json.
    """

    try:

        with open(
            FEED_FILE,
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
            f"💾 Feed сохранён: "
            f"{FEED_FILE}"
        )

        return True

    except Exception as e:

        print(
            f"❌ Ошибка сохранения feed: "
            f"{e}"
        )

        return False


# ============================================================
# ЗАГРУЗКА FEED.JSON
# ============================================================

def load_feed():
    """
    Загружает существующий feed.json.
    """

    if not os.path.exists(
        FEED_FILE
    ):
        print(
            "⚠️ feed.json ещё не существует"
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
        ) as file:

            feed = json.load(file)

        if not isinstance(
            feed,
            dict
        ):
            return {
                "count": 0,
                "query": "",
                "items": []
            }

        items = feed.get(
            "items",
            []
        )

        if not isinstance(
            items,
            list
        ):
            items = []

        feed["items"] = items

        feed["count"] = len(
            items
        )

        return feed

    except Exception as e:

        print(
            f"❌ Ошибка загрузки feed: "
            f"{e}"
        )

        return {
            "count": 0,
            "query": "",
            "items": []
        }


# ============================================================
# ОТПРАВКА В MINI APP
# ============================================================

def send_feed_to_miniapp(feed):
    """
    Отправляет список товаров
    на miniapp-server.
    """

    if not isinstance(
        feed,
        dict
    ):
        print(
            "❌ Некорректный feed"
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
            "❌ feed.items должен быть списком"
        )

        return False

    url = (
        MINIAPP_URL.rstrip("/")
        + "/update_feed"
    )

    print()
    print(
        "📡 Отправляем ленту в Mini App..."
    )

    print(
        f"URL: {url}"
    )

    print(
        f"Товаров: {len(items)}"
    )

    try:

        response = requests.post(
            url,
            json=items,
            timeout=60
        )

    except requests.exceptions.Timeout:

        print(
            "❌ Mini App server "
            "не ответил за 60 секунд"
        )

        return False

    except requests.exceptions.RequestException as e:

        print(
            f"❌ Ошибка отправки "
            f"в Mini App: {e}"
        )

        return False

    print(
        f"HTTP: {response.status_code}"
    )

    if response.status_code != 200:

        print(
            "❌ Mini App server "
            "вернул ошибку:"
        )

        print(
            response.text[:3000]
        )

        return False

    try:

        result = response.json()

    except ValueError:

        print(
            "⚠️ Сервер ответил, "
            "но вернул не JSON"
        )

        print(
            response.text[:1000]
        )

        return True

    print(
        f"✅ Mini App получил "
        f"{result.get('count', len(items))} товаров"
    )

    return True


# ============================================================
# ПОЛНОЕ ОБНОВЛЕНИЕ
# ============================================================

def refresh_feed(
    query=None,
    limit=DEFAULT_LIMIT
):
    """
    Полный цикл:

        источники
        ↓
        объединение
        ↓
        удаление дублей
        ↓
        перемешивание
        ↓
        feed.json
        ↓
        Mini App
    """

    feed = build_feed(
        query=query,
        limit=limit
    )

    if not feed.get("items"):

        print(
            "❌ Лента пустая. "
            "Сохранять и отправлять нечего."
        )

        return feed

    saved = save_feed(
        feed
    )

    if saved:

        sent = send_feed_to_miniapp(
            feed
        )

        if sent:
            print(
                "✅ Лента полностью "
                "обновлена."
            )
        else:
            print(
                "⚠️ Feed сохранён локально, "
                "но не отправлен в Mini App."
            )

    return feed


# ============================================================
# ТЕСТ
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("STYLEFLOW — ТЕСТ АГРЕГАТОРА")
    print("=" * 70)

    feed = refresh_feed(
        query="товары",
        limit=100
    )

    print()
    print("=" * 70)
    print("ПЕРВЫЕ ТОВАРЫ")
    print("=" * 70)

    for index, item in enumerate(
        feed.get("items", [])[:20],
        start=1
    ):

        print()
        print(
            f"#{index} "
            f"[{item.get('source')}]"
        )

        print(
            f"Название: "
            f"{item.get('title')}"
        )

        print(
            f"Цена: "
            f"{item.get('price')} "
            f"{item.get('currency')}"
        )

        print(
            f"Бренд: "
            f"{item.get('brand')}"
        )

        print(
            f"Рейтинг: "
            f"{item.get('rating')}"
        )

        print(
            f"Ссылка: "
            f"{item.get('url')}"
        )

    print()
    print("=" * 70)
    print(
        f"✅ Готово. "
        f"Всего: {feed.get('count', 0)}"
    )
    print("=" * 70)
