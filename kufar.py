import requests
import json
import re
import time
from urllib.parse import urljoin


# ============================================================
# КУФАР API
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
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.kufar.by/",
}


# ============================================================
# НАСТРОЙКИ
# ============================================================

DEFAULT_QUERY = "кроссовки"
DEFAULT_LIMIT = 10


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def make_absolute_url(value):
    """
    Делает URL абсолютным.
    """

    if not isinstance(value, str):
        return ""

    value = value.strip()

    if not value:
        return ""

    if value.startswith("//"):
        return "https:" + value

    if value.startswith("/"):
        return urljoin(
            "https://www.kufar.by",
            value
        )

    return value


def looks_like_image_url(url):
    """
    Проверяет, похож ли URL на изображение.
    """

    if not isinstance(url, str):
        return False

    url = url.strip()

    if not url:
        return False

    lower = url.lower()

    # Только http/https

    if not (
        lower.startswith("http://")
        or lower.startswith("https://")
    ):
        return False

    # Исключаем страницы Kufar

    if "kufar.by/item/" in lower:
        return False

    # Явные расширения изображений

    image_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".avif",
    )

    if any(
        ext in lower
        for ext in image_extensions
    ):
        return True

    # CDN / image URL часто не содержит расширение

    image_markers = (
        "image",
        "images",
        "photo",
        "photos",
        "picture",
        "pictures",
        "media",
        "cdn",
        "img",
        "kufar",
    )

    return any(
        marker in lower
        for marker in image_markers
    )


def extract_urls_recursive(
    value,
    result=None,
    depth=0
):
    """
    Рекурсивно ищет URL внутри любого JSON-объекта.

    Это специально сделано для Kufar,
    потому что структура медиа может меняться.
    """

    if result is None:
        result = []

    # Защита от слишком глубокой структуры

    if depth > 15:
        return result

    # STRING

    if isinstance(value, str):

        # Ищем полноценные URL

        urls = re.findall(
            r'https?://[^\s"\'<>]+',
            value
        )

        for url in urls:

            # Убираем хвостовые символы JSON

            url = url.rstrip(
                ".,;:)]}"
            )

            if looks_like_image_url(
                url
            ):

                if url not in result:

                    result.append(
                        url
                    )

        return result

    # DICT

    if isinstance(
        value,
        dict
    ):

        for key, item in value.items():

            # В первую очередь интересуют
            # поля, связанные с изображениями

            key_lower = str(
                key
            ).lower()

            priority = any(
                word in key_lower
                for word in (
                    "image",
                    "photo",
                    "picture",
                    "media",
                    "gallery",
                    "thumbnail",
                    "preview",
                    "picture_url",
                    "image_url",
                    "photo_url",
                )
            )

            if priority:

                extract_urls_recursive(
                    item,
                    result,
                    depth + 1
                )

        # Затем всё остальное

        for item in value.values():

            extract_urls_recursive(
                item,
                result,
                depth + 1
            )

        return result

    # LIST / TUPLE

    if isinstance(
        value,
        (list, tuple)
    ):

        for item in value:

            extract_urls_recursive(
                item,
                result,
                depth + 1
            )

        return result

    return result


# ============================================================
# ЦЕНА
# ============================================================

def normalize_price(
    price,
    currency="BYN"
):
    """
    Приводит цену Kufar к нормальному виду.

    Старый BYR:
        5000 BYR -> 0.50 BYN

    BYN:
        50 BYN -> 50 BYN
    """

    if price is None:
        return 0

    try:

        # Строки вида "5 000"

        if isinstance(
            price,
            str
        ):

            cleaned = (
                price
                .replace(" ", "")
                .replace(",", ".")
            )

            price = float(
                cleaned
            )

        else:

            price = float(
                price
            )

    except (
        ValueError,
        TypeError
    ):

        return 0

    currency = str(
        currency or ""
    ).upper()

    # BYR -> BYN после деноминации

    if currency == "BYR":

        price = price / 10000

        currency = "BYN"

    # Иногда Kufar отдаёт старый код,
    # но данные уже фактически BYN.

    if currency == "BYN":

        return round(
            price,
            2
        )

    return round(
        price,
        2
    )


# ============================================================
# ЦЕНА ИЗ ОБЪЯВЛЕНИЯ
# ============================================================

def extract_price(
    ad
):
    """
    Извлекает цену из объявления.
    """

    currency = (
        ad.get(
            "currency"
        )
        or "BYN"
    )

    # --------------------------------------------------------
    # Основное поле price
    # --------------------------------------------------------

    if ad.get(
        "price"
    ) is not None:

        price = normalize_price(
            ad.get("price"),
            currency
        )

        return price, (
            "BYN"
            if str(currency).upper() == "BYR"
            else str(currency).upper()
        )


    # --------------------------------------------------------
    # Calculator
    # --------------------------------------------------------

    calculator = ad.get(
        "calculator"
    )


    if isinstance(
        calculator,
        list
    ):

        # Сначала ищем BYN/BYR

        for item in calculator:

            if not isinstance(
                item,
                dict
            ):
                continue

            item_currency = (
                item.get(
                    "currency"
                )
                or ""
            ).upper()

            if item_currency in (
                "BYN",
                "BYR"
            ):

                price = normalize_price(
                    item.get(
                        "price"
                    ),
                    item_currency
                )

                return price, "BYN"


    return 0, (
        "BYN"
        if str(currency).upper()
        in ("BYN", "BYR")
        else str(currency).upper()
    )


# ============================================================
# ТЕКСТОВОЕ ПОЛЕ
# ============================================================

def first_value(
    data,
    *keys,
    default=""
):
    """
    Возвращает первое найденное значение.
    """

    if not isinstance(
        data,
        dict
    ):
        return default

    for key in keys:

        value = data.get(
            key
        )

        if value is not None:

            return value

    return default


# ============================================================
# НАЗВАНИЕ
# ============================================================

def extract_title(
    ad
):

    title = first_value(
        ad,
        "subject",
        "title",
        "name",
        "name_short",
        default=""
    )

    if title:

        return str(
            title
        ).strip()

    return "Объявление Kufar"


# ============================================================
# ССЫЛКА
# ============================================================

def extract_link(
    ad
):

    link = first_value(
        ad,
        "ad_link",
        "link",
        "url",
        default=""
    )

    if link:

        return make_absolute_url(
            str(link)
        )

    ad_id = first_value(
        ad,
        "ad_id",
        "id",
        default=""
    )

    if ad_id:

        return (
            "https://www.kufar.by/item/"
            f"{ad_id}"
        )

    return ""


# ============================================================
# ИЗОБРАЖЕНИЯ
# ============================================================

def extract_images(
    ad
):

    images = []


    # --------------------------------------------------------
    # 1. Рекурсивный поиск по всему объявлению
    # --------------------------------------------------------

    found = extract_urls_recursive(
        ad
    )


    for url in found:

        url = make_absolute_url(
            url
        )

        if (
            url
            and url not in images
        ):

            images.append(
                url
            )


    # --------------------------------------------------------
    # 2. Дополнительный поиск по известным полям
    # --------------------------------------------------------

    possible_fields = (
        "images",
        "photos",
        "gallery",
        "media",
        "image",
        "thumbnail",
        "preview",
        "image_url",
        "photo_url",
    )


    for field in possible_fields:

        value = ad.get(
            field
        )


        if isinstance(
            value,
            str
        ):

            value = make_absolute_url(
                value
            )

            if (
                looks_like_image_url(
                    value
                )
                and value not in images
            ):

                images.append(
                    value
                )


        elif isinstance(
            value,
            list
        ):

            for item in value:

                if isinstance(
                    item,
                    str
                ):

                    url = make_absolute_url(
                        item
                    )

                    if (
                        looks_like_image_url(
                            url
                        )
                        and url not in images
                    ):

                        images.append(
                            url
                        )

                elif isinstance(
                    item,
                    dict
                ):

                    nested = (
                        extract_urls_recursive(
                            item
                        )
                    )

                    for url in nested:

                        if url not in images:

                            images.append(
                                url
                            )


    # --------------------------------------------------------
    # Ограничиваем количество фотографий
    # --------------------------------------------------------

    return images[:20]


# ============================================================
# ПРЕОБРАЗОВАНИЕ ОБЪЯВЛЕНИЯ
# ============================================================

def convert_kufar_ad(
    ad
):

    ad_id = first_value(
        ad,
        "ad_id",
        "id",
        default=""
    )


    title = extract_title(
        ad
    )


    link = extract_link(
        ad
    )


    images = extract_images(
        ad
    )


    price, currency = extract_price(
        ad
    )


    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    if ad_id:

        product_id = (
            f"kufar_{ad_id}"
        )

    else:

        product_id = (
            "kufar_"
            + str(
                abs(
                    hash(
                        title
                    )
                )
            )
        )


    # --------------------------------------------------------
    # Категория
    # --------------------------------------------------------

    category = first_value(
        ad,
        "category",
        default=""
    )


    # Иногда category приходит
    # числом.

    if category is None:

        category = ""


    # --------------------------------------------------------
    # Результат
    # --------------------------------------------------------

    product = {

        "id": product_id,

        "source": "kufar",

        "external_id": str(
            ad_id
        ),

        "title": title,

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
    # Поисковый запрос
    # --------------------------------------------------------

    if query:

        params["query"] = query


    # --------------------------------------------------------
    # Cursor
    # --------------------------------------------------------

    if cursor:

        params["cursor"] = cursor


    print()
    print(
        "=" * 60
    )

    print(
        "КУФАР — ЗАПРОС"
    )

    print(
        "=" * 60
    )

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

        print(
            "HTTP:",
            response.status_code
        )

        print(
            "URL:",
            response.url
        )


        # ----------------------------------------------------
        # Ошибка
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


        # ----------------------------------------------------
        # Сохраняем полный ответ
        # ----------------------------------------------------

        try:

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

        except Exception as e:

            print(
                "Не удалось сохранить raw JSON:",
                e
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
        # Pagination
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

                pagination.get(
                    "cursor"
                )

                or pagination.get(
                    "next_cursor"
                )

                or pagination.get(
                    "next"
                )

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

    print(
        "=" * 60
    )

    print(
        "STYLEFLOW — ТЕСТ КУФАРА"
    )

    print(
        "=" * 60
    )


    query = DEFAULT_QUERY


    products = search_kufar(

        query=query,

        limit=DEFAULT_LIMIT

    )


    print()

    print(
        "=" * 60
    )

    print(
        "РЕЗУЛЬТАТ"
    )

    print(
        "=" * 60
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
            "ID:",
            product.get(
                "id"
            )
        )

        print(
            "Название:",
            product.get(
                "title"
            )
        )

        print(
            "Цена:",
            product.get(
                "price"
            ),
            product.get(
                "currency"
            )
        )

        print(
            "Количество фото:",
            len(
                product.get(
                    "images",
                    []
                )
            )
        )

        print(
            "Картинка:",
            product.get(
                "image"
            )
        )

        print(
            "Ссылка:",
            product.get(
                "url"
            )
        )


        # Показываем первые 3 фото

        for photo_index, photo in enumerate(

            product.get(
                "images",
                []
            )[:3],

            start=1

        ):

            print(
                f"Фото #{photo_index}:",
                photo
            )


    # --------------------------------------------------------
    # Сохраняем нормализованные товары
    # --------------------------------------------------------

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
            "Ошибка сохранения товаров:",
            e
        )


    print()

    print(
        "Тест завершён."
    )
