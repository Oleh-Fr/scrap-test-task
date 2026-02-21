import re


def parse_mileage(text: str) -> int | None:
    if not text:
        return None
    text = re.sub(r"<!--.*?-->", "", text).replace("\xa0", " ").strip().lower()
    match = re.search(r"[\d\s,.]+", text)
    if not match:
        return None
    number = match.group(0).replace(" ", "").replace(",", ".")
    try:
        value = float(number)
        if "тис" in text:
            value *= 1000
        return int(value)
    except ValueError:
        return None


def clean_price(text: str) -> int | None:
    if not text:
        return None
    text = text.replace("\xa0", " ").strip()
    match = re.search(r"([\d\s,.]+)", text)
    if not match:
        return None
    number = match.group(1).replace(" ", "").replace(",", "")
    try:
        return int(number)
    except ValueError:
        return None
