import requests
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://www.wildberries.ru/",
}

def get_wb_items(category="men_shoes", page=1, limit=100):
    url = f"https://catalog.wb.ru/catalog/{category}/catalog"
    params = {
        "appType": 1,
        "curr": "rub",
        "dest": 12358230,      # ВАЖНО: рабочий dest
        "sort": "popular",
        "page": page,
        "limit": limit
    }

    r = requests.get(url, params=params, headers=HEADERS)

    try:
        data = r.json()
    except:
        print("WB вернул НЕ JSON. Ответ:")
        print(r.text[:500])
        return []

    items = []

    for product in data.get("data", {}).get("products", []):
        items.append({
            "id": product.get("id"),
            "name": product.get("name"),
            "brand": product.get("brand"),
            "price": product.get("salePriceU") / 100,
            "old_price": product.get("priceU") / 100,
            "rating": product.get("rating"),
            "feedbacks": product.get("feedbacks"),
            "image": f"https://images.wbstatic.net/c516x688/{product.get('id')}.jpg",
            "link": f"https://www.wildberries.ru/catalog/{product.get('id')}/detail.aspx"
        })

    return items


def main():
    items = get_wb_items("men_shoes")

    feed = {
        "query": "кроссовки",
        "count": len(items),
        "items": items
    }

    print(json.dumps(feed, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
