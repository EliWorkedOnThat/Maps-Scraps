# Maps Scraps 🗺️

A Python-based GUI tool for collecting business information from Google Maps using Selenium and BeautifulSoup.

> ⚠️ **Work in Progress** — This project is actively being developed. Features, implementation details, and the interface are subject to change.

## Current Features

* Search Google Maps using a provided location/address
* Automatically scroll through dynamically loaded results
* Collect unique businesses
* Extract:

  * Business name
  * Google Maps URL
  * Rating
  * Review count
  * Category
  * Additional listing details
  * Address
  * Phone number
  * Opening hours
  * Open/closed status
  * Price range
* Export results to CSV
* Append results to an existing CSV
* Automatically skip duplicate businesses
* Select output directories through a GUI
* Live scraping logs
* Background scraping thread to keep the GUI responsive

## Tech Stack

* **Python**
* **Selenium**
* **BeautifulSoup4**
* **Tkinter**
* **CSV**
* **Threading**

## Current Workflow

```text
Google Maps
     ↓
Selenium
     ↓
Search Location
     ↓
Scroll & Collect Results
     ↓
BeautifulSoup
     ↓
Extract Business Data
     ↓
Collect Detailed Information
     ↓
Duplicate Filtering
     ↓
CSV Export
```

## Project Status

The core scraping workflow is currently functional, but the project is **not finished**.

Future development may include:

* Improved error handling
* More robust selectors
* Better scraping controls
* Improved GUI
* Additional export formats
* More configuration options
* Performance improvements
* Cleaner project architecture

## Disclaimer

This project is intended for educational and research purposes. When using it, make sure your use of automated data collection complies with the applicable website terms, policies, and laws.

## Author

Built by **EliWorkedOnThat** while experimenting with browser automation, web scraping, HTML parsing, and Python GUI development.
