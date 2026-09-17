import asyncio
from playwright.async_api import async_playwright


WB_URL = "https://www.wildberries.ru/catalog/0/search.aspx"


async def search_wildberries(query="кроссовки", limit=10):
    print()
    print("=" * 60)
    print("STYLEFLOW — WILDBERRIES PLAYWRIGHT")
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

        page = await browser.new_page(
            viewport={
                "width": 1366,
                "height": 900,
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
        )

        url = f"{WB_URL}?search={query}"

        print("Открываю Wildberries...")
        print(url)
        print()

        try:
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            if response:
                print(f"HTTP: {response.status}")

            await page.wait_for_timeout(5000)

            print(f"Заголовок: {await page.title()}")
            print(f"URL после загрузки: {page.url}")

            # Сохраняем HTML для диагностики.
            html = await page.content()

            with open(
                "wb_debug.html",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(html)

            print("HTML сохранён в wb_debug.html")

            # Ищем карточки товаров.
            cards = await page.locator(
                "article.product-card"
            ).all()

            print(f"Карточек найдено: {len(cards)}")

            products = []

            for card in cards[:limit]:

                try:
                    name_element = card.locator(
                        ".product-card__name"
                    )

                    price_element = card.locator(
                        ".price__lower-price"
                    )

                    link_element = card.locator(
                        "a.product-card__link"
                    )

                    name = ""

                    if await name_element.count():
                        name = (
                            await name_element.first.text_content()
                            or ""
                        )

                    price = ""

                    if await price_element.count():
                        price = (
                            await price_element.first.text_content()
                            or ""
                        )

                    link = ""

                    if await link_element.count():
                        link = (
                            await link_element.first.get_attribute(
                                "href"
                            )
                            or ""
                        )

                    products.append(
                        {
                            "name": name.strip(),
                            "price": price.strip(),
                            "url": link,
                        }
                    )

                except Exception as e:
                    print(
                        f"⚠️ Ошибка обработки карточки: {e}"
                    )

            print()
            print("=" * 60)
            print("ТОВАРЫ")
            print("=" * 60)

            for i, product in enumerate(products, 1):
                print()
                print(f"#{i}")
                print(f"Название: {product['name']}")
                print(f"Цена:     {product['price']}")
                print(f"Ссылка:   {product['url']}")

            await browser.close()

            return products

        except Exception as e:

            print()
            print(f"❌ Ошибка Playwright: {e}")

            await page.screenshot(
                path="wb_error.png",
                full_page=True,
            )

            await browser.close()

            return []


if __name__ == "__main__":
    asyncio.run(
        search_wildberries(
            query="кроссовки",
            limit=10,
        )
    )
