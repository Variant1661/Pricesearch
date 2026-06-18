import os
import re
from urllib.parse import urlparse

import pandas as pd
import requests
import streamlit as st


# ------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------
st.set_page_config(
    page_title="Lowest Price Finder",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ------------------------------------------------------
# STYLES
# ------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero {
            padding: 28px 30px;
            border-radius: 24px;
            background: linear-gradient(135deg, #0f172a 0%, #134e4a 100%);
            color: white;
            margin-bottom: 24px;
        }

        .hero-title {
            font-size: 2.6rem;
            font-weight: 900;
            margin-bottom: 8px;
            letter-spacing: -0.04em;
        }

        .hero-subtitle {
            font-size: 1.08rem;
            opacity: 0.9;
            max-width: 760px;
        }

        .deal-card {
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 18px;
            background: #ffffff;
            box-shadow: 0 6px 22px rgba(15, 23, 42, 0.06);
            margin-bottom: 14px;
        }

        .deal-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 8px;
        }

        .deal-seller {
            color: #4b5563;
            font-size: 0.92rem;
            margin-bottom: 8px;
        }

        .deal-price {
            font-size: 1.55rem;
            font-weight: 900;
            color: #0f766e;
            margin-bottom: 8px;
        }

        .deal-meta {
            color: #6b7280;
            font-size: 0.9rem;
            margin-bottom: 12px;
        }

        .deal-button {
            display: inline-block;
            padding: 9px 14px;
            border-radius: 10px;
            background: #0f766e;
            color: white !important;
            text-decoration: none;
            font-weight: 700;
            font-size: 0.9rem;
        }

        .deal-button:hover {
            background: #115e59;
            color: white !important;
        }

        .rank-badge {
            display: inline-block;
            background: #ecfeff;
            color: #155e75;
            border: 1px solid #a5f3fc;
            padding: 4px 9px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 800;
            margin-bottom: 10px;
        }

        .note-box {
            padding: 14px 16px;
            border-radius: 14px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #475569;
            font-size: 0.95rem;
        }

        .footer-note {
            color: #64748b;
            font-size: 0.85rem;
            margin-top: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------------
# SECRETS
# ------------------------------------------------------
def get_serpapi_key():
    try:
        return st.secrets.get("SERPAPI_KEY", os.getenv("SERPAPI_KEY"))
    except Exception:
        return os.getenv("SERPAPI_KEY")


SERPAPI_KEY = get_serpapi_key()


# ------------------------------------------------------
# HEADER
# ------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <div class="hero-title">🛒 Lowest Price Finder</div>
        <div class="hero-subtitle">
            Search a product, compare online prices, and find the cheapest available option.
            Works best with exact model names, storage size, colour, or product codes.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------
with st.sidebar:
    st.header("Search settings")

    country = st.selectbox(
        "Country / Market",
        options=["uk", "us", "in", "ca", "au", "de", "fr"],
        index=0,
        help="Choose the Google Shopping market."
    )

    max_results = st.slider(
        "Maximum results",
        min_value=5,
        max_value=60,
        value=25,
        step=5
    )

    include_delivery = st.checkbox(
        "Include delivery when available",
        value=True
    )

    st.divider()

    if SERPAPI_KEY:
        st.success("API key connected")
    else:
        st.error("API key missing")
        st.caption("Add SERPAPI_KEY in Streamlit Secrets.")

    st.divider()

    st.caption(
        "Tip: Search like `Sony WH-1000XM5 black`, "
        "`iPhone 15 128GB blue`, or `Dyson V15 Detect Absolute`."
    )


# ------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------
def parse_price(value):
    """
    Converts strings like:
    £129.99, $1,299, ₹54,990
    into float values.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)", text)

    if not match:
        return None

    return float(match.group(1))


def get_currency_symbol(price_text):
    if not price_text:
        return ""

    text = str(price_text)

    if "£" in text:
        return "£"
    if "$" in text:
        return "$"
    if "₹" in text:
        return "₹"
    if "€" in text:
        return "€"

    return ""


def get_domain(link):
    if not link:
        return ""

    try:
        return urlparse(link).netloc.replace("www.", "")
    except Exception:
        return ""


def clean_text(value):
    if value is None:
        return ""

    if isinstance(value, list):
        return ", ".join(str(x) for x in value)

    return str(value)


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


def normalise_results(data, include_delivery_cost=True):
    rows = []
    shopping_results = data.get("shopping_results", []) or []

    for item in shopping_results:
        price_text = item.get("price")
        extracted_price = item.get("extracted_price")
        price = extracted_price if extracted_price is not None else parse_price(price_text)

        link = item.get("link") or item.get("product_link")

        delivery_text = (
            item.get("delivery")
            or item.get("shipping")
            or item.get("extensions", "")
        )

        delivery_text = clean_text(delivery_text)

        delivery_cost = None

        if delivery_text:
            if "free" in delivery_text.lower():
                delivery_cost = 0.0
            else:
                delivery_cost = parse_price(delivery_text)

        estimated_total = price

        if include_delivery_cost and price is not None and delivery_cost is not None:
            estimated_total = price + delivery_cost

        rows.append(
            {
                "Product": item.get("title", ""),
                "Seller": item.get("source", "") or get_domain(link),
                "Price": price,
                "Displayed price": price_text,
                "Currency": get_currency_symbol(price_text),
                "Delivery info": delivery_text,
                "Estimated total": estimated_total,
                "Rating": item.get("rating"),
                "Reviews": item.get("reviews"),
                "Link": link,
                "Thumbnail": item.get("thumbnail"),
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df = df.dropna(subset=["Price"])

    if df.empty:
        return df

    sort_col = "Estimated total" if include_delivery_cost else "Price"
    df = df.sort_values(by=sort_col, ascending=True).reset_index(drop=True)

    return df


def safe_link(link):
    if not link:
        return "#"
    return link


def format_rating(row):
    parts = []

    if pd.notna(row.get("Rating")):
        parts.append(f"⭐ {row.get('Rating')}")

    if pd.notna(row.get("Reviews")):
        parts.append(f"{int(row.get('Reviews')):,} reviews")

    return " | ".join(parts) if parts else "Rating not shown"


# ------------------------------------------------------
# SEARCH UI
# ------------------------------------------------------
search_col, button_col = st.columns([5, 1.3])

with search_col:
    product = st.text_input(
        "What product are you searching for?",
        placeholder="Example: Sony WH-1000XM5 black"
    )

with button_col:
    st.write("")
    st.write("")
    search_clicked = st.button(
        "Search",
        type="primary",
        use_container_width=True
    )


st.markdown(
    """
    <div class="note-box">
        This tool uses Google Shopping data through SerpApi. 
        Always confirm the final price, delivery cost, warranty, and seller reliability before buying.
    </div>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------------
# MAIN APP LOGIC
# ------------------------------------------------------
if search_clicked:
    if not product.strip():
        st.error("Please enter a product name first.")

    elif not SERPAPI_KEY:
        st.error("SerpApi API key is missing. Add SERPAPI_KEY in Streamlit Secrets and reboot the app.")

    else:
        with st.spinner("Searching prices online..."):
            try:
                raw_data = search_google_shopping(
                    query=product.strip(),
                    country_code=country,
                    api_key=SERPAPI_KEY
                )

                df = normalise_results(
                    data=raw_data,
                    include_delivery_cost=include_delivery
                )

                if df.empty:
                    st.warning(
                        "No prices found. Try a more specific search, for example model number, colour, size, or storage."
                    )

                else:
                    df = df.head(max_results).copy()
                    cheapest = df.iloc[0]

                    st.divider()

                    # Summary cards
                    metric_1, metric_2, metric_3, metric_4 = st.columns(4)

                    with metric_1:
                        st.metric("Lowest price", cheapest["Displayed price"])

                    with metric_2:
                        st.metric("Cheapest seller", cheapest["Seller"])

                    with metric_3:
                        st.metric("Results shown", len(df))

                    with metric_4:
                        average_price = df["Price"].mean()
                        currency = cheapest.get("Currency", "")
                        st.metric("Average price", f"{currency}{average_price:,.2f}")

                    # Best deal
                    st.subheader("Best deal found")

                    st.markdown(
                        f"""
                        <div class="deal-card">
                            <div class="rank-badge">Best price</div>
                            <div class="deal-title">{cheapest["Product"]}</div>
                            <div class="deal-seller">Seller: {cheapest["Seller"]}</div>
                            <div class="deal-price">{cheapest["Displayed price"]}</div>
                            <div class="deal-meta">
                                Delivery: {cheapest["Delivery info"] or "Not shown"}<br>
                                {format_rating(cheapest)}
                            </div>
                            <a class="deal-button" href="{safe_link(cheapest["Link"])}" target="_blank">
                                Open product
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Results table
                    st.subheader("Price comparison table")

                    display_df = df[
                        [
                            "Product",
                            "Seller",
                            "Displayed price",
                            "Delivery info",
                            "Estimated total",
                            "Rating",
                            "Reviews",
                            "Link",
                        ]
                    ].copy()

                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Product": st.column_config.TextColumn("Product", width="large"),
                            "Seller": st.column_config.TextColumn("Seller", width="medium"),
                            "Displayed price": st.column_config.TextColumn("Price", width="small"),
                            "Delivery info": st.column_config.TextColumn("Delivery", width="medium"),
                            "Estimated total": st.column_config.NumberColumn(
                                "Estimated total",
                                format="%.2f"
                            ),
                            "Rating": st.column_config.NumberColumn("Rating", format="%.1f"),
                            "Reviews": st.column_config.NumberColumn("Reviews", format="%d"),
                            "Link": st.column_config.LinkColumn("Open"),
                        }
                    )

                    csv = df.to_csv(index=False).encode("utf-8")

                    st.download_button(
                        "Download results as CSV",
                        data=csv,
                        file_name="lowest_price_results.csv",
                        mime="text/csv"
                    )

                    # Top 5 cards
                    st.subheader("Top cheapest options")

                    for position, (_, row) in enumerate(df.head(5).iterrows(), start=1):
                        st.markdown(
                            f"""
                            <div class="deal-card">
                                <div class="rank-badge">#{position} cheapest</div>
                                <div class="deal-title">{row["Product"]}</div>
                                <div class="deal-seller">Seller: {row["Seller"]}</div>
                                <div class="deal-price">{row["Displayed price"]}</div>
                                <div class="deal-meta">
                                    Delivery: {row["Delivery info"] or "Not shown"}<br>
                                    {format_rating(row)}
                                </div>
                                <a class="deal-button" href="{safe_link(row["Link"])}" target="_blank">
                                    View deal
                                </a>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    st.markdown(
                        """
                        <div class="footer-note">
                            Price results are based on available shopping data at the time of search.
                            The cheapest result is not always the best option. Check seller reputation, warranty,
                            returns policy, and delivery cost before purchasing.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            except requests.HTTPError as e:
                st.error(f"API error: {e}")

            except requests.Timeout:
                st.error("The search timed out. Try again in a few seconds.")

            except Exception as e:
                st.error(f"Something went wrong: {e}")
