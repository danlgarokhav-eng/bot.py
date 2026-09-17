import os
import requests
import json


REEF_API_KEY = os.getenv("REEF_API_KEY", "").strip()

URL = "https://api.reefapi.com/wildberries/v1/search"


headers = {
    "x-api-key": REEF_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

payload = {
    "query": "кроссовки",
    "country": "by",
    "page": 1,
    "sort": "popular",
}


print("=" * 60)
print("STYLEFLOW — REEFAPI / WILDBERRIES")
print("=" * 60)

print("🔑 Ключ:", "найден" if REEF_API_KEY else "НЕ НАЙДЕН")
print("📡 Отправляем запрос...")
print(payload)

try:
    response = requests.post(
        URL,
        headers=headers,
        json=payload,
        timeout=120,
    )

    print()
    print("HTTP:", response.status_code)
    print("Размер ответа:", len(response.text))

    print()
    print(response.text[:10000])

except Exception as e:
    print()
    print("❌ ОШИБКА:")
    print(repr(e))
