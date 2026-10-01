def total(prices):
    return round(sum(prices), 2)


def discount(amount, percent):
    if percent < 0 or percent > 100:
        raise ValueError("percent must be between 0 and 100")
    return round(amount * (100 - percent) / 100, 2)


def parse_price(text):
    return round(float(text.strip().lstrip("$")), 2)


def format_price(value):
    return f"${value:.2f}"
