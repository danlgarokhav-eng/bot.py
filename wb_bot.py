import requests
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

def search_wb(query, limit=100):
    url = "https://catalog.wb.ru/catalog/search/catalog"
    params = {
        "search": query,
        "page": 1,
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
    query = "кроссовки"

    items = search_wb(query)

    feed = {
        "query": query,
        "count": len(items),
        "items": items
    }

    print(json.dumps(feed, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
