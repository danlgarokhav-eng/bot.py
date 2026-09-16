def filter_by_price(
    items,
    min_price=0,
    max_price=999999
):

    return [
        item
        for item in items
        if min_price <= item.get("price", 0) <= max_price
    ]


def filter_by_brand(
    items,
    brand
):

    brand = brand.lower()

    return [
        item
        for item in items
        if item.get("brand", "").lower() == brand
    ]


def filter_by_category(
    items,
    category
):

    category = category.lower()

    return [
        item
        for item in items
        if category in item.get(
