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

    Возвращает список товаров в едином формате StyleFlow.
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
    }

    print("=" * 60)
    print("STYLEFLOW — WILDBERRIES / REEFAPI")
    print("=" * 60)
    print(f"🔎 Запрос: {query}")
    print(f"🌍 Страна: {country}")
    print(f"📄 Страница: {page}")
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
        print("❌ ReefAPI вернул ошибку:")
        print(response.text[:3000])
        return []

    try:
        data = response.json()
    except ValueError:
        print("❌ ReefAPI вернул не JSON")
        print(response.text[:3000])
        return []

    if not data.get("ok"):
        print("❌ ReefAPI сообщил об ошибке:")
        print(data.get("error", data))
        return []

    results = data.get("data", {}).get("results", [])

    if not isinstance(results, list):
        print("❌ Некорректный формат results")
        return []

    print(f"✅ Получено от Wildberries: {len(results)} товаров")

    products = []

    for item in results[:limit]:

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
            # Основные поля StyleFlow
            "id": f"wb_{product_id}",
            "source": "wildberries",
            "external_id": str(product_id),

            # Название
            "title": title,
            "name": title,

            # Информация о товаре
            "brand": item.get("brand") or "",
            "category": "",
            "category_id": item.get("category_id"),

            # Цена
            "price": item.get("price"),
            "oldPrice": item.get("was_price"),
            "currency": item.get("currency") or "BYN",

            # Рейтинг
            "rating": item.get("rating"),
            "reviews": item.get("review_count", 0),

            # Остаток
            "stock": item.get("stock_quantity", 0),
            "available": item.get("available", False),

            # Изображения
            "image": image,
            "images": images,

            # Ссылка
            "url": item.get("url") or "",
            "link": item.get("url") or "",

            # Описание
            "description": "",

            # Дополнительная информация
            "seller": seller.get("name") or "",
            "seller_rating": seller.get("rating"),

            "discount_percent": item.get("discount_percent"),

            "delivery_hours": item.get("delivery_hours"),

            "price_before_logistics": item.get(
                "price_before_logistics"
            ),

            "logistics_fee": item.get(
                "logistics_fee"
            ),

            "size_count": item.get("size_count", 0),

            "colours": item.get("colours", []),

            # Служебное
            "raw": item,
        }

        products.append(product)

    print(f"📦 Подготовлено для StyleFlow: {len(products)} товаров")

    return products


def test_wildberries():
    """
    Локальный тест Wildberries.
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
        return

    for index, product in enumerate(products, start=1):

        print()
        print(f"#{index}")
        print(f"ID: {product['external_id']}")
        print(f"Название: {product['title']}")
        print(f"Бренд: {product['brand']}")
        print(
            f"Цена: {product['price']} "
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
            f"Продавец: "
            f"{product['seller']}"
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
