import requests
import json
import os
import time


# ==========================================
# MINI APP
# ==========================================

MINIAPP_URL = (
    "https://miniapp-server-production.up.railway.app/update_feed"
)


# ==========================================
# KUFAR
# ==========================================

KUFAR_API = (
    "https://cre-api.kufar.by/"
    "ads-search/v1/engine/v1/search/rendered-paginated"
)

KUFAR_IMAGE_BASE = (
    "https://rms.kufar.by/v1/gallery/"
)

KUFAR_HEADERS = {
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
# НАСТРОЙКИ ЛЕНТЫ
# ==========================================

# Несколько поисковых запросов,
# чтобы лента была разнообразной.

KUFAR_QUERIES = [
    "кроссовки",
    "кеды",
    "футболка",
    "джинсы",
    "куртка",
    "худи",
    "штаны",
    "сумка",
]


# Сколько товаров максимум получать
# с каждого запроса.

ITEMS_PER_QUERY = 15


# Общий лимит товаров в ленте.

MAX_FEED_ITEMS = 100


# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================

def make_image_url(path):
    """
    Превращает Kufar path
    в полноценный URL картинки.
    """

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


def normalize_price(
    price,
    currency="BYN"
):
    """
    Нормализация цены.

    Пока считаем price_byn
    непосредственно значением BYN.
    """

    if price in (None, ""):
        return 0

    try:

        price = float(
            str(price)
            .replace(" ", "")
            .replace(",", ".")
        )

    except (
        ValueError,
        TypeError
    ):

        return 0

    currency = str(
        currency or ""
    ).upper()

    if currency == "BYR":

        price = price / 10000

        currency = "BYN"

    return round(
        price,
        2
    )


def extract_price(ad):
    """
    Получает цену объявления.

    Приоритет:

    1. price_byn
    2. price
    3. calculator
    """

    # ------------------------------
    # price_byn
    # ------------------------------

    price_byn = ad.get(
        "price_byn"
    )

    if price_byn not in (
        None,
        ""
    ):

        price = normalize_price(
            price_byn,
            "BYN"
        )

        if price > 0:

            return price, "BYN"


    # ------------------------------
    # price
    # ------------------------------

    price = ad.get(
        "price"
    )

    if price not in (
        None,
        ""
    ):

        currency = (
            ad.get("currency")
            or "BYN"
        )

        normalized = normalize_price(
            price,
            currency
        )

        result_currency = (
            "BYN"
            if str(currency).upper()
            == "BYR"
            else str(currency).upper()
        )

        return (
            normalized,
            result_currency
        )


    # ------------------------------
    # calculator
    # ------------------------------

    calculator = ad.get(
        "calculator"
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

            calculator_price = item.get(
                "price"
            )

            if calculator_price in (
                None,
                ""
            ):
                continue

            calculator_currency = (
                item.get("currency")
                or "BYN"
            )

            normalized = normalize_price(
                calculator_price,
                calculator_currency
            )

            result_currency = (
                "BYN"
                if str(
                    calculator_currency
                ).upper() == "BYR"
                else str(
                    calculator_currency
                ).upper()
            )

            return (
                normalized,
                result_currency
            )


    return 0, "BYN"


def extract_images(ad):
    """
    Получает все изображения объявления.
    """

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
# ПОЛУЧЕНИЕ KUFAR
# ==========================================

def get_kufar_ads(
    query,
    limit=15
):

    params = {
        "size": limit,
        "sort": "lst.d",
        "query": query,
    }


    print()
    print(
        "=" * 60
    )

    print(
        f"KUFAR → '{query}'"
    )

    print(
        "=" * 60
    )


    try:

        response = requests.get(

            KUFAR_API,

            params=params,

            headers=KUFAR_HEADERS,

            timeout=20
        )


        print(
            "HTTP:",
            response.status_code
        )


        if response.status_code != 200:

            print(
                "Ошибка Kufar:"
            )

            print(
                response.text[:1000]
            )

            return []


        data = response.json()


        ads = data.get(
            "ads",
            []
        )


        print(
            "Получено:",
            len(ads)
        )


        return ads


    except requests.RequestException as e:

        print(
            "Ошибка запроса Kufar:",
            e
        )

        return []


    except ValueError:

        print(
            "Kufar вернул некорректный JSON"
        )

        return []


# ==========================================
# ПРЕОБРАЗОВАНИЕ KUFAR → STYLEFLOW
# ==========================================

def convert_kufar_ad(
    ad
):

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


    price, currency = extract_price(
        ad
    )


    images = extract_images(
        ad
    )


    category = (
        ad.get("category")
        or ""
    )


    return {

        # Главное ID StyleFlow
        "id": f"kufar_{ad_id}",

        # Источник
        "source": "kufar",

        # ID оригинального объявления
        "external_id": str(
            ad_id
        ),

        # Название
        "title": str(
            title
        ).strip(),

        # Бренд
        "brand": "",

        # Категория
        "category": str(
            category
        ),

        # Цена
        "price": price,

        # Старая цена
        "oldPrice": 0,

        # Валюта
        "currency": currency,

        # У Kufar пока нет
        # нормального рейтинга товара
        "rating": 0,

        # Главная фотография
        "image": (
            images[0]
            if images
            else ""
        ),

        # Все фотографии
        "images": images,

        # Оригинальный товар
        "url": link,

        # Исходные данные
        "raw": ad
    }


# ==========================================
# ПОЛУЧЕНИЕ ВСЕЙ ЛЕНТЫ
# ==========================================

def build_feed():

    print()
    print(
        "🔥 STYLEFLOW — СОБИРАЕМ ЛЕНТУ"
    )

    print(
        f"Запросов: {len(KUFAR_QUERIES)}"
    )

    print(
        f"Товаров на запрос: "
        f"{ITEMS_PER_QUERY}"
    )


    all_products = []

    used_ids = set()


    # ======================================
    # ПЕРЕБИРАЕМ ЗАПРОСЫ
    # ======================================

    for query in KUFAR_QUERIES:

        ads = get_kufar_ads(
            query=query,
            limit=ITEMS_PER_QUERY
        )


        for ad in ads:

            try:

                product = convert_kufar_ad(
                    ad
                )

            except Exception as e:

                print(
                    "Ошибка обработки товара:",
                    e
                )

                continue


            product_id = product.get(
                "id"
            )


            # ------------------------------
            # Удаляем дубли
            # ------------------------------

            if (
                not product_id
                or product_id in used_ids
            ):

                continue


            # ------------------------------
            # Без картинки
            # не берём
            # ------------------------------

            if not product.get(
                "image"
            ):

                continue


            used_ids.add(
                product_id
            )


            all_products.append(
                product
            )


            # ------------------------------
            # Общий лимит
            # ------------------------------

            if len(
                all_products
            ) >= MAX_FEED_ITEMS:

                break


        if len(
            all_products
        ) >= MAX_FEED_ITEMS:

            break


    # ======================================
    # ПЕРЕМЕШИВАЕМ ЛЕНТУ
    # ======================================

    # Чтобы сначала не шли подряд
    # все кроссовки, потом футболки и т.д.

    import random

    random.shuffle(
        all_products
    )


    print()
    print(
        "=" * 60
    )

    print(
        "🔥 ЛЕНТА СОБРАНА"
    )

    print(
        "Товаров:",
        len(all_products)
    )

    print(
        "=" * 60
    )


    return {

        "source": "Kufar",

        "query": "StyleFlow",

        "count": len(
            all_products
        ),

        "updated_at": time.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "items": all_products
    }


# ==========================================
# СОХРАНЕНИЕ FEED.JSON
# ==========================================

def save_feed(
    feed,
    filename="feed.json"
):

    items = feed.get(
        "items",
        []
    )


    if not items:

        print(
            "❌ Товары отсутствуют."
        )

        print(
            "Старый feed.json "
            "не изменён."
        )

        return False


    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(

                feed,

                file,

                ensure_ascii=False,

                indent=2
            )


        print(
            f"💾 feed.json сохранён:"
            f" {len(items)} товаров"
        )


        return True


    except Exception as e:

        print(
            "Ошибка сохранения:",
            e
        )

        return False


# ==========================================
# ОТПРАВКА В MINI APP
# ==========================================

def send_feed_to_miniapp(
    feed
):

    items = feed.get(
        "items",
        []
    )


    if not items:

        print(
            "❌ Mini App: "
            "нечего отправлять."
        )

        return False


    try:

        print()
        print(
            f"🚀 Mini App: отправляю "
            f"{len(items)} товаров..."
        )


        response = requests.post(

            MINIAPP_URL,

            json=items,

            headers={
                "Content-Type":
                "application/json"
            },

            timeout=30
        )


        print(
            "HTTP:",
            response.status_code
        )


        response.raise_for_status()


        try:

            result = response.json()

        except ValueError:

            result = response.text


        print(
            "✅ Mini App: "
            "фид успешно отправлен."
        )


        print(
            "Ответ сервера:",
            result
        )


        return True


    except requests.RequestException as e:

        print(
            "❌ Mini App: "
            f"ошибка отправки: {e}"
        )

        return False


# ==========================================
# MAIN
# ==========================================

def main():

    print()
    print(
        "=" * 60
    )

    print(
        "STYLEFLOW AGGREGATOR"
    )

    print(
        "KUFAR → MINI APP"
    )

    print(
        "=" * 60
    )


    # ------------------------------
    # Собираем
    # ------------------------------

    feed = build_feed()


    # ------------------------------
    # Сохраняем
    # ------------------------------

    saved = save_feed(
        feed
    )


    if not saved:

        print(
            "❌ Фид пустой."
        )

        return


    # ------------------------------
    # Отправляем
    # ------------------------------

    sent = send_feed_to_miniapp(
        feed
    )


    print()
    print(
        "=" * 60
    )


    if sent:

        print(
            "🔥 STYLEFLOW ГОТОВ"
        )

        print(
            f"В ленте: "
            f"{feed['count']} товаров"
        )

    else:

        print(
            "⚠️ Товары собраны,"
            " но Mini App не получил фид."
        )


    print(
        "=" * 60
    )


# ==========================================
# ЗАПУСК
# ==========================================

if __name__ == "__main__":

    main()
