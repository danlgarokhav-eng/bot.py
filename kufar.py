import requests
import json

KUFAR_API = (
    "https://cre-api.kufar.by/"
    "ads-search/v1/engine/v1/search/rendered-paginated"
)

KUFAR_IMAGE_BASE = "https://rms.kufar.by/v1/gallery/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.kufar.by/",
}

DEFAULT_QUERY = "кроссовки"
DEFAULT_LIMIT = 10


def make_image_url(path):
    """Превращает Kufar path в полноценный URL изображения."""

    if not path:
        return ""

    path = str(path).strip()

    if path.startswith("http://") or path.startswith("https://"):
        return path

    return KUFAR_IMAGE_BASE + path.lstrip("/")


def normalize_price(price, currency="BYN"):
    if price is None:
        return 0

    try:
        price = float(price)
    except (ValueError, TypeError):
        return 0

    currency = str(currency or "").upper()

    # Старый белорусский рубль
    if currency == "BYR":
        price = price / 10000
        currency = "BYN"

    return round(price, 2)


def extract_price(ad):
    """
    Берём цену из price_byn,
    затем из price,
    затем из calculator.
    """

    price_byn = ad.get("price_byn")

    if price_byn not in (None, ""):
        try:
            return round(
                float(
                    str(price_byn)
                    .replace(" ", "")
                    .replace(",", ".")
                ),
                2
            ), "BYN"
        except (ValueError, TypeError):
            pass

    price = ad.get("price")

    if price not in (None, ""):
        currency = ad.get("currency") or "BYN"

        return normalize_price(
            price,
            currency
        ), (
            "BYN"
            if str(currency).upper() == "BYR"
            else str(currency).upper()
        )

    calculator = ad.get("calculator")

    if isinstance(calculator, list):

        for item in calculator:

            if not isinstance(item, dict):
                continue

            calculator_price = item.get("price")
            calculator_currency = item.get("currency") or "BYN"

            if calculator_price not in (None, ""):

                return normalize_price(
                    calculator_price,
                    calculator_currency
                ), (
                    "BYN"
                    if str(calculator_currency).upper() == "BYR"
                    else str(calculator_currency).upper()
                )

    return 0, "BYN"


def extract_images(ad):
    """Получает все фотографии объявления."""

    images = ad.get("images", [])

    result = []

    if not isinstance(images, list):
        return result

    for image in images:

        if not isinstance(image, dict):
            continue

        path = image.get("path")

        if not path:
            continue

        url = make_image_url(path)

        if url not in result:
            result.append(url)

    return result


def convert_kufar_ad(ad):

    ad_id = ad.get("ad_id")

    title = (
        ad.get("subject")
        or ad.get("title")
        or "Объявление Kufar"
    )

    link = ad.get("ad_link")

    if not link and ad_id:
        link = f"https://www.kufar.by/item/{ad_id}"

    price, currency = extract_price(ad)

    images = extract_images(ad)

    category = ad.get("category") or ""

    return {
        "id": f"kufar_{ad_id}",

        "source": "kufar",

        "external_id": str(ad_id),

        "title": str(title).strip(),

        "brand": "",

        "category": str(category),

        "price": price,

        "oldPrice": 0,

        "currency": currency,

        "rating": 0,

        "image": images[0] if images else "",

        "images": images,

        "url": link,

        "raw": ad
    }


def get_kufar_ads(
    query="",
    limit=50,
    cursor=None
):

    params = {
        "size": limit,
        "sort": "lst.d",
    }

    if query:
        params["query"] = query

    if cursor:
        params["cursor"] = cursor

    print()
    print("=" * 60)
    print("КУФАР — ЗАПРОС")
    print("=" * 60)

    print(
        json.dumps(
            params,
            ensure_ascii=False,
            indent=2
        )
    )

    try:

        response = requests.get(
            KUFAR_API,
            params=params,
            headers=HEADERS,
            timeout=20
        )

        print()
        print("HTTP:", response.status_code)
        print("URL:", response.url)

        if response.status_code != 200:

            print()
            print("ОШИБКА KUFAR:")
            print(response.text[:5000])

            return None

        data = response.json()

        ads = data.get("ads", [])

        print()
        print(
            "Куфар: найдено объявлений:",
            len(ads)
        )

        print(
            "Всего:",
            data.get("total", "?")
        )

        pagination = data.get(
            "pagination",
            {}
        )

        next_cursor = None

        if isinstance(pagination, dict):

            next_cursor = (
                pagination.get("cursor")
                or pagination.get("next_cursor")
                or pagination.get("next")
            )

        print(
            "Следующий cursor:",
            next_cursor
        )

        return {
            "ads": ads,

            "total": data.get(
                "total",
                0
            ),

            "cursor": next_cursor,

            "raw": data
        }

    except requests.RequestException as e:

        print(
            "Ошибка HTTP:",
            e
        )

        return None

    except ValueError as e:

        print(
            "Ошибка JSON:",
            e
        )

        return None


def search_kufar(
    query="",
    limit=50
):

    result = get_kufar_ads(
        query=query,
        limit=limit
    )

    if not result:
        return []

    products = []

    for ad in result.get(
        "ads",
        []
    ):

        try:

            product = convert_kufar_ad(
                ad
            )

            products.append(
                product
            )

        except Exception as e:

            print(
                "Ошибка обработки:",
                e
            )

    return products


if __name__ == "__main__":

    print()
    print("=" * 60)
    print("STYLEFLOW — ТЕСТ KUFAR")
    print("=" * 60)

    products = search_kufar(
        query=DEFAULT_QUERY,
        limit=DEFAULT_LIMIT
    )

    print()
    print("=" * 60)
    print("РЕЗУЛЬТАТ")
    print("=" * 60)

    print()
    print(
        "Получено товаров:",
        len(products)
    )

    for index, product in enumerate(
        products,
        start=1
    ):

        print()
        print(
            f"ТОВАР #{index}"
        )

        print(
            "ID:",
            product["id"]
        )

        print(
            "Название:",
            product["title"]
        )

        print(
            "Цена:",
            product["price"],
            product["currency"]
        )

        print(
            "Количество фото:",
            len(
                product["images"]
            )
        )

        print(
            "Картинка:",
            product["image"]
        )

        for photo_index, photo in enumerate(
            product["images"][:3],
            start=1
        ):

            print(
                f"Фото #{photo_index}:",
                photo
            )

        print(
            "Ссылка:",
            product["url"]
        )

    try:

        with open(
            "kufar_products.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                products,
                file,
                ensure_ascii=False,
                indent=2
            )

        print()
        print(
            "Товары сохранены:"
            " kufar_products.json"
        )

    except Exception as e:

        print(
            "Ошибка сохранения:",
            e
        )

    print()
    print("Тест завершён.")
