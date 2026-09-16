def pretty(item):

    name = item.get(
        "name",
        "Без названия"
    )

    price = item.get(
        "price",
        0
    )

    rating = item.get(
        "rating",
        0
    )

    brand = item.get(
        "brand",
        ""
    )

    return (
        f"{name}\n"
        f"Бренд: {brand}\n"
        f"Цена: {price}$\n"
        f"⭐ {rating}"
    )
