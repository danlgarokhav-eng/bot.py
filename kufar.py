import requests
import re

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

print("API HTTP:", response.status_code)

data = response.json()
ad = data["ads"][0]

ad_id = ad["ad_id"]
ad_url = ad["ad_link"]

print()
print("ОБЪЯВЛЕНИЕ:")
print(ad["subject"])
print(ad_url)

print()
print("PATH ИЗ API:")
for image in ad.get("images", []):
    print(image.get("path"))

print()
print("=" * 60)
print("ПРОВЕРЯЕМ СТРАНИЦУ KUFAR")
print("=" * 60)

page = requests.get(
    ad_url,
    headers=HEADERS,
    timeout=20
)

print("PAGE HTTP:", page.status_code)
print("Размер страницы:", len(page.text))

print()
print("ИЩЕМ JPG/WEBP URL:")

urls = re.findall(
    r'https?://[^"\'\s<>]+?\.(?:jpg|jpeg|webp|png)',
    page.text,
    re.IGNORECASE
)

unique = []

for url in urls:
    if url not in unique:
        unique.append(url)

for index, url in enumerate(unique[:20], start=1):
    print()
    print(f"IMAGE #{index}:")
    print(url)

print()
print("Всего найдено:", len(unique))
