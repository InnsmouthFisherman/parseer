import time
import json
import requests
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

AUTHORIZATION = "Bearer ..."
X_USERID = "2286769"
X_USERDATA = "YOUR USERDATA"

def get_cookies(query):
    ua = UserAgent()
    user_agent = ua.random

    options = Options()
    options.add_argument(f"--user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}"
        driver.get(search_url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-card, .j-card-item"))
        )
        time.sleep(2)

        cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
        print(f"getting {len(cookies)} cookies")
        return cookies, user_agent
    except Exception as e:
        print(f"err getting cookies: {e}")
        return None, None
    finally:
        driver.quit()

def parse(query, pages=1, cookies=None, user_agent=None):
    url = "https://www.wildberries.ru/__internal/search/exactmatch/ru/common/v18/search"
    
    params = {
        "query": query,
        "curr": "rub",
        "dest": "-3827485",
        "resultset": "catalog",
        "sort": "popular",
        "spp": 30,
    }

    encoded_query = quote(query)

    headers = {
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Authorization": AUTHORIZATION,
        "x-userid": X_USERID,
        "x-userdata": X_USERDATA,
        "Referer": f"https://www.wildberries.ru/catalog/0/search.aspx?search={encoded_query}",
        "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://www.wildberries.ru",
        "x-requested-with": "XMLHttpRequest",
        "x-spa-version": "14.13.2",
        "x-queryid": f"qid{int(time.time())}",
    }

    all_products = []

    for page in range(1, pages + 1):
        params["page"] = page
        print(f"requesting {page}...")
        try:
            response = requests.get(url, params=params, headers=headers, cookies=cookies)
            response.raise_for_status()
            data = response.json()
            ###
            products = data.get("data", {}).get("products", [])
            if not products:
                print(f"no products at {page} page")
                break
            all_products.extend(products)
            print(f"got {len(products)} products, total: {len(all_products)}")
            time.sleep(1)
        except Exception as e:
            print(f"error in page {page}: {e}, perhaps token update needed")
            break

    return data

def main():
    query = input("request?: ")
    pages = int(input("pages?: "))

    cookies, user_agent = get_cookies(query)
    if not cookies:
        print("err getting cookies")
        return

    products = parse(query, pages, cookies, user_agent)
    if products:
        with open("wb_products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"{len(products)} products in wb_products.json")
    else:
        print("err getting data")

if __name__ == "__main__":
    main()
