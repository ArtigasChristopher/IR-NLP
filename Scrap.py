import json
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def init_driver(chrome_driver_path, headless=True):
    service = Service(chrome_driver_path)
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--log-level=3')
    return webdriver.Chrome(service=service, options=options)

def scroll_to_bottom(driver, scroll_pause_time=2, max_scrolls=5):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def click_load_more(driver, max_clicks=15):
    loop : int = 0
    while loop < max_clicks:
        try:
            load_more = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Load More")]'))
            )
            driver.execute_script("arguments[0].click();", load_more)
            time.sleep(2)
            scroll_to_bottom(driver, scroll_pause_time=2, max_scrolls=2)
        except Exception:
            print("No more articles to load.")
            break
        loop += 1

def load_all_articles(driver):
    scroll_to_bottom(driver, scroll_pause_time=2, max_scrolls=5)
    click_load_more(driver, max_clicks=15)
    scroll_to_bottom(driver, scroll_pause_time=2, max_scrolls=2)

def get_article_urls(driver, url, max_articles=100):
    driver.get(url)
    load_all_articles(driver)
    time.sleep(2)

    articles = driver.find_elements(By.XPATH, "//article")
    urls = []
    for article in articles:
        try:
            a = article.find_element(By.XPATH, ".//a")
            link = a.get_attribute("href")
            if link and "venturebeat.com" in link:
                urls.append(link)
        except Exception:
            continue
    unique_urls = list(dict.fromkeys(urls))[:max_articles]
    return unique_urls

def clean_article_content(content):
    unwanted_patterns = [
        r"Join our daily and weekly newsletters for the latest updates and exclusive content on industry-leading AI coverage\. Learn More",
        r"Subscribe Now",
        r"Read our Privacy Policy",
        r"GB Daily",
        r"Daily insights on business use cases with VB Daily"
    ]
    for pattern in unwanted_patterns:
        content = re.sub(pattern, "", content, flags=re.IGNORECASE)
    content = re.sub(r'\n+', '\n', content)
    return content.strip()

def extract_article_data(driver, href):
    driver.get(href)
    time.sleep(1)
    # Used ChatGPT for this part
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(1)
    
    title = "No title"
    content = "No content available"
    
    title_xpaths = [
        '//h1',
        '//header//h1'
    ]
    for xpath in title_xpaths:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            title = element.text.strip()
            if title:
                break
        except Exception:
            continue
    
    content_xpaths = [
        '//div[contains(@class, "article-content")]',
        '//div[contains(@class, "article__body")]',
        '//div[@class="article-body"]'
    ]
    for xpath in content_xpaths:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            content = element.text.strip()
            if content:
                break
        except Exception:
            continue

    content = clean_article_content(content)
    return {"title": title, "url": href, "content": content}

def scrape_articles(chrome_driver_path, url, max_articles=50):
    driver = init_driver(chrome_driver_path, headless=True)
    articles_data = []
    try:
        article_urls = get_article_urls(driver, url, max_articles)
        print(f"Found {len(article_urls)} unique URLs.")
        for href in article_urls:
            data = extract_article_data(driver, href)
            if data["content"] and data["content"] != "No content available":
                articles_data.append(data)
                print(f"✅ Scraped: {data['title']}")
            else:
                print(f"⚠️ Skipped (empty content): {href}")
            time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()
    return articles_data

def save_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    chrome_driver_path = r"C:\ProgramData\chocolatey\bin\chromedriver.exe"
    url = "https://venturebeat.com/category/ai/"
    articles = scrape_articles(chrome_driver_path, url, max_articles=50)
    save_to_json(articles, "articles_ai.json")
    print(f"\n✅ Saved {len(articles)} articles in 'articles_ai.json'.")

if __name__ == "__main__":
    main()
