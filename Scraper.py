#Imports  
import requests  
import os  
from bs4 import BeautifulSoup  
import selenium  
from selenium import webdriver  
from selenium.webdriver.common.by import By 
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from rich import print as rprint  
import time  
import csv
 
directory_name = "Information_Sample"  
 
#Welcome message  
rprint("[cyan]Welcome to the unorthodox scraper[/cyan]")  
 
#Function to get the URL to scrape  
def get_url():  
    try:  
        URL = input("Please enter the exact URL you want to scrape: ")  
        return URL  
    except Exception as e:  
        rprint(f"[red][ERROR]:[/red] {e}")  
        return None 

#Helper to wait specifically for result cards to appear in the DOM
def wait_for_results(driver, timeout=15):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="article"]'))
    )

#Helper to wait for the page to actually finish loading instead of sleeping blindly
def wait_for_page_ready(driver, timeout=15):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
 
def search_address(driver, address): 
    # Wait for the search box to be present and interactable 
    search_box = WebDriverWait(driver, 10).until( 
        EC.element_to_be_clickable((By.NAME, "q")) 
    ) 
    search_box.clear() 
    search_box.send_keys(address) 
    search_box.send_keys(Keys.RETURN) 
 
    # Give the results/map time to load 
    wait_for_page_ready(driver)
    wait_for_results(driver)
 
#Function to create directory for HTML samples 
def generate_directory():  
    try:  
        path = directory_name 
        counter = 1 
 
        while os.path.exists(path): 
            path = f"{directory_name}_{counter}" 
            counter += 1 
 
        os.mkdir(path) 
 
        rprint(f"[green][SUCCESS]: Directory Created at:[/green] {os.path.abspath(path)}") 
 
        return path 
 
    except PermissionError:  
        rprint(f"[red][ERROR]:[/red] {PermissionError}")  
        return None
    except Exception as e:  
        rprint(f"[red][ERROR]:[/red] {e}")  
        return None

#Function to generate CSV file
def csv_setup(filepath , fieldnames):
    with open(filepath , mode = "w" , newline = '' , encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

#Function to append a list of business dicts to the CSV
def csv_write_rows(filepath, fieldnames, rows):
    with open(filepath, mode="a", newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerows(rows)

#Function to sample the parsed HTML 
def sample_html(path, soup, filename="sample.html"): 
    filepath = os.path.join(path, filename) 
    with open(filepath, "w", encoding="utf-8") as f: 
        f.write(soup.prettify()) 
    rprint(f"[green][SUCCESS]: HTML sample saved to:[/green] {os.path.abspath(filepath)}") 
 
#Function to get place to search 
def get_user_address(): 
    print("[yellow]Enter an adress to lookup:[/yellow]") 
    try: 
        address = input() 
        return address 
    except Exception as e: 
        print(f"[red][ERROR]:[/red] {e}") 

#Function to extract result card info
def extract_business_info(card):
    info = {}

    # Name
    link = card.select_one("a.hfpxzc")
    info["name"] = link["aria-label"] if link and link.has_attr("aria-label") else None
    info["url"] = link["href"] if link and link.has_attr("href") else None

    # Rating
    rating_span = card.select_one("span.MW4etd")
    info["rating"] = rating_span.text if rating_span else None

    review_span = card.select_one("span.UY7F9")
    info["review_count"] = review_span.text.strip("()") if review_span else None

    # Category + details (both live in div.W4Efsd, in order)
    detail_blocks = card.select("div.W4Efsd > span > span")
    info["category"] = detail_blocks[0].text if len(detail_blocks) > 0 else None
    info["details"] = detail_blocks[1].text if len(detail_blocks) > 1 else None

    return info

#Function to run extraction across every card on the parsed page
def extract_all_businesses(soup):
    cards = soup.select('div[role="article"]')
    return [extract_business_info(card) for card in cards]
 
#Function to startup selenium driver  
def setup_selenium(URL):  
    driver = webdriver.Chrome()  
    driver.get(URL)  
 
    wait_for_page_ready(driver)

    # Parse the HTML before the search happens
    html_before = driver.page_source
    soup_before = BeautifulSoup(html_before, "html.parser")

    address = get_user_address()
    if address:
        search_address(driver, address)

    # Parse the HTML after the search happens
    html_after = driver.page_source  
    soup_after = BeautifulSoup(html_after , "html.parser")  

    print()  
    print(soup_after.prettify())   
    return soup_before, soup_after, driver

driver = None
try:
    URL = get_url()
    if URL:
        soup_before, soup_after, driver = setup_selenium(URL)
        path = generate_directory()
        if path:
            sample_html(path, soup_before, "sample_before.html")
            sample_html(path, soup_after, "sample_after.html")

            # Extract business info from the after-search results
            businesses = extract_all_businesses(soup_after)
            rprint(f"[cyan]Found {len(businesses)} results:[/cyan]")
            for b in businesses:
                rprint(b)

            csv_path = os.path.join(path, "businesses.csv")
            fieldnames = ["name", "url", "rating", "review_count", "category", "details"]
            csv_setup(csv_path, fieldnames)
            csv_write_rows(csv_path, fieldnames, businesses)
            rprint(f"[green][SUCCESS]: Data logged to:[/green] {os.path.abspath(csv_path)}")
        else:
            rprint("[red][ERROR]:[/red] Could not create directory, skipping extraction and CSV logging.")

        rprint("[cyan]Driver is staying open. Press Ctrl+C to close it and exit.[/cyan]")
        while True:
            time.sleep(1) 
    else:
        rprint("[red][ERROR]:[/red] No URL provided, exiting.")
except KeyboardInterrupt:
    rprint("\n[yellow]Ctrl+C detected, closing driver...[/yellow]")
finally:
    if driver is not None:
        driver.quit()
        rprint("[green][SUCCESS]: Driver closed.[/green]")