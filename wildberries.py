import requests


WB_SEARCH_URL = (
    "https://search.wb.ru/exactmatch/ru/common/v4/search"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9",
}


def get_wb_image(nm_id):
    """
    Строит URL основной картинки Wildberries.

    nm_id — артикул товара WB.
    """

    try:
        nm_id = int(nm_id)
    except (TypeError, ValueError):
        return ""

    vol = nm_id // 100000
    part = nm_id // 1000

    # Основной вариант CDN.
    # Для части старых/новых карточек конкретный basket
    # может отличаться, поэтому при необходимости позже
    # сделаем более надёжное определение CDN.
    basket = (vol // 100) + 1

    return (
        f"https://basket-{basket:02d}.wbbasket.ru/"
        f"vol{vol}/part{part}/{nm_id}/images/big/1.webp"
    )


def extract_price(product):
    """
    Получает цену товара.

    Wildberries обычно отдаёт:
    salePriceU = цена в копейках.

    Например:
    350000 -> 3500 RUB
    """

    sale_price = product.get("salePriceU")

    if sale_price is not None:
        try:
            return float(sale_price) / 100
        except (TypeError, ValueError):
            pass

    # Запасной вариант
    price_u = product.get("priceU")

    if price_u is not None:
        try:
            return float(price_u) / 100
        except (TypeError, ValueError):
            pass

    return 0.0


def extract_old_price(product):
    """
    Получает старую цену, если она есть.
    """

    price_u = product.get("priceU")

    if price_u is None:
        return 0.0

    try:
        return float(price_u) / 100
    except (TypeError, ValueError):
        return 0.0


def convert_wb_product(product):
    """
    Приводит карточку Wildberries
    к единому формату StyleFlow.
    """

    nm_id = product.get("id")

    title = (
        product.get("name")
        or product.get("title")
        or "Товар Wildberries"
    )

    brand = product.get("brand", "")

    price = extract_price(product)
    old_price = extract_old_price(product)

    rating = product.get("reviewRating")

    try:
        rating = float(rating) if rating is not None else None
    except (TypeError, ValueError):
        rating = None

    reviews = product.get("feedbacks", 0)

    try:
        reviews = int(reviews)
    except (TypeError, ValueError):
        reviews = 0

    image = get_wb_image(nm_id)

    url = ""

    if nm_id:
        url = (
            f"https://www.wildberries.ru/catalog/"
            f"{nm_id}/detail.aspx"
        )

    return {
        "id": f"wb_{nm_id}",
        "source": "wildberries",
        "external_id": str(nm_id) if nm_id else "",

        "title": title,
        "name": title,

        "brand": brand,
        "category": "",

        "price": price,
        "oldPrice": old_price,
        "currency": "RUB",

        "rating": rating,
        "stock": None,
        "reviews": reviews,

        "image": image,
        "images": [image] if image else [],

        "url": url,
        "link": url,

        "description": "",

        # Оставляем исходную карточку.
        "raw": product,
    }


def search_wildberries(query, limit=50, page=1):
    """
    Ищет товары на Wildberries.

    query:
        Например "кроссовки"

    limit:
        Сколько товаров вернуть.

    page:
        Страница WB.
    """

    params = {
        "query": query,
        "resultset": "catalog",

        # Беларусь/Россия и другие направления
        # позже можно вынести в настройки.
        "dest": "-1257786",

        "curr": "rub",
        "spp": "30",
        "appType": "1",
        "lang": "ru",

        "page": page,
    }

    print()
    print("=" * 60)
    print("WILDBERRIES — ПОИСК")
    print("=" * 60)
    print(f"Запрос: {query}")
    print(f"Страница: {page}")
    print(f"Лимит: {limit}")
    print()

    try:
        response = requests.get(
            WB_SEARCH_URL,
            params=params,
            headers=HEADERS,
            timeout=20,
        )

        print(f"HTTP: {response.status_code}")

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as e:
        print(f"❌ Ошибка запроса WB: {e}")
        return []

    except ValueError as e:
        print(f"❌ WB вернул не JSON: {e}")
        print(response.text[:500])
        return []

    products = data.get("products", [])

    if not isinstance(products, list):
        print("❌ Поле products имеет неправильный формат.")
        return []

    print(f"Найдено WB: {len(products)}")

    result = []

    for product in products[:limit]:

        try:
            normalized = convert_wb_product(product)
            result.append(normalized)

        except Exception as e:
            print(
                f"⚠️ Ошибка обработки товара "
                f"{product.get('id')}: {e}"
            )

    print(f"Обработано: {len(result)}")

    return result


if __name__ == "__main__":

    print("=" * 60)
    print("STYLEFLOW — ТЕСТ WILDBERRIES")
    print("=" * 60)

    products = search_wildberries(
        query="кроссовки",
        limit=10,
    )

    print()
    print("=" * 60)
    print("РЕЗУЛЬТАТ")
    print("=" * 60)

    for index, product in enumerate(products, start=1):

        print()
        print(f"#{index}")
        print(f"ID:       {product['external_id']}")
        print(f"Название: {product['title']}")
        print(f"Бренд:    {product['brand']}")
        print(f"Цена:     {product['price']} {product['currency']}")
        print(f"Старая:   {product['oldPrice']} {product['currency']}")
        print(f"Рейтинг:  {product['rating']}")
        print(f"Отзывы:   {product['reviews']}")
        print(f"Фото:     {product['image']}")
        print(f"Ссылка:   {product['url']}")
