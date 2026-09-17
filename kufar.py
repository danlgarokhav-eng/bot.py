```python
import requests
import json
import time


# ============================================================
# КУФАР
# ============================================================

KUFAR_API = (
    "https://cre-api.kufar.by/"
    "ads-search/v1/engine/v1/search/rendered-paginated"
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),

    "Accept": (
        "application/json, text/plain, */*"
    ),

    "Accept-Language": (
        "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    ),

    "Referer": "https://www.kufar.by/",
}


# ============================================================
# ЗАПРОС КУФАРА
# ============================================================

def get_kufar_ads(
    query="",
    limit=50,
    cursor=None
):

    params = {
        "size": limit,
        "sort": "lst.d",
    }


    # --------------------------------------------------------
    # ПОИСК
    # --------------------------------------------------------

    if query:

        params["query"] = query


    # --------------------------------------------------------
    # ПАГИНАЦИЯ
    # --------------------------------------------------------

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

        print(
            "URL:",
            response.url
        )


        # ----------------------------------------------------
        # ОШИБКА
        # ----------------------------------------------------

        if response.status_code != 200:

            print()
            print(
                "ОШИБКА КУФАРА:"
            )

            print(
                response.text[:5000]
            )

            return None


        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        data = response.json()


        # Сохраняем ответ для диагностики

        with open(
            "kufar_response.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )


        ads = data.get(
            "ads",
            []
        )


        print()
        print(
            "Куфар: найдено объявлений:",
            len(ads)
        )


        print(
            "Всего:",
            data.get(
                "total",
                "?"
            )
        )


        # ----------------------------------------------------
        # CURSOR
        # ----------------------------------------------------

        pagination = data.get(
            "pagination",
            {}
        )


        next_cursor = None


        if isinstance(
            pagination,
            dict
        ):

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


    except ValueError:

        print(
            "Куфар вернул некорректный JSON."
        )

        return None


# ============================================================
# ИЗВЛЕЧЕНИЕ ПОЛЕЙ
# ============================================================

def get_value(
    ad,
    *keys,
    default=""
):

    for key in keys:

        value = ad.get(
            key
        )

        if value is not None:

            return value


    return default


# ============================================================
# КАРТИНКИ
# ============================================================

def extract_images(ad):

    images = []


    # --------------------------------------------------------
    # Возможные поля
    # --------------------------------------------------------

    for key in (
        "images",
        "image",
        "photos",
        "gallery"
    ):

        value = ad.get(
            key
        )


        if isinstance(
            value,
            list
        ):

            for item in value:

                if isinstance(
                    item,
                    str
                ):

                    images.append(
                        item
                    )

                elif isinstance(
                    item,
                    dict
                ):

                    url = (
                        item.get("url")
                        or item.get("src")
                        or item.get("image")
                    )


                    if url:

                        images.append(
                            url
                        )


    # Убираем дубликаты

    result = []


    for image in images:

        if image not in result:

            result.append(
                image
            )


    return result


# ============================================================
# ЦЕНА
# ============================================================

def extract_price(ad):

    price = ad.get(
        "price"
    )


    if price is not None:

        try:

            return float(
                price
            )

        except:

            pass


    # calculator

    calculator = ad.get(
        "calculator",
        []
    )


    if isinstance(
        calculator,
        list
    ):

        for item in calculator:

            if not isinstance(
                item,
                dict
            ):

                continue


            if item.get(
                "currency"
            ) in (
                "BYN",
                "BYR"
            ):

                try:

                    return float(
                        item.get(
                            "price",
                            0
                        )
                    )

                except:

                    pass


    return 0


# ============================================================
# НОРМАЛИЗАЦИЯ ОБЪЯВЛЕНИЯ
# ============================================================

def convert_kufar_ad(ad):

    ad_id = get_value(
        ad,
        "ad_id",
        "id",
        default=""
    )


    title = get_value(
        ad,
        "subject",
        "title",
        "name",
        default="Объявление Kufar"
    )


    link = get_value(
        ad,
        "ad_link",
        "link",
        "url",
        default=""
    )


    images = extract_images(
        ad
    )


    price = extract_price(
        ad
    )


    currency = get_value(
        ad,
        "currency",
        default="BYN"
    )


    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    product_id = (
        f"kufar_{ad_id}"
        if ad_id
        else f"kufar_{hash(title)}"
    )


    return {

        "id": product_id,

        "source": "kufar",

        "external_id": str(
            ad_id
        ),

        "title": title,

        "brand": "",

        "category": get_value(
            ad,
            "category",
            default=""
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


# ============================================================
# ПОИСК KUFAR
# ============================================================

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


    ads = result.get(
        "ads",
        []
    )


    products = []


    for ad in ads:

        try:

            product = convert_kufar_ad(
                ad
            )


            products.append(
                product
            )

        except Exception as e:

            print(
                "Ошибка обработки объявления:",
                e
            )


    return products


# ============================================================
# ТЕСТ
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("STYLEFLOW — ТЕСТ КУФАРА")
    print("=" * 60)


    query = "кроссовки"


    products = search_kufar(
        query=query,
        limit=5
    )


    print()
    print("=" * 60)
    print("РЕЗУЛЬТАТ")
    print("=" * 60)


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
            "Картинка:",
            product["image"]
        )

        print(
            "Ссылка:",
            product["url"]
        )


    # --------------------------------------------------------
    # Сохраняем результат
    # --------------------------------------------------------

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


    print()
    print(
        "Тест завершён."
    )
```
