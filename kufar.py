```python
import requests
import json


KUFAR_API = (
    "https://cre-api.kufar.by/"
    "ads-search/v1/engine/v1/search/rendered-paginated"
)

KUFAR_IMAGE_BASE = (
    "https://rms.kufar.by/v1/gallery/"
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": (
        "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    ),
    "Referer": "https://www.kufar.by/",
}


# ==========================================
# КАРТИНКА
# ==========================================

def make_image_url(path):

    if not path:
        return ""

    path = str(path).strip()

    if (
        path.startswith("http://")
        or path.startswith("https://")
    ):
        return path

    return (
        KUFAR_IMAGE_BASE
        + path.lstrip("/")
    )


# ==========================================
# ЦЕНА
# ==========================================

def extract_price(ad):

    # ==========================================
    # 1. CALCULATOR
    # ==========================================

    calculator = ad.get("calculator")

    if isinstance(calculator, list):

        for item in calculator:

            if not isinstance(item, dict):
                continue

            currency = str(
                item.get("currency", "")
            ).upper()

            if currency != "BYN":
                continue

            raw_price = item.get("price")

            if raw_price in (
                None,
                ""
            ):
                continue

            try:

                price = float(
                    str(raw_price)
                    .replace(" ", "")
                    .replace(",", ".")
                )

                return (
                    round(price / 100, 2),
                    "BYN"
                )

            except (
                ValueError,
                TypeError
            ):

                pass


    # ==========================================
    # 2. PRICE_BYN
    # ==========================================

    price_byn = ad.get("price_byn")

    if price_byn not in (
        None,
        ""
    ):

        try:

            price = float(
                str(price_byn)
                .replace(" ", "")
                .replace(",", ".")
            )

            return (
                round(price / 100, 2),
                "BYN"
            )

        except (
            ValueError,
            TypeError
        ):

            pass


    # ==========================================
    # 3. ОБЫЧНЫЙ PRICE
    # ==========================================

    price = ad.get("price")

    if price not in (
        None,
        ""
    ):

        try:

            price = float(
                str(price)
                .replace(" ", "")
                .replace(",", ".")
            )

            currency = str(
                ad.get("currency")
                or "BYN"
            ).upper()


            # BYN у Kufar хранится в копейках
            if currency == "BYN":

                price = price / 100

                return (
                    round(price, 2),
                    "BYN"
                )


            # В некоторых ответах Kufar
            # currency может быть BYR.
            #
            # Но если мы дошли сюда, значит
            # price_byn и calculator отсутствуют.
            #
            # Поэтому используем ту же
            # минимальную единицу цены.

            if currency == "BYR":

                price = price / 100

                return (
                    round(price, 2),
                    "BYN"
                )


            return (
                round(price, 2),
                currency
            )


        except (
            ValueError,
            TypeError
        ):

            pass


    # ==========================================
    # ЦЕНА НЕ НАЙДЕНА
    # ==========================================

    return 0, "BYN"


# ==========================================
# ФОТО
# ==========================================

def extract_images(ad):

    images = ad.get(
        "images",
        []
    )

    result = []

    if not isinstance(
        images,
        list
    ):
        return result


    for image in images:

        if not isinstance(
            image,
            dict
        ):
            continue

        path = image.get(
            "path"
        )

        if not path:
            continue

        url = make_image_url(
            path
        )

        if (
            url
            and url not in result
        ):

            result.append(
                url
            )


    return result


# ==========================================
# ПОЛУЧЕНИЕ ОБЪЯВЛЕНИЙ
# ==========================================

def get_kufar_ads(
    query="",
    limit=50
):

    params = {
        "size": limit,
        "sort": "lst.d",
    }


    if query:

        params["query"] = query


    print()
    print(
        "=" * 60
    )

    print(
        "KUFAR:",
        query
    )

    print(
        "=" * 60
    )


    try:

        response = requests.get(
            KUFAR_API,
            params=params,
            headers=HEADERS,
            timeout=20
        )


        print(
            "HTTP:",
            response.status_code
        )


        if response.status_code != 200:

            print(
                response.text[:2000]
            )

            return {
                "ads": [],
                "total": 0,
                "cursor": None
            }


        data = response.json()


        ads = data.get(
            "ads",
            []
        )


        print(
            "Получено:",
            len(ads)
        )

        print(
            "Всего:",
            data.get(
                "total",
                "?"
            )
        )


        return {
            "ads": ads,

            "total": data.get(
                "total",
                0
            ),

            "cursor": None,

            "raw": data
        }


    except requests.RequestException as e:

        print(
            "Ошибка Kufar:",
            e
        )

        return {
            "ads": [],
            "total": 0,
            "cursor": None
        }


    except ValueError:

        print(
            "Kufar вернул "
            "некорректный JSON"
        )

        return {
            "ads": [],
            "total": 0,
            "cursor": None
        }


# ==========================================
# KUFAR → STYLEFLOW
# ==========================================

def convert_kufar_ad(ad):

    ad_id = ad.get(
        "ad_id"
    )


    title = (
        ad.get("subject")
        or ad.get("title")
        or "Объявление Kufar"
    )


    link = ad.get(
        "ad_link"
    )


    if (
        not link
        and ad_id
    ):

        link = (
            "https://www.kufar.by/item/"
            f"{ad_id}"
        )


    # Получаем цену
    price, currency = extract_price(
        ad
    )


    # Получаем изображения
    images = extract_images(
        ad
    )


    category = (
        ad.get("category")
        or ""
    )


    product = {

        "id": f"kufar_{ad_id}",

        "source": "kufar",

        "external_id": str(
            ad_id
        ),

        "title": str(
            title
        ).strip(),

        "brand": "",

        "category": str(
            category
        ),

        "price": price,

        "oldPrice": 0,

        "currency": currency,

        "rating": 0,

        "image": (
            images[0]
            if images
            else ""
        ),

        "images": images,

        "url": link,

        "raw": ad
    }


    return product


# ==========================================
# ПОИСК
# ==========================================

def search_kufar(
    query="",
    limit=50
):

    result = get_kufar_ads(
        query=query,
        limit=limit
    )


    products = []


    for ad in result.get(
        "ads",
        []
    ):

        try:

            product = convert_kufar_ad(
                ad
            )


            # Без картинки не берём
            if not product.get(
                "image"
            ):

                continue


            products.append(
                product
            )


        except Exception as e:

            print(
                "Ошибка обработки:",
                e
            )


    return products


# ==========================================
# ТЕСТ
# ==========================================

if __name__ == "__main__":

    print()
    print(
        "=" * 60
    )

    print(
        "STYLEFLOW — ТЕСТ KUFAR"
    )

    print(
        "=" * 60
    )


    products = search_kufar(
        query="кроссовки",
        limit=10
    )


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
            "Название:",
            product["title"]
        )

        print(
            "Цена:",
            product["price"],
            product["currency"]
        )

        print(
            "Фото:",
            len(
                product["images"]
            )
        )

        print(
            "Ссылка:",
            product["url"]
        )
```
