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
    "Referer": "https://www.kufar.by/",
}

params = {
    "size": 1,
    "sort": "lst.d",
    "query": "кроссовки",
}

response = requests.get(
    KUFAR_API,
    params=params,
    headers=HEADERS,
    timeout=20
)

print("HTTP:", response.status_code)

data = response.json()
ad = data["ads"][0]

print()
print("НАЗВАНИЕ:")
print(ad.get("subject"))

print()
print("ФОТО:")
print("=" * 60)

for index, image in enumerate(ad.get("images", []), start=1):

    path = image.get("path")
    storage = image.get("media_storage")

    print()
    print(f"Фото #{index}")
    print("storage:", storage)
    print("path:", path)

print()
print("=" * 60)
print("ПЕРВЫЙ PATH:")
print(ad["images"][0]["path"])
