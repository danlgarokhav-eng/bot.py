import asyncio
import json

from playwright.async_api import async_playwright


SEARCH_URL = (
    "https://search.wb.ru/exactmatch/ru/common/v18/search"
)


async def search_wildberries(query="кроссовки", limit=10):
    print()
    print("=" * 60)
    print("STYLEFLOW — WILDBERRIES JS FETCH")
    print("=" * 60)
    print(f"Запрос: {query}")
    print(f"Лимит: {limit}")
    print()

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = await browser.new_context(
            viewport={
                "width": 1366,
                "height": 900,
            },
            locale="ru-RU",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
        )

        page = await context.new_page()

        try:
            print("Открываю Wildberries...")

            response = await page.goto(
                "https://www.wildberries.ru/",
                wait_until="domcontentloaded",
                timeout=60000,
            )

            if response:
                print(f"Главная страница HTTP: {response.status}")

            await page.wait_for_timeout(3000)

            print("Выполняю fetch внутри Chromium...")

            result = await page.evaluate(
                """
                async ({ searchUrl, query }) => {

                    const params = new URLSearchParams({
                        query: query,
                        resultset: "catalog",
                        dest: "-1257786",
                        curr: "rub",
                        spp: "30",
                        appType: "1",
                        lang: "ru",
                        page: "1",
                        sort: "popular"
                    });

                    const url = searchUrl + "?" + params.toString();

                    try {

                        const response = await fetch(
                            url,
                            {
                                method: "GET",
                                credentials: "include",
                                headers: {
                                    "Accept": "*/*"
                                }
                            }
                        );

                        const text = await response.text();

                        return {
                            status: response.status,
                            url: url,
                            text: text
                        };

                    } catch (error) {

                        return {
                            status: 0,
                            url: url,
                            error: String(error)
                        };
                    }
                }
                """,
                {
                    "searchUrl": SEARCH_URL,
                    "query": query,
                },
            )

            print(f"Fetch HTTP: {result.get('status')}")
            print(f"Fetch URL: {result.get('url')}")

            if result.get("error"):
                print(f"❌ Ошибка fetch: {result['error']}")
                await browser.close()
                return []

            text = result.get("text", "")

            print(f"Получено символов: {len(text)}")

            if not text:
                print("❌ Wildberries вернул пустой ответ.")
                await browser.close()
                return []

            # Сохраняем ответ для диагностики.
            with open(
                "wb_response.txt",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(text)

            print("Ответ сохранён в wb_response.txt")

            if result["status"] != 200:
                print()
                print("❌ WB не вернул HTTP 200.")
                print("Первые 500 символов ответа:")
                print(text[:500])

                await browser.close()
                return []

            try:
                data = json.loads(text)

            except json.JSONDecodeError as e:
                print(f"❌ Ответ не является JSON: {e}")
                print(text[:500])

                await browser.close()
                return []

            products = data.get("products", [])

            if not isinstance(products, list):

                # На случай другой структуры ответа.
                nested_data = data.get("data", {})

                if isinstance(nested_data, dict):
                    products = nested_data.get(
                        "products",
                        [],
                    )

            print(f"Товаров получено: {len(products)}")

            result_products = []

            for product in products[:limit]:

                nm_id = product.get("id")

                name = (
                    product.get("name")
                    or product.get("title")
                    or "Товар Wildberries"
                )

                brand = product.get(
                    "brand",
                    "",
                )

                sale_price = product.get(
                    "salePriceU"
                )

                price_u = product.get(
                    "priceU"
                )

                if sale_price is not None:
                    try:
                        price = float(sale_price) / 100
                    except (TypeError, ValueError):
                        price = 0
                elif price_u is not None:
                    try:
                        price = float(price_u) / 100
                    except (TypeError, ValueError):
                        price = 0
                else:
                    price = 0

                if price_u is not None:
                    try:
                        old_price = float(price_u) / 100
                    except (TypeError, ValueError):
                        old_price = 0
                else:
                    old_price = 0

                rating = product.get(
                    "reviewRating"
                )

                reviews = product.get(
                    "feedbacks",
                    0,
                )

                url = ""

                if nm_id:
                    url = (
                        "https://www.wildberries.ru/catalog/"
                        f"{nm_id}/detail.aspx"
                    )

                normalized = {
                    "id": f"wb_{nm_id}",
                    "source": "wildberries",
                    "external_id": str(nm_id),

                    "title": name,
                    "name": name,

                    "brand": brand,
                    "category": "",

                    "price": price,
                    "oldPrice": old_price,
                    "currency": "RUB",

                    "rating": rating,
                    "stock": None,
                    "reviews": reviews,

                    "image": "",
                    "images": [],

                    "url": url,
                    "link": url,

                    "description": "",

                    "raw": product,
                }

                result_products.append(
                    normalized
                )

            print()
            print("=" * 60)
            print("ТОВАРЫ")
            print("=" * 60)

            for i, product in enumerate(
                result_products,
                1,
            ):
                print()
                print(f"#{i}")
                print(
                    f"ID:       "
                    f"{product['external_id']}"
                )
                print(
                    f"Название: "
                    f"{product['title']}"
                )
                print(
                    f"Бренд:    "
                    f"{product['brand']}"
                )
                print(
                    f"Цена:     "
                    f"{product['price']} "
                    f"{product['currency']}"
                )
                print(
                    f"Старая:   "
                    f"{product['oldPrice']} "
                    f"{product['currency']}"
                )
                print(
                    f"Рейтинг:  "
                    f"{product['rating']}"
                )
                print(
                    f"Отзывы:   "
                    f"{product['reviews']}"
                )
                print(
                    f"Ссылка:   "
                    f"{product['url']}"
                )

            await browser.close()

            return result_products

        except Exception as e:

            print()
            print(f"❌ Общая ошибка: {e}")

            await browser.close()

            return []


if __name__ == "__main__":
    asyncio.run(
        search_wildberries(
            query="кроссовки",
            limit=10,
        )
    )
