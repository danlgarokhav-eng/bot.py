from playwright.sync_api import sync_playwright
import json
import time

def parse_wb_search(query):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}"
        page.goto(url)

        time.sleep(3)  # ждём загрузку JS

        products = page.query_selector_all("div.product-card")

        items = []

        for product in products:
            try:
                name = product.query_selector("span.goods-name").inner_text()
                price = product.query_selector("ins").inner_text()
                link = product.query_selector("a").get_attribute("href")

                items.append({
                    "name": name,
                    "price": price,
                    "link": "https://www.wildberries.ru" + link
                })
            except:
                continue

        browser.close()
        return items


def main():
    query = "кроссовки"
    items = parse_wb_search(query)

    feed = {
        "query": query,
        "count": len(items),
        "items": items
    }

    print(json.dumps(feed, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
