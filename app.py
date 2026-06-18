import os
import re
import requests
import pandas as pd
import streamlit as st
from urllib.parse import urlparse

st.set_page_config(page_title="Lowest Price Finder", page_icon="🛒", layout="wide")

st.title("🛒 Lowest Price Finder")
st.caption("Search a product online, compare prices, and sort from lowest to highest.")

st.warning(
    "Use this responsibly. This MVP uses SerpApi/Google Shopping data instead of scraping retailer websites directly."
)

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

with st.sidebar:
    st.header("Settings")
    api_key_input = st.text_input(
        "SerpApi API Key",
        value=SERPAPI_KEY or "",
        type="password",
        help="Get a key from SerpApi and paste it here, or set SERPAPI_KEY as an environment variable."
    )
    country = st.selectbox(
        "Country / Market",
        ["uk", "us", "in", "ca", "au", "de", "fr"],
        index=0
    )
    max_results = st.slider("Maximum results", min_value=5, max_value=60, value=20, step=5)
    include_delivery = st.checkbox("Try to include delivery cost if available", value=True)

product = st.text_input("Product name", placeholder="Example: Sony WH-1000XM5 headphones")
search = st.button("Find lowest price", type="primary")

def parse_price(value):
    """
    Converts strings like '£129.99', '$1,299', '₹54,990' into float.
    Returns None if no usable number found.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value)
    text = text.replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    return float(match.group(1))

def get_domain(link):
    if not link:
        return ""
    try:
        domain = urlparse(link).netloc.replace("www.", "")
        return domain
    except Exception:
        return ""

def search_google_shopping(query, country_code, api_key):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_shopping",
        "q": query,
        "gl": country_code,
        "hl": "en",
        "api_key": api_key,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def normalise_results(data):
    rows = []
    shopping_results = data.get("shopping_results", []) or []

    for item in shopping_results:
        price_text = item.get("price")
        extracted_price = item.get("extracted_price")
        price = extracted_price if extracted_price is not None else parse_price(price_text)

        delivery_text = (
            item.get("delivery")
            or item.get("shipping")
            or item.get("extensions", [])
        )

        delivery_cost = None
        if isinstance(delivery_text, str):
            if "free" in delivery_text.lower():
                delivery_cost = 0.0
            else:
                delivery_cost = parse_price(delivery_text)

        total_estimated = price
        if include_delivery and price is not None and delivery_cost is not None:
            total_estimated = price + delivery_cost

        rows.append({
            "Product": item.get("title", ""),
            "Seller": item.get("source", "") or get_domain(item.get("link")),
            "Price": price,
            "Displayed price": price_text,
            "Delivery info": delivery_text if isinstance(delivery_text, str) else "",
            "Estimated total": total_estimated,
            "Rating": item.get("rating"),
            "Reviews": item.get("reviews"),
            "Link": item.get("link") or item.get("product_link"),
            "Thumbnail": item.get("thumbnail")
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.dropna(subset=["Price"])
        sort_col = "Estimated total" if include_delivery else "Price"
        df = df.sort_values(by=sort_col, ascending=True)
    return df

if search:
    if not product.strip():
        st.error("Enter a product name first.")
    elif not api_key_input.strip():
        st.error("Add your SerpApi API key in the sidebar.")
    else:
        with st.spinner("Searching prices..."):
            try:
                raw = search_google_shopping(product, country, api_key_input.strip())
                df = normalise_results(raw)

                if df.empty:
                    st.warning("No prices found. Try a more specific product name, model number, or barcode.")
                else:
                    df = df.head(max_results)

                    cheapest = df.iloc[0]
                    st.success(
                        f"Lowest found: {cheapest['Displayed price']} from {cheapest['Seller']}"
                    )

                    st.subheader("Results")
                    display_cols = [
                        "Product", "Seller", "Displayed price", "Delivery info",
                        "Estimated total", "Rating", "Reviews", "Link"
                    ]
                    st.dataframe(
                        df[display_cols],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Link": st.column_config.LinkColumn("Open product"),
                            "Estimated total": st.column_config.NumberColumn(format="%.2f"),
                        }
                    )

                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "Download results as CSV",
                        data=csv,
                        file_name="lowest_price_results.csv",
                        mime="text/csv"
                    )

                    st.subheader("Top 5 cheapest")
                    for _, row in df.head(5).iterrows():
                        st.markdown(
                            f"""
                            **{row['Product']}**  
                            Seller: {row['Seller']}  
                            Price: {row['Displayed price']}  
                            Delivery: {row['Delivery info'] or 'Not shown'}  
                            [Open product]({row['Link']})
                            ---
                            """
                        )

            except requests.HTTPError as e:
                st.error(f"API error: {e}")
            except Exception as e:
                st.error(f"Something went wrong: {e}")