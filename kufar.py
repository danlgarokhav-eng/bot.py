import requests
import re


KUFAR_API = (
    "https://cre-api.kufar.by/"
    "ads-search/v1/engine/v1/search/rendered-paginated"
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def get_kufar_products(
    query="",
    limit=50,
):
    """
    Получение объявлений Куфара.

    query:
        поисковый запрос.
        Например:
        "кроссовки"
        "куртка"
        "iphone"

    limit:
        количество товаров.
    """

    params = {
        "size": min(limit, 100),
        "sort": "lst.d",
    }

    if query:
        params["query"] = query

    try:

        print(
            f"Куфар: получаю товары "
            f"по запросу '{query}'..."
        )

        response = requests.get(
            KUFAR_API,
            params=params,
            headers=HEADERS,
            timeout=20,
        )

        print(
            f"Куфар HTTP: {response.status_code}"
        )

        response.raise_for_status()

        data = response.json()

        ads = data.get("ads", [])

        print(
            f"Куфар: получено объявлений: "
            f"{len(ads)}"
        )

        return ads

    except requests.RequestException as e:

        print(
            f"Куфар: ошибка запроса: {e}"
        )

        return []

    except ValueError:

        print(
            "Куфар: сервер вернул "
            "некорректный JSON"
        )

        return []


def get_value(
    data,
    *keys,
    default=None,
):
    """
    Безопасно ищет значение
    в словаре по нескольким возможным ключам.
    """

    if not isinstance(data, dict):
        return default

    for key in keys:

        value = data.get(key)

        if value is not None:
            return value

    return default


def extract_image(ad):
    """
    Пытаемся достать первое изображение.
    Формат ответа Куфара может меняться,
    поэтому проверяем несколько вариантов.
    """

    images = []

    media = ad.get("media")

    if isinstance(media, dict):

        for key in (
            "images",
            "photos",
            "gallery",
        ):

            value = media.get(key)

            if isinstance(value, list):
                images.extend(value)

    for key in (
        "images",
        "photos",
        "gallery",
    ):

        value = ad.get(key)

        if isinstance(value, list):
            images.extend(value)

    for image in images:

        if isinstance(image, str):
            return image

        if isinstance(image, dict):

            url = (
                image.get("url")
                or image.get("src")
                or image.get("original")
            )

            if url:
                return url

    return ""


def extract_images(ad):
    """
    Получение всех доступных изображений.
    """

    result = []

    media = ad.get("media")

    candidates = []

    if isinstance(media, dict):

        for key in (
            "images",
            "photos",
            "gallery",
        ):

            value = media.get(key)

            if isinstance(value, list):
                candidates.extend(value)

    for key in (
        "images",
        "photos",
        "gallery",
    ):

        value = ad.get(key)

        if isinstance(value, list):
            candidates.extend(value)

    for image in candidates:

        if isinstance(image, str):

            result.append(image)

        elif isinstance(image, dict):

            url = (
                image.get("url")
                or image.get("src")
                or image.get("original")
            )

            if url:
                result.append(url)

    # убираем дубли
    unique = []

    for image in result:

        if image not in unique:
            unique.append(image)

    return unique


def convert_kufar_product(ad):
    """
    Превращает объявление Куфара
    в формат StyleFlow.
    """

    ad_id = (
        ad.get("ad_id")
        or ad.get("id")
        or ad.get("list_id")
    )

    title = (
        ad.get("subject")
        or ad.get("title")
        or ad.get("name")
        or "Без названия"
    )

    description = (
        ad.get("body")
        or ad.get("description")
        or ""
    )

    price = (
        ad.get("price")
        or 0
    )

    currency = (
        ad.get("currency")
        or "BYN"
    )

    images = extract_images(ad)

    image = (
        extract_image(ad)
    )

    # Если Куфар не дал готовую ссылку,
    # собираем стандартную.
    link = (
        ad.get("url")
        or ad.get("link")
        or ""
    )

    if not link and ad_id:

        link = (
            f"https://www.kufar.by/"
            f"item/{ad_id}"
        )

    return {

        "id": f"kufar_{ad_id}",

        "source": "kufar",

        "external_id": str(
            ad_id
        ) if ad_id else "",

        "name": title,

        "brand": (
            ad.get("brand")
            or "Куфар"
        ),

        "price": price,

        "old_price": 0,

        "discount": 0,

        "currency": currency,

        "rating": (
            ad.get("rating")
            or 0
        ),

        "stock": 1,

        "category": (
            ad.get("category")
            or ""
        ),

        "description": description,

        "image": image,

        "images": images,

        "link": link,

        "raw": ad,
    }


def search_kufar(
    query="",
    limit=50,
):

    ads = get_kufar_products(
        query=query,
        limit=limit,
    )

    products = []

    for ad in ads:

        try:

            product = (
                convert_kufar_product(ad)
            )

            if product.get("external_id"):

                products.append(product)

        except Exception as e:

            print(
                f"Куфар: ошибка "
                f"обработки объявления: {e}"
            )

    print(
        f"Куфар: подготовлено "
        f"{len(products)} товаров"
    )

    return products
