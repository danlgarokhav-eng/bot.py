import os
import requests


REEF_API_URL = "https://api.reefapi.com/wildberries/v1/search"

REEF_API_KEY = os.getenv("REEF_API_KEY", "").strip()


def search_wildberries(
    query="кроссовки",
    country="by",
    page=1,
    limit=50,
):
    """
    Поиск товаров Wildberries через ReefAPI.

    Возвращает товары в едином формате StyleFlow.
    """

    if not REEF_API_KEY:
        print("❌ Не найден REEF_API_KEY")
        return []

    headers = {
        "x-api-key": REEF_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "query": query,
        "country": country,
        "page": page,
        "sort": "popular",
        "max_rotations": 12,
    }

    print("=" * 60)
    print("STYLEFLOW — WILDBERRIES / REEFAPI")
    print("=" * 60)
    print(f"🔎 Запрос: {query}")
    print(f"🌍 Страна: {country}")
    print(f"📄 Страница: {page}")
    print("🔄 Максимум попыток ReefAPI: 12")
    print("📡 Отправляем запрос...")

    try:
        response = requests.post(
            REEF_API_URL,
            headers=headers,
            json=payload,
            timeout=120,
        )

    except requests.exceptions.Timeout:
        print("❌ ReefAPI не ответил за 120 секунд")
        return []

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса ReefAPI: {e}")
        return []

    print(f"HTTP: {response.status_code}")

    if response.status_code != 200:
        print("❌ ReefAPI вернул HTTP-ошибку:")
        print(response.text[:3000])
        return []

    try:
        data = response.json()

    except ValueError:
        print("❌ ReefAPI вернул некорректный JSON")
        print(response.text[:3000])
        return []

    if not data.get("ok"):
        error = data.get("error", {})

        print("❌ ReefAPI сообщил об ошибке:")
        print(error)

        if isinstance(error, dict):
            print(f"Код: {error.get('code')}")
            print(f"Сообщение: {error.get('message')}")
            print(f"Повторить позже: {error.get('retryable')}")

        return []

    api_data = data.get("data", {})

    if not isinstance(api_data, dict):
        print("❌ Некорректное поле data")
        return []

    results = api_data.get("results", [])

    if not isinstance(results, list):
        print("❌ Некорректное поле results")
        return []

    print(f"✅ Получено от Wildberries: {len(results)} товаров")

    products = []

    for item in results[:limit]:

        if not isinstance(item, dict):
            continue

        product_id = item.get("product_id")

        if not product_id:
            continue

        title = item.get("title") or "Товар Wildberries"

        seller = item.get("seller") or {}

        if not isinstance(seller, dict):
            seller = {}

        image = item.get("image") or ""

        images = []

        if image:
            images.append(image)

        product = {
            # ==========================================
            # ОСНОВНЫЕ ПОЛЯ STYLEFLOW
            # ==========================================

            "id": f"wb_{product_id}",

            "source": "wildberries",

            "external_id": str(product_id),

            # ==========================================
            # НАЗВАНИЕ
            # ==========================================

            "title": title,

            "name": title,

            # ==========================================
            # ТОВАР
            # ==========================================

            "brand": item.get("brand") or "",

            "category": "",

            "category_id": item.get("category_id"),

            # ==========================================
            # ЦЕНА
            # ==========================================

            "price": item.get("price"),

            "oldPrice": item.get("was_price"),

            "currency": item.get("currency") or "BYN",

            # ==========================================
            # РЕЙТИНГ
            # ==========================================

            "rating": item.get("rating"),

            "reviews": item.get("review_count", 0),

            # ==========================================
            # НАЛИЧИЕ
            # ==========================================

            "stock": item.get("stock_quantity", 0),

            "available": item.get("available", False),

            # ==========================================
            # ФОТО
            # ==========================================

            "image": image,

            "images": images,

            # ==========================================
            # ССЫЛКА
            # ==========================================

            "url": item.get("url") or "",

            "link": item.get("url") or "",

            # ==========================================
            # ОПИСАНИЕ
            # ==========================================

            "description": "",

            # ==========================================
            # ПРОДАВЕЦ
            # ==========================================

            "seller": seller.get("name") or "",

            "seller_rating": seller.get("rating"),

            "seller_id": seller.get("id"),

            # ==========================================
            # СКИДКА
            # ==========================================

            "discount_percent": item.get("discount_percent"),

            # ==========================================
            # ДОСТАВКА
            # ==========================================

            "delivery_hours": item.get("delivery_hours"),

            # ==========================================
            # ЛОГИСТИКА
            # ==========================================

            "price_before_logistics": item.get(
                "price_before_logistics"
            ),

            "logistics_fee": item.get(
                "logistics_fee"
            ),

            # ==========================================
            # РАЗМЕРЫ / ЦВЕТА
            # ==========================================

            "size_count": item.get("size_count", 0),

            "colours": item.get("colours", []),

            # ==========================================
            # ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ
            # ==========================================

            "root_id": item.get("root_id"),

            "image_count": item.get("image_count", 0),

            "is_new": item.get("is_new", False),

            "price_source": item.get("price_source"),

            # ==========================================
            # RAW — ОРИГИНАЛЬНЫЙ ОБЪЕКТ REEFAPI
            # ==========================================

            "raw": item,
        }

        products.append(product)

    print(f"📦 Подготовлено для StyleFlow: {len(products)} товаров")

    return products


def test_wildberries():
    """
    Тест Wildberries через ReefAPI.
    """

    products = search_wildberries(
        query="кроссовки",
        country="by",
        page=1,
        limit=10,
    )

    print()

    print("=" * 60)
    print("РЕЗУЛЬТАТ ТЕСТА")
    print("=" * 60)

    if not products:
        print("❌ Товары не получены")
        print("=" * 60)
        return

    for index, product in enumerate(products, start=1):

        print()
        print(f"ТОВАР #{index}")
        print("-" * 60)

        print(f"ID: {product['external_id']}")

        print(f"Название: {product['title']}")

        print(f"Бренд: {product['brand']}")

        print(
            f"Цена: "
            f"{product['price']} "
            f"{product['currency']}"
        )

        print(
            f"Старая цена: "
            f"{product['oldPrice']}"
        )

        print(
            f"Скидка: "
            f"{product['discount_percent']}%"
        )

        print(
            f"Рейтинг: "
            f"{product['rating']}"
        )

        print(
            f"Отзывы: "
            f"{product['reviews']}"
        )

        print(
            f"Остаток: "
            f"{product['stock']}"
        )

        print(
            f"В наличии: "
            f"{product['available']}"
        )

        print(
            f"Продавец: "
            f"{product['seller']}"
        )

        print(
            f"Рейтинг продавца: "
            f"{product['seller_rating']}"
        )

        print(
            f"Доставка: "
            f"{product['delivery_hours']} ч."
        )

        print(
            f"Изображение: "
            f"{product['image']}"
        )

        print(
            f"Ссылка: "
            f"{product['url']}"
        )

    print()

    print("=" * 60)
    print("✅ ТЕСТ ЗАВЕРШЁН")
    print("=" * 60)


if __name__ == "__main__":
    test_wildberries()
