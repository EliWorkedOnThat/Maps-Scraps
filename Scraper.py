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
 
directory_name = "HTML_SAMPLES"  
 
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
    except Exception as e:  
        rprint(f"[red][ERROR]:[/red] {e}")  
 
#Function to sample the parsed HTML 
def sample_html(path, soup): 
    filepath = os.path.join(path, "sample.html") 
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
 
#Function to startup selenium driver  
def setup_selenium(URL):  
    driver = webdriver.Chrome()  
    driver.get(URL)  
 
    wait_for_page_ready(driver)

    address = get_user_address()
    if address:
        search_address(driver, address)

    html = driver.page_source  
    soup = BeautifulSoup(html , "html.parser")  

    print()  
    print(soup.prettify())   
    return soup, driver

driver = None
try:
    URL = get_url()
    if URL:
        soup, driver = setup_selenium(URL)
        path = generate_directory()
        if path:
            sample_html(path, soup)

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