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
        print("[red][ERROR]:{e}[/red]")

#Function to startup selenium driver 
def setup_selenium(URL): 
    driver = webdriver.Chrome() 
    driver.get(URL) 

    time.sleep(5) 

    html = driver.page_source 
    soup = BeautifulSoup(html , "html.parser") 
    driver.quit() 
    print() 
    print(soup.prettify())  
    return soup

URL = get_url() 
if URL:
    soup = setup_selenium(URL)
    path = generate_directory()
    if path:
        sample_html(path, soup)
else:
    rprint("[red][ERROR]:[/red] No URL provided, exiting.")