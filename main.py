import asyncio
import httpx
from lxml import html
import re
import random
import traceback
import os


from db import init_db, insert_car
from additional_func import parse_mileage, clean_price


BASE_URL = os.environ.get("URL")
MAX_CONCURRENT = 3
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36",
]

# --- Fetch ---
async def fetch_page(client, url, sem, retries=3):
    async with sem:
        for attempt in range(retries):
            try:
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                resp = await client.get(url, headers=headers, timeout=15.0)
                if resp.status_code == 429:
                    wait = 2**attempt + random.uniform(1, 2)
                    print(f"429 received for {url}, waiting {wait:.1f}s...")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                await asyncio.sleep(random.uniform(0.5, 1.5))
                return html.fromstring(resp.text)
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                print(f"Request failed {url}: {e}")
                await asyncio.sleep(1 + random.random())
        print(f"Failed to fetch {url} after {retries} retries")
        return None


# --- Parse ---
async def parse_detail(client, url, sem):
    tree = await fetch_page(client, url, sem)
    if tree is None:
        return None
    try:
        car_number = tree.xpath('//*[@id="badges"]/div[1]/span/text()')
        username = tree.xpath('//*[@id="sellerInfoUserName"]/span/text()')
        images_count = tree.xpath('//*[@id="photoSlider"]/span/span[2]/text()')
        image_url = tree.xpath('//span[contains(@class,"picture")]//img/@src')
        filtered_image = [u for u in image_url if u and "photosnew/auto/photo" in u]
        text = tree.text_content()
        match = re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", text)
        car_vin = match.group(0) if match else None
        phone_number = tree.xpath(
            '//button[@data-action="showBottomPopUp"]//span[contains(text(),"(")]/text()'
        )

        return {
            "username": username[0].strip() if username else None,
            "phone_number": phone_number[0].strip() if phone_number else None,
            "image_url": filtered_image[0] if filtered_image else None,
            "images_count": int(images_count[0].strip()) if images_count else None,
            "car_number": car_number[0].strip() if car_number else None,
            "car_vin": car_vin,
        }
    except Exception:
        print(f"Error parsing detail {url}:\n{traceback.format_exc()}")
        return None


async def parse_cards(client, page_num, sem):
    url = f"{BASE_URL}?page={page_num}"
    tree = await fetch_page(client, url, sem)
    if tree is None:
        return []

    cards = tree.xpath('//a[contains(@class,"product-card")]')
    if not cards:
        return []

    results = []
    tasks = []

    for card in cards:
        link = card.get("href")
        if not link:
            continue

        title = card.xpath('.//div[contains(@class,"titleS")]/text()')
        price_usd = card.xpath('.//span[contains(@class,"c-green")]/text()')
        mileage = card.xpath('.//span[contains(text(),"тис.")]/text()')
        full_link = "https://auto.ria.com" + link

        tasks.append(parse_detail(client, full_link, sem))
        results.append(
            {
                "url": full_link,
                "title": title[0].strip() if title else None,
                "price_usd": clean_price(price_usd[0]) if price_usd else None,
                "odometer": parse_mileage(mileage[0]) if mileage else None,
            }
        )

    details = await asyncio.gather(*tasks, return_exceptions=True)
    for res, detail in zip(results, details):
        if isinstance(detail, dict):
            res.update(detail)
        else:
            print(f"Skipping detail page due to error:\n{traceback.format_exc()}")

    return results


async def main():
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    # Initialize DB & create table
    await init_db()

    async with httpx.AsyncClient() as client:
        page_num = 0
        while True:
            print(f"Parsing page {page_num}")
            page_results = await parse_cards(client, page_num, sem)

            if not page_results:
                break

            for car in page_results:
                await insert_car(car)

            page_num += 1

    print("Scraping finished!")


if __name__ == "__main__":
    asyncio.run(main())
