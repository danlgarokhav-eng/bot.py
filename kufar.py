import requests
import json
import time


# ============================================================
# КУФАР API
# ============================================================

KUFAR_API = (
    "https://cre-api.kufar.by/"
    "ads-search/v1/engine/v1/search/rendered-paginated"
)


# ============================================================
# НАСТРОЙКИ
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def first_value(data, *keys, default=None):
    """
    Возвращает первое найденное значение
    из списка возможных ключей.
    """

    if not isinstance(data, dict):
        return default

    for key in keys:

        value = data.get(key)

        if value is not None:
            return value

    return default


def make_absolute_url(url):
    """
    Превращает относительную ссылку
    в полноценную ссылку Куфара.
    """

    if not url:
        return ""

    if url.startswith("http://"):
        return url

    if url.startswith("https://"):
        return url

    if url.startswith("//"):
        return "https:" + url

    if url.startswith("/"):
        return "https://www.kufar.by" + url

    return url


# ============================================================
# ИЗОБРАЖЕНИЯ
# ============================================================

def extract_images(ad):
    """
    Пытается найти изображения объявления
    в нескольких возможных местах JSON.
    """

    found = []

    def add_image(value):

        if not value:
            return

        if isinstance(value, str):

            url = make_absolute_url(value)

            if url and url not in found:
                found.append(url)

            return

        if isinstance(value, dict):

            url = first_value(
                value,
                "url",
                "src",
                "link",
                "original",
                "large",
                "medium",
                "small",
            )

            if url:

                url = make_absolute_url(url)

                if url and url not in found:
                    found.append(url)

    # --------------------------------------------------------
    # Прямые поля
    # --------------------------------------------------------

    for key in (
        "images",
        "photos",
        "gallery",
        "media",
    ):

        value = ad.get(key)

        if isinstance(value, list):

            for item in value:
                add_image(item)

        elif isinstance(value, dict):

            for nested_key in (
                "images",
                "photos",
                "gallery",
                "items",
            ):

                nested = value.get(nested_key)

                if isinstance(nested, list):

                    for item in nested:
                        add_image(item)

    # --------------------------------------------------------
    # Иногда картинки находятся в content
    # --------------------------------------------------------

    content = ad.get("content")

    if isinstance(content, dict):

        for key in (
            "images",
            "photos",
            "gallery",
            "media",
        ):

            value = content.get(key)

            if isinstance(value, list):

                for item in value:
                    add_image(item)

    # --------------------------------------------------------
    # Иногда данные лежат в ad_params
    # --------------------------------------------------------

    ad_params = ad.get("ad_params")

    if isinstance(ad_params, dict):

        for key in (
            "images",
            "photos",
            "gallery",
        ):

            value = ad_params.get(key)

            if isinstance(value, list):

                for item in value:
                    add_image(item)

    return found


# ============================================================
# ЦЕНА
# ============================================================

def extract_price(ad):
    """
    Пытается получить цену объявления.
    """

    price = first_value(
        ad,
        "price",
        "price_byn",
        "price_value",
        default=0,
    )

    # Если цена словарь
    if isinstance(price, dict):

        price = first_value(
            price,
            "value",
            "amount",
            "price",
            default=0,
        )

    try:
        return float(price)

    except (TypeError, ValueError):
        return 0


def extract_currency(ad):
    """
    Определяет валюту.
    """

    currency = first_value(
        ad,
        "currency",
        "currency_code",
        "price_currency",
        default="BYN",
    )

    if isinstance(currency, dict):

        currency = first_value(
            currency,
            "code",
            "name",
            "currency",
            default="BYN",
        )

    if not currency:
        return "BYN"

    return str(currency).upper()


# ============================================================
# ССЫЛКА НА ОБЪЯВЛЕНИЕ
# ============================================================

def extract_link(ad, ad_id):
    """
    Получает прямую ссылку на объявление.
    """

    link = first_value(
        ad,
        "url",
        "link",
        "href",
        "ad_url",
        default="",
    )

    if link:
        return make_absolute_url(link)

    if ad_id:

        return (
            "https://www.kufar.by/"
            f"item/{ad_id}"
        )

    return ""


# ============================================================
# ПОЛУЧЕНИЕ ОБЪЯВЛЕНИЙ
# ============================================================

def get_kufar_ads(
    query="",
    limit=50,
    page=1,
):
    """
    Получает объявления Куфара.

    query:
        Поисковый запрос.

    limit:
        Количество объявлений.

    page:
        Страница результатов.
    """

    limit = max(
        1,
        min(int(limit), 100)
    )

    page = max(
        1,
        int(page)
    )

    params = {
        "size": limit,
        "page": page,
    }

    if query:

        params["query"] = query

    print()
    print("=" * 60)
    print("КУФАР")
    print("=" * 60)
    print(
        f"Запрос: {query or 'все объявления'}"
    )
    print(
        f"Количество: {limit}"
    )
    print(
        f"Страница: {page}"
    )
    print("=" * 60)

    try:

        response = requests.get(
            KUFAR_API,
            params=params,
            headers=HEADERS,
            timeout=30,
        )

        print(
            "HTTP:",
            response.status_code
        )

        response.raise_for_status()

    except requests.Timeout:

        print(
            "Куфар: превышено время ожидания."
        )

        return []

    except requests.RequestException as e:

        print(
            "Куфар: ошибка запроса:"
        )

        print(e)

        return []

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    try:

        data = response.json()

    except ValueError:

        print(
            "Куфар: сервер вернул "
            "не JSON."
        )

        print(
            response.text[:1000]
        )

        return []

    # --------------------------------------------------------
    # Сохраняем сырой ответ для диагностики
    # --------------------------------------------------------

    try:

        with open(
            "kufar_debug.json",
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print(
            "Сырой ответ сохранён: "
            "kufar_debug.json"
        )

    except Exception as e:

        print(
            "Не удалось сохранить "
            "kufar_debug.json:",
            e
        )

    # --------------------------------------------------------
    # Ищем массив объявлений
    # --------------------------------------------------------

    ads = []

    if isinstance(data, list):

        ads = data

    elif isinstance(data, dict):

        # Самые вероятные варианты
        for key in (
            "ads",
            "items",
            "results",
            "data",
            "listings",
            "advertisements",
        ):

            value = data.get(key)

            if isinstance(value, list):

                ads = value
                break

            if isinstance(value, dict):

                for nested_key in (
                    "ads",
                    "items",
                    "results",
                    "listings",
                ):

                    nested = value.get(
                        nested_key
                    )

                    if isinstance(
                        nested,
                        list
                    ):

                        ads = nested
                        break

                if ads:
                    break

    print(
        f"Куфар: найдено объявлений "
        f"в ответе: {len(ads)}"
    )

    return ads


# ============================================================
# ПРЕОБРАЗОВАНИЕ ОБЪЯВЛЕНИЯ
# ============================================================

def convert_kufar_ad(ad):
    """
    Преобразует объявление Куфара
    в формат StyleFlow.
    """

    if not isinstance(ad, dict):
        return None

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    ad_id = first_value(
        ad,
        "ad_id",
        "id",
        "list_id",
        "advert_id",
    )

    if not ad_id:
        return None

    # --------------------------------------------------------
    # Название
    # --------------------------------------------------------

    title = first_value(
        ad,
        "subject",
        "title",
        "name",
        "name_ru",
        default="Без названия",
    )

    # --------------------------------------------------------
    # Описание
    # --------------------------------------------------------

    description = first_value(
        ad,
        "body",
        "description",
        "text",
        default="",
    )

    # --------------------------------------------------------
    # Цена
    # --------------------------------------------------------

    price = extract_price(ad)

    currency = extract_currency(ad)

    # --------------------------------------------------------
    # Изображения
    # --------------------------------------------------------

    images = extract_images(ad)

    image = (
        images[0]
        if images
        else ""
    )

    # --------------------------------------------------------
    # Ссылка
    # --------------------------------------------------------

    link = extract_link(
        ad,
        ad_id,
    )

    # --------------------------------------------------------
    # Категория
    # --------------------------------------------------------

    category = first_value(
        ad,
        "category",
        "category_name",
        "category_title",
        default="",
    )

    if isinstance(
        category,
        dict
    ):

        category = first_value(
            category,
            "name",
            "title",
            "name_ru",
            default="",
        )

    # --------------------------------------------------------
    # Бренд
    # --------------------------------------------------------

    brand = first_value(
        ad,
        "brand",
        "brand_name",
        default="",
    )

    if isinstance(
        brand,
        dict
    ):

        brand = first_value(
            brand,
            "name",
            "title",
            default="",
        )

    if not brand:
        brand = "Куфар"

    # --------------------------------------------------------
    # Итоговый товар
    # --------------------------------------------------------

    product = {

        "id": f"kufar_{ad_id}",

        "source": "kufar",

        "external_id": str(
            ad_id
        ),

        "name": str(
            title
        ),

        "brand": str(
            brand
        ),

        "price": price,

        "old_price": 0,

        "discount": 0,

        "currency": currency,

        "rating": 0,

        "stock": 1,

        "category": str(
            category
        ),

        "description": str(
            description
        ),

        "image": image,

        "images": images,

        "link": link,

        "raw": ad,
    }

    return product


# ============================================================
# ПОИСК ТОВАРОВ
# ============================================================

def search_kufar(
    query="",
    limit=50,
):
    """
    Главная функция для aggregator.py.

    Возвращает готовые товары StyleFlow.
    """

    ads = get_kufar_ads(
        query=query,
        limit=limit,
        page=1,
    )

    products = []

    for ad in ads:

        try:

            product = convert_kufar_ad(
                ad
            )

            if product:

                products.append(
                    product
                )

        except Exception as e:

            print(
                "Куфар: ошибка "
                "обработки объявления:"
            )

            print(e)

    print()
    print(
        f"Куфар: подготовлено "
        f"{len(products)} товаров"
    )

    return products


# ============================================================
# ПОЛУЧЕНИЕ НЕСКОЛЬКИХ СТРАНИЦ
# ============================================================

def search_kufar_pages(
    query="",
    pages=3,
    per_page=50,
):
    """
    Получает несколько страниц Куфара.

    Например:

        pages=3
        per_page=50

    даст до 150 объявлений.
    """

    all_products = []

    seen_ids = set()

    pages = max(
        1,
        min(int(pages), 10)
    )

    per_page = max(
        1,
        min(int(per_page), 100)
    )

    for page in range(
        1,
        pages + 1
    ):

        ads = get_kufar_ads(
            query=query,
            limit=per_page,
            page=page,
        )

        if not ads:
            break

        for ad in ads:

            try:

                product = convert_kufar_ad(
                    ad
                )

                if not product:
                    continue

                product_id = product.get(
                    "id"
                )

                if product_id in seen_ids:
                    continue

                seen_ids.add(
                    product_id
                )

                all_products.append(
                    product
                )

            except Exception as e:

                print(
                    "Ошибка обработки "
                    "товара:",
                    e
                )

        # Небольшая пауза между страницами
        time.sleep(0.5)

    print()
    print("=" * 60)
    print(
        f"Куфар: всего товаров: "
        f"{len(all_products)}"
    )
    print("=" * 60)

    return all_products


# ============================================================
# СОХРАНЕНИЕ ТЕСТОВОГО РЕЗУЛЬТАТА
# ============================================================

def save_debug_products(
    products,
    filename="kufar_products.json",
):
    """
    Сохраняет полученные товары,
    чтобы можно было посмотреть JSON.
    """

    try:

        with open(
            filename,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                products,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print(
            f"Товары сохранены: "
            f"{filename}"
        )

        return True

    except Exception as e:

        print(
            "Ошибка сохранения:",
            e
        )

        return False


# ============================================================
# ТЕСТОВЫЙ ЗАПУСК
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "STYLEFLOW — ТЕСТ КУФАРА"
    )
    print()

    products = search_kufar(
        query="кроссовки",
        limit=5,
    )

    print()
    print(
        "========== ТОВАРЫ =========="
    )
    print()

    for index, product in enumerate(
        products,
        start=1,
    ):

        print(
            f"#{index}"
        )

        print(
            "ID:",
            product.get(
                "external_id"
            )
        )

        print(
            "Название:",
            product.get(
                "name"
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
            "Бренд:",
            product.get(
                "brand"
            )
        )

        print(
            "Категория:",
            product.get(
                "category"
            )
        )

        print(
            "Картинка:",
            product.get(
                "image"
            )
        )

        print(
            "Все картинки:",
            len(
                product.get(
                    "images",
                    []
                )
            )
        )

        print(
            "Ссылка:",
            product.get(
                "link"
            )
        )

        print(
            "-" * 50
        )

    save_debug_products(
        products
    )

    print()
    print(
        "Тест завершён."
    )
