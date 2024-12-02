### Scraping Wallmart :https://scrapfly.io/blog/how-to-scrape-walmartcom/" ###

import asyncio
import json
import httpx
from urllib.parse import urlencode
from parsel import Selector
from loguru import logger as log

# List of keywords to check for
flammable_keywords = ["flammable", "flame"]

# Function to parse the search result and get product URLs
def parse_search(html_text: str):
    """Extract search results from search HTML response"""
    sel = Selector(text=html_text)
    data = sel.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
    data = json.loads(data)

    total_results = data["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"][0]["count"]
    results = data["props"]["pageProps"]["initialData"]["searchResult"]["itemStacks"][0]["items"]
    return results, total_results

# Function to scrape the Walmart product page and check for keywords
async def scrape_product_page(session: httpx.AsyncClient, product_url: str):
    """Scrape a product page and check for multiple keywords like 'flammable', 'heat', etc."""
    url = f"https://www.walmart.com{product_url}"
    resp = await session.get(url)
    assert resp.status_code == 200, "Request failed"

    # Use a selector to search for the keywords
    sel = Selector(text=resp.text)

    # Check for any of the keywords in the page text
    flammable_found = False
    page_text = sel.xpath('string(.)').get().lower()  # Get all the text from the page and make it lowercase

    for keyword in flammable_keywords:
        if keyword in page_text:
            flammable_found = True
            break  # Stop checking further if a keyword is found

    return flammable_found


# Function to scrape Walmart search and check product pages
async def scrape_search_and_check_flammable(search_query: str, session: httpx.AsyncClient, max_scrape_pages: int = None):
    """Scrape Walmart search results and check for multiple keywords on product pages"""
    log.info(f"Scraping Walmart search for the keyword {search_query}")

    # Scrape the first page
    _resp_page1 = await scrape_walmart_page(query=search_query, session=session)
    results, total_items = parse_search(_resp_page1.text)

    # Create a list to store the product URLs and whether they are flammable
    flammable_products = []

    # Go through each result and check the product page
    for result in results:
        canonical_url = result.get("canonicalUrl", "")
        if canonical_url:
            log.info(f"Checking product page: {canonical_url}")
            flammable_found = await scrape_product_page(session, canonical_url)
            flammable_products.append({
                "product_name": result["name"],
                "product_url": f"https://www.walmart.com{canonical_url}",
                "flammable": flammable_found
            })

    # Save the results to a JSON file
    with open("flammable_products.json", "w", encoding="utf-8") as file:
        json.dump(flammable_products, file, indent=2, ensure_ascii=False)
    log.info("Results saved to flammable_products.json")

# Function to scrape a single Walmart search page
async def scrape_walmart_page(session: httpx.AsyncClient, query: str = "", page: int = 1, sort: str = "best_match"):
    """Scrape a single Walmart search page"""
    url = "https://www.walmart.com/search?" + urlencode(
        {
            "q": query,
            "sort": sort,
            "page": page,
            "affinityOverride": "default",
        },
    )
    resp = await session.get(url)
    assert resp.status_code == 200, "Request is blocked"
    return resp

# Main async function
async def run():
    # Limit connection speed to prevent scraping too fast
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=5)
    client_session = httpx.AsyncClient(headers={
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-US;en;q=0.9",
        "accept-encoding": "gzip, deflate",
    }, limits=limits)

    # Run the search and check for multiple keywords
    await scrape_search_and_check_flammable(search_query="Antiperspirant Products", session=client_session)

if __name__ == "__main__":
    asyncio.run(run())
