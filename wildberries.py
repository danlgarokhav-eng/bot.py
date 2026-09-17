import os
import requests


# ============================================================
# REEFAPI — WILDBERRIES
# ============================================================

REEF_API_KEY = os.getenv("REEF_API_KEY", "").strip()

REEF_URL = "https://api.reefapi.com/wildberries/v1/search"


def search_wildberries(
    query="кроссовки",
    country="by",
    page=1,
    limit=10,
):
    """
    Поиск товаров Wildberries через ReefAPI.

    query   — поисковый запрос
    country — страна:
              ru = Россия
              by = Беларусь
              kz = Казахстан
              и т.д.
    page    — страница 1-3
    limit   — сколько товаров вернуть из ответа
    """

    if not REEF_API_KEY:
        print("❌ Не найден REEF_API_KEY")
        print("Добавь переменную окружения REEF_API_KEY")
        return []

    headers = {
        "x-api-key": REEF_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "query": query,
        "country": country,
        "page": page,
    }

    try:
        print("=" * 60)
        print("STYLEFLOW — REEFAPI / WILDBERRIES")
        print("=" * 60)

        print(f"🔎 Поиск: {query}")
        print(f"🌍 Страна: {country}")
        print(f"📄 Страница: {page}")
        print()

        response = requests.post(
            REEF_URL,
            headers=headers,
            json=payload,
            timeout=60,
        )

        print(f"HTTP: {response.status_code}")

        if response.status_code != 200:
            print("❌ Ошибка ReefAPI:")
            print(response.text[:3000])
            return []

        data = response.json()

        # ----------------------------------------------------
        # Проверяем ответ ReefAPI
        # ----------------------------------------------------

        if not data.get("ok"):
            print("❌ ReefAPI вернул ошибку:")
            print(data.get("error"))
            return []

        api_data = data.get("data", {})

        results = api_data.get("results", [])

        print(f"✅ Получено товаров: {len(results)}")
        print()

        # ----------------------------------------------------
        # Показываем товары
        # ----------------------------------------------------

        products = []

        for item in results[:limit]:

            product_id = item.get("product_id")

            title = item.get("title", "")
            brand = item.get("brand", "")

            seller = item.get("seller") or {}

            seller_name = seller.get("name", "")
            seller_rating = seller.get("rating")

            price = item.get("price")
            old_price = item.get("was_price")

            currency = item.get("currency", "BYN")

            rating = item.get("rating")
            reviews = item.get("review_count")

            image = item.get("image")
            url = item.get("url")

            stock = item.get("stock_quantity")

            product = {
                "id": str(product_id) if product_id else "",
                "source": "wildberries",
                "external_id": str(product_id) if product_id else "",

                "title": title,
                "name": title,

                "brand": brand,
                "category": "",

                "price": price,
                "oldPrice": old_price,
                "currency": currency,

                "rating": rating,
                "reviews": reviews,
                "stock": stock,

                "image": image,
                "images": [image] if image else [],

                "url": url,
                "link": url,

                "description": "",

                "seller": seller_name,
                "seller_rating": seller_rating,

                "raw": item,
            }

            products.append(product)

            # ------------------------------------------------
            # Вывод в консоль
            # ------------------------------------------------

            print("-" * 60)
            print(f"ID:       {product_id}")
            print(f"Название: {title}")
            print(f"Бренд:    {brand}")
            print(f"Продавец: {seller_name}")

            print(
                f"Цена:     {price} {currency}"
            )

            if old_price:
                print(
                    f"Старая:   {old_price} {currency}"
                )

            print(f"Рейтинг:  {rating}")
            print(f"Отзывы:   {reviews}")
            print(f"Фото:     {image}")
            print(f"Ссылка:   {url}")

        print()
        print("=" * 60)
        print("ТЕСТ ЗАВЕРШЁН")
        print("=" * 60)

        return products

    except requests.exceptions.Timeout:
        print("❌ ReefAPI не ответил за 60 секунд")
        return []

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return []

    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return []


# ============================================================
# ТЕСТ
# ============================================================

if __name__ == "__main__":

    products = search_wildberries(
        query="кроссовки",
        country="by",
        page=1,
        limit=10,
    )

    print()
    print(f"ИТОГО ТОВАРОВ: {len(products)}")
