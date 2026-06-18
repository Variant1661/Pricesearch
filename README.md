# Lowest Price Finder

A simple Streamlit app to search for product prices online and sort them from lowest to highest.

## What it does

- Takes a product name or model number
- Searches Google Shopping through SerpApi
- Extracts product title, seller, price, rating, reviews, delivery info, and link
- Sorts by lowest price or estimated total
- Exports results to CSV

## Why this approach

Directly scraping Amazon, Currys, Argos, eBay, etc. is fragile and can breach website terms. This MVP uses a search/shopping API, which is more stable and safer.

## Setup

1. Install Python 3.10+
2. Install requirements:

```bash
pip install -r requirements.txt
```

3. Get a SerpApi key and set it:

Windows PowerShell:

```powershell
$env:SERPAPI_KEY="your_api_key_here"
```

Mac/Linux:

```bash
export SERPAPI_KEY="your_api_key_here"
```

Or paste the key inside the app sidebar.

4. Run:

```bash
streamlit run app.py
```

## Best search tips

Use exact model names, for example:

- `Sony WH-1000XM5 black`
- `Samsung Galaxy S25 Ultra 256GB`
- `Dyson V15 Detect Absolute`
- `Sony A7 IV body only`

## Next upgrades

- Add barcode / GTIN search
- Add Amazon-only tracking using Keepa API
- Add eBay search API
- Add daily price alerts by email
- Add price history database
- Add retailer whitelist
- Add alert when price drops below your target