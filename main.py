import asyncio
import httpx
from lxml import html
import re


BASE_URL = "https://auto.ria.com/uk/search/"

# -------------------------------
# Допоміжні функції
# -------------------------------

def parse_mileage(text: str) -> int | None:
    """Перетворює пробіг типу '285 тис. км' або '1 667 км' у int"""
    if not text:
        return None
    text = re.sub(r"<!--.*?-->", "", text)
    text = text.replace("\xa0", " ").strip().lower()
    match = re.search(r'[\d\s,.]+', text)
    if not match:
        return None
    number = match.group(0).replace(" ", "").replace(",", "")
    if not number:
        return None
    value = int(number)
    if 'тис' in text:
        value *= 1000
    return value

def clean_price(text: str) -> int | None:
    """Витягує число з тексту типу '23 800 $' або '1 667 050 грн'"""
    if not text:
        return None
    text = text.replace("\xa0", " ").strip()
    match = re.search(r'([\d\s,.]+)', text)
    if not match:
        return None
    number = match.group(1).replace(" ", "").replace(",", "")
    return int(number) if number else None

# -------------------------------
# Асинхронний парсер сторінки
# -------------------------------

async def fetch_page(client, url):
    resp = await client.get(url)
    resp.raise_for_status()
    return html.fromstring(resp.text)

async def parse_cards(client, url):
    tree = await fetch_page(client, url)
    cards = tree.xpath('//a[contains(@class,"product-card")]')

    results = []
    for card in cards:
        title = card.xpath('.//div[contains(@class,"titleS")]/text()')
        price_usd = card.xpath('.//span[contains(@class,"c-green")]/text()')
        mileage = card.xpath('.//span[contains(text(),"тис.")]/text()')
        link = card.get("href")

        detail_tree = await fetch_page(client, "https://auto.ria.com" + link)

        car_number = detail_tree.xpath('//*[@id="badges"]/div[1]/span/text()')
        username = detail_tree.xpath('//*[@id="sellerInfoUserName"]/span/text()')
        images_count = detail_tree.xpath('//*[@id="photoSlider"]/span/span[2]/text()')
        image_url = detail_tree.xpath('//span[contains(@class,"picture")]//img/@src')
        filtered_image = [url for url in image_url if url and "photosnew/auto/photo" in url]

        text = detail_tree.text_content()
        match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', text)
        car_vin = match.group(0) if match else None

        phone_number = detail_tree.xpath('//button[@data-action="showBottomPopUp"]//span[contains(text(),"(")]/text()')

        results.append({
        "url": "https://auto.ria.com" + link if link else None,
        "title": title[0].strip() if title else None,
        "price_usd": clean_price(price_usd[0]) if price_usd else None,
        "odometer": parse_mileage(mileage[0]) if mileage else None,
        "username": username[0].strip() if username else None,
        "phone_number": phone_number[0].strip() if phone_number else None,
        "image_url": filtered_image[0] if filtered_image else None ,
        "images_count": int(images_count[0].strip()) if images_count else None,
        "car_number": car_number[0].strip() if car_number else None,
        "car_vin": car_vin if car_vin else None,
    })

    return results


async def main():
    async with httpx.AsyncClient() as client:
        cars = await parse_cards(client, BASE_URL)
        for car in cars:
            print(car)


if __name__ == "__main__":
    asyncio.run(main())
