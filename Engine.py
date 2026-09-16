#Imports
import tkinter as tk
from tkinter import scrolledtext
from tkinter import filedialog
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
from Setup_DB import choice

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

#Function to open a folder picker and store the chosen path
def choose_output_directory(output_path_var, text_widget):
    folder = filedialog.askdirectory()
    if folder:  # user might cancel, which returns an empty string
        output_path_var.set(folder)
        log(text_widget, f"Output directory set to: {folder}")

#Function to read existing URL's from a CSV file and use to avoid duplicate entries
def load_existing_urls(filepath, text_widget):
    existing_urls = set()
    try:
        with open(filepath, mode="r", newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get("url"):
                    existing_urls.add(row["url"])
        log(text_widget, f"Loaded {len(existing_urls)} existing entries from: {filepath}")
    except Exception as e:
        log(text_widget, f"ERROR reading existing CSV: {type(e).__name__}: {e}")
    return existing_urls

#Function to filter out businesses whose url already exists in the target CSV
def filter_new_businesses(businesses, existing_urls, text_widget):
    new_businesses = [b for b in businesses if b.get("url") not in existing_urls]
    skipped = len(businesses) - len(new_businesses)
    if skipped > 0:
        log(text_widget, f"Skipped {skipped} duplicate businesses already in the file.")
    return new_businesses

#Function to open a file picker for selecting an existing CSV to append to
def choose_existing_csv(csv_path_var, text_widget):
    filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filepath:
        csv_path_var.set(filepath)
        log(text_widget, f"Will append to: {filepath}")

#Function to create a fresh numbered output directory inside the chosen base path
def generate_directory(text_widget, base_path):
    try:
        path = os.path.join(base_path, directory_name)
        counter = 1
        while os.path.exists(path):
            path = os.path.join(base_path, f"{directory_name}_{counter}")
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

#Function to add a typed query into the queries listbox, then close the popup
def add_query(query_text, queries_listbox, popup , entry):
    query_text = query_text.strip()
    if query_text:
        queries_listbox.insert(tk.END, query_text)
        entry.delete(0, tk.END)

#Function to open the small "add query" popup window next to the address field
def open_add_query_popup(root, queries_listbox):
    popup = tk.Toplevel(root)
    popup.title("Add Query")
    popup.geometry("360x110")
    popup.transient(root)
    popup.grab_set()  # keep focus on popup until it's closed

    tk.Label(popup, text="Enter another address/query:").pack(anchor="w", padx=10, pady=(10, 0))
    entry = tk.Entry(popup, width=50)
    entry.pack(padx=10, pady=5, fill="x")
    entry.focus_set()

    entry.bind("<Return>", lambda event: add_query(entry.get(), queries_listbox, popup , entry ))
    popup.bind("<Escape>", lambda event: popup.destroy())

#Function to remove whichever queries are currently selected in the listbox
def remove_selected_queries(queries_listbox):
    selection = queries_listbox.curselection()
    for index in reversed(selection):
        queries_listbox.delete(index)

def run_scrape(url, addresses, text_widget, start_button, output_path_var, save_mode_var, csv_path_var):
    driver = None
    try:
        log(text_widget, "Starting Chrome...")
        driver = webdriver.Chrome()
        driver.get(url)
        driver.set_window_size(1300, 1200)
        wait_for_page_ready(driver)

        all_businesses = {}

        for i, address in enumerate(addresses, start=1):
            # Reset back to the base Maps page before every query after the first,
            # so leftover panel state from the previous search doesn't interfere.
            if i > 1:
                driver.get(url)
                wait_for_page_ready(driver)

            log(text_widget, f"[{i}/{len(addresses)}] Searching: {address}")
            try:
                search_address(driver, address)
            except Exception as e:
                log(text_widget, f"ERROR: Could not search '{address}' ({type(e).__name__}), skipping this query.")
                continue

            log(text_widget, "Scrolling and collecting results...")
            businesses = scroll_and_collect(driver, text_widget)
            log(text_widget, f"Found {len(businesses)} unique businesses for this query.")

            log(text_widget, "Collecting detailed info for each business...")
            businesses = collect_place_details(driver, businesses, text_widget)

            for biz in businesses:
                if biz.get("url"):
                    all_businesses[biz["url"]] = biz

            log(text_widget, f"Running total: {len(all_businesses)} unique businesses across all queries so far.")

        businesses = list(all_businesses.values())

        fieldnames = ["name", "url", "rating", "review_count", "category",
                      "details", "address", "phone", "open_status", "hours", "price_range"]

        if save_mode_var.get() == "append":
            csv_path = csv_path_var.get()
            if not csv_path:
                log(text_widget, "ERROR: No existing CSV selected to append to.")
                return

            existing_urls = load_existing_urls(csv_path, text_widget)
            businesses = filter_new_businesses(businesses, existing_urls, text_widget)

            if businesses:
                csv_write_rows(csv_path, fieldnames, businesses)
                log(text_widget, f"Appended {len(businesses)} new businesses to: {csv_path}")
            else:
                log(text_widget, "No new businesses to add, file unchanged.")

        else:  # "new" file mode
            base_path = output_path_var.get() or os.getcwd()
            path = generate_directory(text_widget, base_path)
            if path:
                csv_path = os.path.join(path, "businesses.csv")
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
def on_start_click(url_entry, address_entry, queries_listbox, text_widget, start_button, output_path_var, save_mode_var, csv_path_var):
    url = url_entry.get().strip()
    primary_address = address_entry.get().strip()
    queued_addresses = [q.strip() for q in queries_listbox.get(0, tk.END)]

    addresses = ([primary_address] if primary_address else []) + queued_addresses
    addresses = [a for a in addresses if a]  # drop any blanks

    if not url or not addresses:
        log(text_widget, "Please enter a URL and at least one address/query.")
        return

    start_button.config(state=tk.DISABLED)
    text_widget.delete("1.0", tk.END)

    thread = threading.Thread(
        target=run_scrape,
        args=(url, addresses, text_widget, start_button, output_path_var, save_mode_var, csv_path_var),
        daemon=True
    )
    thread.start()

#Function to build and launch the GUI
def build_gui():
    root = tk.Tk()
    root.title("Maps Scraps")
    root.geometry("600x650")

    output_path_var = tk.StringVar(value="")
    csv_path_var = tk.StringVar(value="")
    save_mode_var = tk.StringVar(value="new")  # "new" or "append"

    tk.Label(root, text="Maps URL:").pack(anchor="w", padx=10, pady=(10, 0))
    url_entry = tk.Entry(root, width=80)
    url_entry.pack(padx=10, fill="x")

    tk.Label(root, text="Address to search:").pack(anchor="w", padx=10, pady=(10, 0))
    address_frame = tk.Frame(root)
    address_frame.pack(padx=10, fill="x")
    address_entry = tk.Entry(address_frame, width=70)
    address_entry.pack(side="left", fill="x", expand=True)
    add_query_button = tk.Button(
        address_frame, text="+", width=3,
        command=lambda: open_add_query_popup(root, queries_listbox)
    )
    add_query_button.pack(side="left", padx=(5, 0))

    tk.Label(root, text="Queued queries (select + press Delete to remove):").pack(anchor="w", padx=10, pady=(10, 0))
    queries_frame = tk.Frame(root)
    queries_frame.pack(padx=10, fill="x")
    queries_listbox = tk.Listbox(queries_frame, height=4, selectmode=tk.EXTENDED)
    queries_listbox.pack(side="left", fill="both", expand=True)
    queries_scrollbar = tk.Scrollbar(queries_frame, orient="vertical", command=queries_listbox.yview)
    queries_scrollbar.pack(side="right", fill="y")
    queries_listbox.config(yscrollcommand=queries_scrollbar.set)
    queries_listbox.bind("<Delete>", lambda event: remove_selected_queries(queries_listbox))

    text_widget = scrolledtext.ScrolledText(root, height=15)
    text_widget.pack(padx=10, pady=10, fill="both", expand=True)

    # Save mode selector
    mode_frame = tk.Frame(root)
    mode_frame.pack(pady=(0, 5))
    tk.Radiobutton(mode_frame, text="New file", variable=save_mode_var, value="new").pack(side="left", padx=5)
    tk.Radiobutton(mode_frame, text="Append to existing", variable=save_mode_var, value="append").pack(side="left", padx=5)

    output_button = tk.Button(
        root, text="Choose output directory (new file mode)",
        command=lambda: choose_output_directory(output_path_var, text_widget)
    )
    output_button.pack(pady=(0, 2))
    tk.Label(root, textvariable=output_path_var, fg="gray").pack()

    csv_button = tk.Button(
        root, text="Choose existing CSV (append mode)",
        command=lambda: choose_existing_csv(csv_path_var, text_widget)
    )
    csv_button.pack(pady=(5, 2))
    tk.Label(root, textvariable=csv_path_var, fg="gray").pack(pady=(0, 10))

    start_button = tk.Button(
        root, text="Start Scraping",
        command=lambda: on_start_click(url_entry, address_entry, queries_listbox, text_widget, start_button, output_path_var, save_mode_var, csv_path_var)
    )
    start_button.pack(pady=(0, 10))

    root.mainloop()

if __name__ == "__main__":
    choice()