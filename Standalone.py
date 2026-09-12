#Imports
import tkinter as tk
from tkinter import scrolledtext
import threading
import os
import csv
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

directory_name = "Information_Sample"

#Function to log a message into the GUI's text box, safe to call from a background thread
def log(text_widget, message):
    text_widget.after(0, lambda: (
        text_widget.insert(tk.END, message + "\n"),
        text_widget.see(tk.END)
    ))

#Function to wait for the page to finish its initial load
def wait_for_page_ready(driver, timeout=15):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

#Function to wait specifically for result cards to appear in the DOM
def wait_for_results(driver, timeout=15):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="article"]'))
    )

#Function to type an address into the search box and submit it
def search_address(driver, address):
    search_box = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, "q"))
    )
    search_box.clear()
    search_box.send_keys(address)
    search_box.send_keys(Keys.RETURN)
    wait_for_page_ready(driver)
    wait_for_results(driver)

#Function to create a fresh numbered output directory
def generate_directory(text_widget):
    try:
        path = directory_name
        counter = 1
        while os.path.exists(path):
            path = f"{directory_name}_{counter}"
            counter += 1
        os.mkdir(path)
        log(text_widget, f"Directory created at: {os.path.abspath(path)}")
        return path
    except Exception as e:
        log(text_widget, f"ERROR creating directory: {type(e).__name__}: {e}")
        return None

#Function to extract one result card's info
def extract_business_info(card):
    info = {}

    link = card.select_one("a.hfpxzc")
    info["name"] = link["aria-label"] if link and link.has_attr("aria-label") else None
    info["url"] = link["href"] if link and link.has_attr("href") else None

    rating_span = card.select_one("span.MW4etd")
    info["rating"] = rating_span.text if rating_span else None

    review_span = card.select_one("span.UY7F9")
    info["review_count"] = review_span.text.strip("()") if review_span else None

    detail_blocks = card.select("div.W4Efsd > span > span")
    info["category"] = detail_blocks[0].text if len(detail_blocks) > 0 else None
    info["details"] = detail_blocks[1].text if len(detail_blocks) > 1 else None

    return info

#Function to extract every result card on the currently loaded page
def extract_all_businesses(soup):
    cards = soup.select('div[role="article"]')
    return [extract_business_info(card) for card in cards]

#Function to extract full detail-panel info for one business (address, phone, hours, price)
def extract_place_details(soup):
    details = {}

    address_btn = soup.select_one('button[data-item-id="address"]')
    address_text = address_btn.select_one("div.Io6YTe") if address_btn else None
    details["address"] = address_text.text if address_text else None

    phone_btn = soup.select_one('button[data-item-id^="phone:"]')
    phone_text = phone_btn.select_one("div.Io6YTe") if phone_btn else None
    details["phone"] = phone_text.text if phone_text else None

    status_span = soup.select_one("div.o0Svhf span.ZDu9vd")
    details["open_status"] = status_span.text if status_span else None

    hours = {}
    rows = soup.select("table.eK4R0e tr.y0skZc")
    for row in rows:
        day_cell = row.select_one("td.ylH6lf")
        hours_cell = row.select_one("td.mxowUb")
        if day_cell and hours_cell:
            day = day_cell.text.strip()
            hours_label = hours_cell.get("aria-label", hours_cell.text).strip()
            hours[day] = hours_label
    details["hours"] = hours

    price_div = soup.select_one("div.MNVeJb")
    details["price_range"] = price_div.get("aria-label").strip() if price_div and price_div.has_attr("aria-label") else None

    return details

#Function to scroll the results panel and collect every business across all scroll positions
def scroll_and_collect(driver, text_widget, max_scrolls=30, pause=1.5):
    all_businesses = {}
    last_count = 0
    stagnant_rounds = 0

    for i in range(max_scrolls):
        try:
            feed = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
            )
        except Exception as e:
            log(text_widget, f"ERROR: Could not find results panel: {type(e).__name__}")
            break

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        current_batch = extract_all_businesses(soup)

        for biz in current_batch:
            if biz["url"]:
                all_businesses[biz["url"]] = biz

        log(text_widget, f"Scroll {i+1}: {len(all_businesses)} unique results so far")

        try:
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].clientHeight;", feed
            )
        except Exception as e:
            log(text_widget, f"WARNING: Scroll action failed this round: {type(e).__name__}")

        time.sleep(pause)

        if len(all_businesses) == last_count:
            stagnant_rounds += 1
            if stagnant_rounds >= 3:
                log(text_widget, "No new results after several scrolls, stopping.")
                break
        else:
            stagnant_rounds = 0
        last_count = len(all_businesses)

    return list(all_businesses.values())

#Function to click into each business card and collect its detail-panel info
def collect_place_details(driver, businesses, text_widget, pause=2.5):
    for biz in businesses:
        if not biz.get("url"):
            continue

        try:
            card_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f'a.hfpxzc[href="{biz["url"]}"]'))
            )

            try:
                card_link.click()
            except Exception:
                driver.execute_script("arguments[0].click();", card_link)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-item-id="address"]'))
            )
            time.sleep(pause)

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            details = extract_place_details(soup)
            biz.update(details)

            log(text_widget, f"Got details for: {biz['name']}")

        except Exception as e:
            log(text_widget, f"ERROR: Failed to get details for {biz.get('name')} ({type(e).__name__}), skipping.")

    return businesses

#Function to write the header row to a fresh CSV file
def csv_setup(filepath, fieldnames):
    with open(filepath, mode="w", newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

#Function to append a list of business dicts to the CSV
def csv_write_rows(filepath, fieldnames, rows):
    with open(filepath, mode="a", newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerows(rows)

#Function that runs the entire scrape end-to-end, meant to run in a background thread
def run_scrape(url, address, text_widget, start_button):
    driver = None
    try:
        log(text_widget, "Starting Chrome...")
        driver = webdriver.Chrome()
        driver.get(url)
        driver.set_window_size(1300, 1200)
        wait_for_page_ready(driver)

        log(text_widget, f"Searching: {address}")
        search_address(driver, address)

        log(text_widget, "Scrolling and collecting results...")
        businesses = scroll_and_collect(driver, text_widget)
        log(text_widget, f"Found {len(businesses)} unique businesses.")

        log(text_widget, "Collecting detailed info for each business...")
        businesses = collect_place_details(driver, businesses, text_widget)

        path = generate_directory(text_widget)
        if path:
            csv_path = os.path.join(path, "businesses.csv")
            fieldnames = ["name", "url", "rating", "review_count", "category",
                          "details", "address", "phone", "open_status", "hours", "price_range"]
            csv_setup(csv_path, fieldnames)
            csv_write_rows(csv_path, fieldnames, businesses)
            log(text_widget, f"Done! Data saved to: {os.path.abspath(csv_path)}")
        else:
            log(text_widget, "ERROR: Could not create output directory, results not saved.")

    except Exception as e:
        log(text_widget, f"ERROR: {type(e).__name__}: {e}")

    finally:
        if driver is not None:
            driver.quit()
        start_button.after(0, lambda: start_button.config(state=tk.NORMAL))

#Function to handle the Start button click
def on_start_click(url_entry, address_entry, text_widget, start_button):
    url = url_entry.get().strip()
    address = address_entry.get().strip()

    if not url or not address:
        log(text_widget, "Please enter both a URL and an address.")
        return

    start_button.config(state=tk.DISABLED)
    text_widget.delete("1.0", tk.END)

    thread = threading.Thread(
        target=run_scrape,
        args=(url, address, text_widget, start_button),
        daemon=True
    )
    thread.start()

#Function to build and launch the GUI
def build_gui():
    root = tk.Tk()
    root.title("Unorthodox Scraper")
    root.geometry("600x500")

    tk.Label(root, text="Maps URL:").pack(anchor="w", padx=10, pady=(10, 0))
    url_entry = tk.Entry(root, width=80)
    url_entry.pack(padx=10, fill="x")

    tk.Label(root, text="Address to search:").pack(anchor="w", padx=10, pady=(10, 0))
    address_entry = tk.Entry(root, width=80)
    address_entry.pack(padx=10, fill="x")

    text_widget = scrolledtext.ScrolledText(root, height=20)
    text_widget.pack(padx=10, pady=10, fill="both", expand=True)

    start_button = tk.Button(
        root, text="Start Scraping",
        command=lambda: on_start_click(url_entry, address_entry, text_widget, start_button)
    )
    start_button.pack(pady=(0, 10))

    root.mainloop()

if __name__ == "__main__":
    build_gui()