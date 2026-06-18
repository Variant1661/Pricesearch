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
    initial_sidebar_state="expanded",
)


# ------------------------------------------------------
# CSS
# ------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero {
            padding: 30px;
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
            opacity: 0.92;
            max-width: 850px;
        }

        .note-box {
            padding: 14px 16px;
            border-radius: 14px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #475569;
            font-size: 0.95rem;
            margin-top: 12px;
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
            font-size: 1.5rem;
            font-weight: 900;
            color: #0f766e;
            margin-bottom: 8px;
        }

        .deal-meta {
            color: #6b7280;
            font-size: 0.9rem;
            line-height: 1.6;
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

        .contract-badge {
            display: inline-block;
            background: #fff7ed;
            color: #9a3412;
            border: 1px solid #fed7aa;
            padding: 4px 9px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 800;
            margin-left: 6px;
            margin-bottom: 10px;
        }

        .outright-badge {
            display: inline-block;
            background: #f0fdf4;
            color: #166534;
            border: 1px solid #bbf7d0;
            padding: 4px 9px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 800;
            margin-left: 6px;
            margin-bottom: 10px;
        }

        .footer-note {
            color: #64748b;
            font-size: 0.85rem;
            margin-top: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------
# API KEY
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
            Search products, compare outright prices and contract deals, and sort by the real estimated total cost.
            Best for phones, electronics, appliances, and other items that may be sold upfront or on monthly plans.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
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
        help="Choose the Google Shopping market.",
    )

    max_results = st.slider(
        "Maximum results",
        min_value=5,
        max_value=60,
        value=25,
        step=5,
    )

    include_delivery = st.checkbox(
        "Include delivery when available",
        value=True,
    )

    show_outright = st.checkbox(
        "Show outright purchases",
        value=True,
    )

    show_contracts = st.checkbox(
        "Show contracts / subscriptions",
        value=True,
    )

    sort_mode = st.selectbox(
        "Sort by",
        options=[
            "Estimated total cost",
            "Displayed upfront price",
            "Monthly cost",
        ],
        index=0,
    )

    st.divider()

    if SERPAPI_KEY:
        st.success("API key connected")
    else:
        st.error("API key missing")
        st.caption("Add SERPAPI_KEY in Streamlit Secrets.")

    st.divider()

    st.caption(
        "For phones, try: `iPhone 17 Pro Max 1TB unlocked`, "
        "`Samsung S25 Ultra 256GB contract`, or `iPhone 16 Pro 256GB SIM free`."
    )


# ------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------
def parse_price(value):
    """
    Converts strings like:
    £129.99, $1,299, ₹54,990, €899
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
        return "£"

    text = str(price_text)

    if "£" in text:
        return "£"
    if "$" in text:
        return "$"
    if "₹" in text:
        return "₹"
    if "€" in text:
        return "€"

    return "£"


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


def money(value, currency="£"):
    if value is None or pd.isna(value):
        return "Not shown"

    return f"{currency}{value:,.2f}"


def safe_link(link):
    if not link:
        return "#"

    return link


def format_rating(row):
    parts = []

    rating = row.get("Rating")
    reviews = row.get("Reviews")

    if pd.notna(rating):
        parts.append(f"⭐ {rating}")

    if pd.notna(reviews):
        try:
            parts.append(f"{int(reviews):,} reviews")
        except Exception:
            parts.append(f"{reviews} reviews")

    return " | ".join(parts) if parts else "Rating not shown"


def detect_contract_details(text):
    """
    Detects contract/subscription style offers.

    Examples:
    - £9 now, £130.20 per month, 12 months
    - £0 upfront, £45/mo, 24 months
    - Monthly payment £35.99, duration 36 months
    """

    original_text = str(text)
    text = original_text.lower().replace(",", "")

    contract_keywords = [
        "per month",
        "/mo",
        "pm",
        "monthly",
        "contract",
        "12 months",
        "24 months",
        "36 months",
        "sim",
        "data",
        "airtime",
        "upfront",
        "£0 now",
        "£0.00 now",
        "today's payment",
        "base price",
        "duration",
    ]

    is_contract = any(keyword in text for keyword in contract_keywords)

    upfront_cost = None
    monthly_cost = None
    duration_months = None

    # Upfront / today / now price
    upfront_patterns = [
        r"£\s*(\d+(?:\.\d+)?)\s*now",
        r"£\s*(\d+(?:\.\d+)?)\s*today",
        r"£\s*(\d+(?:\.\d+)?)\s*upfront",
        r"upfront\s*£\s*(\d+(?:\.\d+)?)",
        r"base price\s*£\s*(\d+(?:\.\d+)?)",
        r"today's payment\s*£\s*(\d+(?:\.\d+)?)",
        r"today’s payment\s*£\s*(\d+(?:\.\d+)?)",
    ]

    for pattern in upfront_patterns:
        match = re.search(pattern, text)
        if match:
            upfront_cost = float(match.group(1))
            break

    # Monthly payment
    monthly_patterns = [
        r"£\s*(\d+(?:\.\d+)?)\s*(?:per month|/mo|pm)",
        r"£\s*(\d+(?:\.\d+)?)\s*/\s*month",
        r"monthly payment\s*£\s*(\d+(?:\.\d+)?)",
        r"£\s*(\d+(?:\.\d+)?)\s*monthly",
    ]

    for pattern in monthly_patterns:
        match = re.search(pattern, text)
        if match:
            monthly_cost = float(match.group(1))
            break

    # Duration
    duration_patterns = [
        r"duration\s*(\d+)\s*months",
        r"(\d+)\s*months",
        r"(\d+)\s*month",
    ]

    for pattern in duration_patterns:
        match = re.search(pattern, text)
        if match:
            possible_duration = int(match.group(1))
            if possible_duration in [1, 3, 6, 12, 18, 24, 30, 36, 48, 60]:
                duration_months = possible_duration
                break

    estimated_contract_total = None

    if monthly_cost is not None and duration_months is not None:
        estimated_contract_total = monthly_cost * duration_months

        if upfront_cost is not None:
            estimated_contract_total += upfront_cost

    return {
        "Is contract": is_contract,
        "Upfront cost": upfront_cost,
        "Monthly cost": monthly_cost,
        "Duration months": duration_months,
        "Estimated contract total": estimated_contract_total,
    }


def classify_offer_type(contract_info):
    if contract_info.get("Is contract"):
        return "Contract / subscription"

    return "Outright purchase"


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
        title = item.get("title", "")
        price_text = item.get("price", "")
        extracted_price = item.get("extracted_price")
        source = item.get("source", "")

        link = item.get("link") or item.get("product_link")

        delivery_text = (
            item.get("delivery")
            or item.get("shipping")
            or item.get("extensions", "")
        )

        delivery_text = clean_text(delivery_text)

        full_text = f"{title} {price_text} {source} {delivery_text} {item}"

        contract_info = detect_contract_details(full_text)
        offer_type = classify_offer_type(contract_info)

        price = extracted_price if extracted_price is not None else parse_price(price_text)
        currency = get_currency_symbol(price_text)

        delivery_cost = None

        if delivery_text:
            if "free" in delivery_text.lower():
                delivery_cost = 0.0
            else:
                delivery_cost = parse_price(delivery_text)

        if contract_info["Estimated contract total"] is not None:
            estimated_total = contract_info["Estimated contract total"]
        else:
            estimated_total = price

            if include_delivery_cost and price is not None and delivery_cost is not None:
                estimated_total = price + delivery_cost

        # If contract but total cannot be calculated, keep displayed price but mark as incomplete
        contract_total_complete = contract_info["Estimated contract total"] is not None

        rows.append(
            {
                "Product": title,
                "Seller": source or get_domain(link),
                "Offer type": offer_type,
                "Displayed price": price_text,
                "Price": price,
                "Upfront cost": contract_info["Upfront cost"],
                "Monthly cost": contract_info["Monthly cost"],
                "Duration months": contract_info["Duration months"],
                "Estimated total": estimated_total,
                "Contract total complete": contract_total_complete,
                "Delivery info": delivery_text,
                "Rating": item.get("rating"),
                "Reviews": item.get("reviews"),
                "Link": link,
                "Thumbnail": item.get("thumbnail"),
                "Currency": currency,
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df = df.dropna(subset=["Estimated total"])

    if df.empty:
        return df

    return df.reset_index(drop=True)


def sort_results(df, sort_choice):
    if df.empty:
        return df

    if sort_choice == "Displayed upfront price":
        return df.sort_values(by="Price", ascending=True, na_position="last").reset_index(drop=True)

    if sort_choice == "Monthly cost":
        return df.sort_values(by="Monthly cost", ascending=True, na_position="last").reset_index(drop=True)

    return df.sort_values(by="Estimated total", ascending=True, na_position="last").reset_index(drop=True)


def offer_badge(offer_type):
    if offer_type == "Contract / subscription":
        return '<span class="contract-badge">Contract / subscription</span>'

    return '<span class="outright-badge">Outright purchase</span>'


# ------------------------------------------------------
# SEARCH UI
# ------------------------------------------------------
search_col, button_col = st.columns([5, 1.3])

with search_col:
    product = st.text_input(
        "What product are you searching for?",
        placeholder="Example: iPhone 17 Pro Max 1TB, Sony WH-1000XM5, Dyson V15",
    )

with button_col:
    st.write("")
    st.write("")
    search_clicked = st.button(
        "Search",
        type="primary",
        use_container_width=True,
    )


st.markdown(
    """
    <div class="note-box">
        This tool uses Google Shopping data through SerpApi. 
        It shows both outright purchase prices and contract/subscription offers where available.
        For contracts, compare the estimated total cost, not only the upfront price.
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------
# MAIN APP LOGIC
# ------------------------------------------------------
if search_clicked:
    if not product.strip():
        st.error("Please enter a product name first.")

    elif not SERPAPI_KEY:
        st.error("SerpApi API key is missing. Add SERPAPI_KEY in Streamlit Secrets and reboot the app.")

    elif not show_outright and not show_contracts:
        st.error("Please select at least one offer type: outright purchases or contracts.")

    else:
        with st.spinner("Searching prices online..."):
            try:
                raw_data = search_google_shopping(
                    query=product.strip(),
                    country_code=country,
                    api_key=SERPAPI_KEY,
                )

                df = normalise_results(
                    data=raw_data,
                    include_delivery_cost=include_delivery,
                )

                if df.empty:
                    st.warning(
                        "No prices found. Try a more specific search, such as model number, colour, size, storage, or SIM-free/contract."
                    )

                else:
                    if not show_outright:
                        df = df[df["Offer type"] != "Outright purchase"]

                    if not show_contracts:
                        df = df[df["Offer type"] != "Contract / subscription"]

                    if df.empty:
                        st.warning("No results found for the selected offer type filters.")

                    else:
                        df = sort_results(df, sort_mode)
                        df = df.head(max_results).copy()
                        best = df.iloc[0]
                        currency = best.get("Currency", "£")

                        st.divider()

                        # ------------------------------------------------------
                        # METRICS
                        # ------------------------------------------------------
                        metric_1, metric_2, metric_3, metric_4 = st.columns(4)

                        with metric_1:
                            st.metric(
                                "Lowest estimated total",
                                money(best["Estimated total"], currency),
                            )

                        with metric_2:
                            st.metric("Seller", best["Seller"])

                        with metric_3:
                            st.metric("Offer type", best["Offer type"])

                        with metric_4:
                            average_total = df["Estimated total"].mean()
                            st.metric("Average estimated total", money(average_total, currency))

                        if best["Offer type"] == "Contract / subscription" and not best["Contract total complete"]:
                            st.warning(
                                "The best result appears to be a contract, but the app could not fully detect monthly cost or duration. Open the product page before comparing."
                            )

                        # ------------------------------------------------------
                        # BEST DEAL CARD
                        # ------------------------------------------------------
                        st.subheader("Best result found")

                        if best["Offer type"] == "Contract / subscription":
                            main_price_line = f"Estimated total: {money(best['Estimated total'], currency)}"
                            extra_lines = f"""
                                Upfront: {money(best['Upfront cost'], currency)}<br>
                                Monthly: {money(best['Monthly cost'], currency)}<br>
                                Duration: {int(best['Duration months']) if pd.notna(best['Duration months']) else 'Not shown'} months<br>
                            """
                        else:
                            main_price_line = f"Price: {best['Displayed price']}"
                            extra_lines = f"""
                                Delivery: {best['Delivery info'] or 'Not shown'}<br>
                            """

                        st.markdown(
                            f"""
                            <div class="deal-card">
                                <div>
                                    <span class="rank-badge">Best match</span>
                                    {offer_badge(best["Offer type"])}
                                </div>
                                <div class="deal-title">{best["Product"]}</div>
                                <div class="deal-seller">Seller: {best["Seller"]}</div>
                                <div class="deal-price">{main_price_line}</div>
                                <div class="deal-meta">
                                    Displayed price: {best["Displayed price"]}<br>
                                    {extra_lines}
                                    {format_rating(best)}
                                </div>
                                <a class="deal-button" href="{safe_link(best["Link"])}" target="_blank">
                                    Open product
                                </a>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # ------------------------------------------------------
                        # TABLE
                        # ------------------------------------------------------
                        st.subheader("Price comparison table")

                        display_df = df[
                            [
                                "Product",
                                "Seller",
                                "Offer type",
                                "Displayed price",
                                "Upfront cost",
                                "Monthly cost",
                                "Duration months",
                                "Estimated total",
                                "Delivery info",
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
                                "Offer type": st.column_config.TextColumn("Offer type", width="medium"),
                                "Displayed price": st.column_config.TextColumn("Displayed price", width="small"),
                                "Upfront cost": st.column_config.NumberColumn("Upfront", format="£%.2f"),
                                "Monthly cost": st.column_config.NumberColumn("Monthly", format="£%.2f"),
                                "Duration months": st.column_config.NumberColumn("Months", format="%d"),
                                "Estimated total": st.column_config.NumberColumn("Estimated total", format="£%.2f"),
                                "Delivery info": st.column_config.TextColumn("Delivery", width="medium"),
                                "Rating": st.column_config.NumberColumn("Rating", format="%.1f"),
                                "Reviews": st.column_config.NumberColumn("Reviews", format="%d"),
                                "Link": st.column_config.LinkColumn("Open"),
                            },
                        )

                        csv = df.to_csv(index=False).encode("utf-8")

                        st.download_button(
                            "Download results as CSV",
                            data=csv,
                            file_name="lowest_price_results.csv",
                            mime="text/csv",
                        )

                        # ------------------------------------------------------
                        # TOP CARDS
                        # ------------------------------------------------------
                        st.subheader("Top cheapest options")

                        for position, (_, row) in enumerate(df.head(5).iterrows(), start=1):
                            row_currency = row.get("Currency", currency)

                            if row["Offer type"] == "Contract / subscription":
                                row_price_line = f"Estimated total: {money(row['Estimated total'], row_currency)}"
                                row_extra = f"""
                                    Upfront: {money(row['Upfront cost'], row_currency)}<br>
                                    Monthly: {money(row['Monthly cost'], row_currency)}<br>
                                    Duration: {int(row['Duration months']) if pd.notna(row['Duration months']) else 'Not shown'} months<br>
                                """
                            else:
                                row_price_line = f"Price: {row['Displayed price']}"
                                row_extra = f"""
                                    Delivery: {row['Delivery info'] or 'Not shown'}<br>
                                """

                            st.markdown(
                                f"""
                                <div class="deal-card">
                                    <div>
                                        <span class="rank-badge">#{position}</span>
                                        {offer_badge(row["Offer type"])}
                                    </div>
                                    <div class="deal-title">{row["Product"]}</div>
                                    <div class="deal-seller">Seller: {row["Seller"]}</div>
                                    <div class="deal-price">{row_price_line}</div>
                                    <div class="deal-meta">
                                        Displayed price: {row["Displayed price"]}<br>
                                        {row_extra}
                                        {format_rating(row)}
                                    </div>
                                    <a class="deal-button" href="{safe_link(row["Link"])}" target="_blank">
                                        View deal
                                    </a>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        st.markdown(
                            """
                            <div class="footer-note">
                                Contract results are estimated from available shopping text. Always check the final checkout page,
                                total payable, delivery, warranty, returns policy, and whether the product is new, used, refurbished,
                                locked, unlocked, SIM-free, or bundled with airtime.
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            except requests.HTTPError as e:
                st.error(f"API error: {e}")

            except requests.Timeout:
                st.error("The search timed out. Try again in a few seconds.")

            except Exception as e:
                st.error(f"Something went wrong: {e}")
