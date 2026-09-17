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


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Referer": "https://www.kufar.by/",
    "Origin": "https://www.kufar.by",
}


# ============================================================
# ЗАПРОС К КУФАРУ
# ============================================================

def request_kufar(params, name="test"):

    print()
    print("=" * 60)
    print(f"ТЕСТ: {name}")
    print("=" * 60)

    print("PARAMS:")
    print(json.dumps(
        params,
        ensure_ascii=False,
        indent=2
    ))

    try:

        response = requests.get(
            KUFAR_API,
            params=params,
            headers=HEADERS,
            timeout=20
        )

        print()
        print("HTTP:", response.status_code)

        print("URL:")
        print(response.url)

        # ----------------------------------------------------
        # СОХРАНЯЕМ RAW ОТВЕТ
        # ----------------------------------------------------

        try:

            data = response.json()

            with open(
                f"kufar_{name}.json",
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=2
                )

            print(
                f"JSON сохранён: kufar_{name}.json"
            )

            print()
            print("ОСНОВНЫЕ КЛЮЧИ:")

            if isinstance(data, dict):

                print(
                    list(data.keys())
                )

            elif isinstance(data, list):

                print(
                    "Ответ является LIST"
                )

            print()
            print("ПЕРВЫЕ 2000 СИМВОЛОВ:")

            print(
                json.dumps(
                    data,
                    ensure_ascii=False,
                    indent=2
                )[:2000]
            )

            return data

        except ValueError:

            print()
            print(
                "Ответ НЕ является JSON"
            )

            print(
                response.text[:3000]
            )

            with open(
                f"kufar_{name}.txt",
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    response.text
                )

            return None

    except Exception as e:

        print(
            "ОШИБКА:",
            repr(e)
        )

        return None


# ============================================================
# ПОИСК ТОВАРОВ
# ============================================================

def test_kufar():

    print()
    print("=" * 60)
    print("STYLEFLOW — ДИАГНОСТИКА КУФАРА")
    print("=" * 60)

    # --------------------------------------------------------
    # ТЕСТ №1
    # --------------------------------------------------------
    #
    # Старый вариант.
    #

    request_kufar(
        {
            "size": 5,
            "page": 1,
            "query": "кроссовки"
        },
        "test1_query"
    )


    # --------------------------------------------------------
    # ТЕСТ №2
    # --------------------------------------------------------
    #
    # Вариант, который встречается
    # в сторонних проектах Kufar.
    #

    request_kufar(
        {
            "size": 5,
            "sort": "lst.d"
        },
        "test2_basic"
    )


    # --------------------------------------------------------
    # ТЕСТ №3
    # --------------------------------------------------------
    #
    # Пробуем поиск через q.
    #

    request_kufar(
        {
            "size": 5,
            "q": "кроссовки"
        },
        "test3_q"
    )


    # --------------------------------------------------------
    # ТЕСТ №4
    # --------------------------------------------------------
    #
    # Пробуем keyword.
    #

    request_kufar(
        {
            "size": 5,
            "keyword": "кроссовки"
        },
        "test4_keyword"
    )


    print()
    print("=" * 60)
    print("ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 60)

    print()
    print(
        "Теперь в корне проекта должны появиться:"
    )

    print(
        "kufar_test1_query.json"
    )

    print(
        "kufar_test2_basic.json"
    )

    print(
        "kufar_test3_q.json"
    )

    print(
        "kufar_test4_keyword.json"
    )


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":

    test_kufar()
    
