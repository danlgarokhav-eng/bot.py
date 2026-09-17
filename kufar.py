import requests
import json

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

KUFAR_QUERY = "кроссовки"


def find_image_fields(value, path="root", result=None):
    if result is None:
        result = []

    if isinstance(value, dict):
        for key, item in value.items():

            key_lower = str(key).lower()

            if any(word in key_lower for word in (
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
            )):
                result.append({
                    "path": f"{path}.{key}",
                    "value": item
                })

            find_image_fields(
                item,
                f"{path}.{key}",
                result
            )

    elif isinstance(value, list):
        for index, item in enumerate(value):
            find_image_fields(
                item,
                f"{path}[{index}]",
                result
            )

    return result


print()
print("=" * 60)
print("STYLEFLOW — ДИАГНОСТИКА ФОТО KUFAR")
print("=" * 60)

params = {
    "size": 1,
    "sort": "lst.d",
    "query": KUFAR_QUERY,
}

print()
print("Запрос:")
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
    print("URL:", response.url)

    if response.status_code != 200:
        print()
        print("ОШИБКА:")
        print(response.text[:5000])
        raise SystemExit

    data = response.json()

    ads = data.get("ads", [])

    print()
    print("Получено объявлений:", len(ads))

    if not ads:
        print("Объявлений нет.")
        raise SystemExit

    ad = ads[0]

    print()
    print("=" * 60)
    print("ПЕРВОЕ ОБЪЯВЛЕНИЕ")
    print("=" * 60)

    print()
    print("ID:", ad.get("ad_id"))
    print("Название:", ad.get("subject"))
    print("Цена:", ad.get("price"))
    print("Ссылка:", ad.get("ad_link"))

    print()
    print("=" * 60)
    print("ПОЛЯ, СВЯЗАННЫЕ С ФОТО")
    print("=" * 60)

    image_fields = find_image_fields(ad)

    if not image_fields:
        print()
        print("ФОТО-ПОЛЯ НЕ НАЙДЕНЫ")
        print()
    else:

        for item in image_fields:

            print()
            print("PATH:")
            print(item["path"])

            print("VALUE:")

            try:
                print(json.dumps(
                    item["value"],
                    ensure_ascii=False,
                    indent=2
                )[:5000])
            except Exception:
                print(str(item["value"])[:5000])

            print("-" * 60)

    print()
    print("=" * 60)
    print("КЛЮЧИ ПЕРВОГО ОБЪЯВЛЕНИЯ")
    print("=" * 60)

    print()

    def print_keys(value, path="root"):

        if isinstance(value, dict):

            for key, item in value.items():

                print(
                    f"{path}.{key} -> "
                    f"{type(item).__name__}"
                )

                print_keys(
                    item,
                    f"{path}.{key}"
                )

        elif isinstance(value, list):

            if value:
                print_keys(
                    value[0],
                    f"{path}[0]"
                )

    print_keys(ad)

    print()
    print("=" * 60)
    print("СОХРАНЯЕМ RAW JSON")
    print("=" * 60)

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

    print()
    print("kufar_response.json сохранён")

except requests.RequestException as e:

    print()
    print("ОШИБКА HTTP:")
    print(e)

except Exception as e:

    print()
    print("ОШИБКА:")
    print(type(e).__name__)
    print(e)
