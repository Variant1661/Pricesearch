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
    page_title="PriceSearch",
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
            padding-top: 1.6rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        .hero {
            padding: 28px 30px;
            border-radius: 26px;
            background: linear-gradient(135deg, #111827 0%, #0f766e 100%);
            color: white;
            margin-bottom: 24px;
            box-shadow: 0 14px 40px rgba(15, 23, 42, 0.20);
        }

        .hero-title {
            font-size: 2.5rem;
            font-weight: 900;
            letter-spacing: -0.04em;
            margin-bottom: 6px;
        }

        .hero-subtitle {
            font-size: 1rem;
            opacity: 0.88;
            max-width: 780px;
        }

        .search-card {
            padding: 20px;
            border: 1px solid #e5e7eb;
            border-radius: 22px;
            background: #ffffff;
            box-shadow: 0 8px 28px rgba(15, 23, 42, 0.06);
            margin-bottom: 22px;
        }

        .deal-card {
            border: 1px solid #e5e7eb;
            border-radius: 22px;
            padding: 20px;
            background: #ffffff;
            box-shadow: 0 8px 26px rgba(15, 23, 42, 0.06);
            margin-bottom: 16px;
        }

        .deal-card:hover {
            box-shadow: 0 12px 34px rgba(15, 23, 42, 0.10);
            transform: translateY(-1px);
            transition: 0.15s ease-in-out;
        }

        .deal-title {
            font-size: 1.05rem;
            font-weight: 850;
            color: #111827;
            margin-top: 8px;
            margin-bottom: 10px;
            line-height: 1.35;
        }

        .deal-seller {
            color: #4b5563;
            font-size: 0.92rem;
            margin-bottom: 10px;
        }

        .deal-price {
            font-size: 1.65rem;
            font-weight: 950;
            color: #0f766e;
            margin-bottom: 10px;
            letter-spacing: -0.02em;
        }

        .deal-meta {
            color: #64748b;
            font-size: 0.92rem;
            line-height: 1.7;
            margin-bottom: 14px;
        }

        .deal-button {
            display: inline-block;
            padding: 10px 15px;
            border-radius: 12px;
            background: #0f766e;
            color: white !important;
            text-decoration: none;
            font-weight: 750;
            font-size: 0.9rem;
        }

        .deal-button:hover {
            background: #115e59;
            color: white !important;
        }

        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 999px;
            font-size: 0.76rem;
            font-weight: 850;
            margin-right: 6px;
            margin-bottom: 6px;
        }

        .badge-rank {
            background: #ecfeff;
            color: #155e75;
            border: 1px solid #a5f3fc;
        }

        .badge-contract {
            background: #fff7ed;
            color: #9a3412;
            border: 1px solid #fed7aa;
        }

        .badge-outright {
            background: #f0fdf4;
            color: #166534;
            border: 1px solid #bbf7d0;
        }

        .badge-new {
            background: #eff6ff;
            color: #1d4ed8;
            border: 1px solid #bfdbfe;
        }

        .badge-refurb {
            background: #fefce8;
            color: #854d0e;
            border: 1px solid #fde68a;
        }

        .badge-used {
            background: #fdf2f8;
            color: #be185d;
            border: 1px solid #fbcfe8;
        }

        .badge-open {
            background: #f5f3ff;
            color: #6d28d9;
            border: 1px solid #ddd6fe;
        }

        .badge-unknown {
            background: #f8fafc;
            color: #475569;
            border: 1px solid #cbd5e1;
        }

        .section-title {
            font-size: 1.45rem;
            font-weight: 900;
            color: #111827;
            margin-top: 10px;
            margin-bottom: 14px;
            letter-spacing: -0.03em;
        }

        .mini-note {
            color: #64748b;
            font-size: 0.86rem;
            margin-top: 8px;
        }

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            padding: 16px 18px;
            border-radius: 18px;
            box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
        }

        .stButton > button {
            border-radius: 14px;
            font-weight: 800;
            height: 3rem;
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
        <div class="hero-title">PriceSearch</div>
        <div class="hero-subtitle">
            Compare outright prices, contracts, refurbished deals and everyday shopping results in one place.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------
with st.sidebar:
    st.header("Filters")

    country = st.selectbox(
        "Market",
        ["uk", "us", "in", "ca", "au", "de", "fr"],
        index=0,
    )

    max_results = st.slider(
        "Results",
        min_value=5,
        max_value=60,
        value=25,
        step=5,
    )

    sort_mode = st.selectbox(
        "Sort by",
        [
            "Estimated total cost",
            "Displayed upfront price",
            "Monthly cost",
        ],
        index=0,
    )

    st.divider()

    offer_types = st.multiselect(
        "Offer type",
        ["Outright purchase", "Contract / subscription"],
        default=["Outright purchase", "Contract / subscription"],
    )

    condition_filter = st.multiselect(
        "Condition",
        [
            "Brand new",
            "Refurbished",
            "Used / pre-owned",
            "Open box",
            "Unknown",
        ],
        default=[
            "Brand new",
            "Refurbished",
            "Used / pre-owned",
            "Open box",
            "Unknown",
        ],
    )

    include_delivery = st.checkbox(
        "Include delivery where detected",
        value=True,
    )

    st.divider()

    if SERPAPI_KEY:
        st.success("API connected")
    else:
        st.error("API key missing")

    st.caption("Use exact model names for better results.")


# ------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------
def parse_price(value):
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
    return link if link else "#"


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

    return " · ".join(parts) if parts else "No rating"


def detect_condition(text):
    text = str(text).lower()

    refurbished_keywords = [
        "refurbished",
        "renewed",
        "reconditioned",
        "certified refurbished",
        "excellent condition",
        "very good condition",
        "good condition",
        "fair condition",
        "grade a",
        "grade b",
        "grade c",
    ]

    used_keywords = [
        "used",
        "pre-owned",
        "pre owned",
        "second hand",
        "previously owned",
    ]

    open_box_keywords = [
        "open box",
        "open-box",
        "opened box",
        "ex display",
        "ex-display",
        "display model",
    ]

    new_keywords = [
        "brand new",
        "new",
        "sealed",
        "unopened",
    ]

    if any(keyword in text for keyword in refurbished_keywords):
        return "Refurbished"

    if any(keyword in text for keyword in used_keywords):
        return "Used / pre-owned"

    if any(keyword in text for keyword in open_box_keywords):
        return "Open box"

    if any(keyword in text for keyword in new_keywords):
        return "Brand new"

    return "Unknown"


def detect_contract_details(text):
    text = str(text).lower().replace(",", "")

    contract_keywords = [
        "per month",
        "/mo",
        "pm",
        "monthly",
        "contract",
        "12 months",
        "18 months",
        "24 months",
        "30 months",
        "36 months",
        "48 months",
        "sim",
        "data",
        "airtime",
        "upfront",
        "£0 now",
        "£0.00 now",
        "today's payment",
        "today’s payment",
        "base price",
        "duration",
    ]

    is_contract = any(keyword in text for keyword in contract_keywords)

    upfront_cost = None
    monthly_cost = None
    duration_months = None

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


def condition_badge(condition):
    badge_class = {
        "Brand new": "badge-new",
        "Refurbished": "badge-refurb",
        "Used / pre-owned": "badge-used",
        "Open box": "badge-open",
        "Unknown": "badge-unknown",
    }.get(condition, "badge-unknown")

    return f'<span class="badge {badge_class}">{condition}</span>'


def offer_badge(offer_type):
    if offer_type == "Contract / subscription":
        return '<span class="badge badge-contract">Contract</span>'

    return '<span class="badge badge-outright">Outright</span>'


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

        condition = detect_condition(full_text)
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

        rows.append(
            {
                "Product": title,
                "Seller": source or get_domain(link),
                "Condition": condition,
                "Offer type": offer_type,
                "Displayed price": price_text,
                "Price": price,
                "Upfront cost": contract_info["Upfront cost"],
                "Monthly cost": contract_info["Monthly cost"],
                "Duration months": contract_info["Duration months"],
                "Estimated total": estimated_total,
                "Contract total complete": contract_info["Estimated contract total"] is not None,
                "Delivery info": delivery_text,
                "Rating": item.get("rating"),
                "Reviews": item.get("reviews"),
                "Link": link,
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


def result_card(row, position=None, best=False):
    currency = row.get("Currency", "£")
    offer_type = row.get("Offer type", "Outright purchase")
    condition = row.get("Condition", "Unknown")

    if offer_type == "Contract / subscription":
        headline = f"Estimated total: {money(row.get('Estimated total'), currency)}"
        details = f"""
            Upfront: {money(row.get('Upfront cost'), currency)} ·
            Monthly: {money(row.get('Monthly cost'), currency)} ·
            {int(row.get('Duration months')) if pd.notna(row.get('Duration months')) else 'Unknown'} months
        """
    else:
        headline = f"Price: {row.get('Displayed price')}"
        details = f"Delivery: {row.get('Delivery info') or 'Not shown'}"

    rank_text = "Best result" if best else f"#{position}"

    return f"""
        <div class="deal-card">
            <div>
                <span class="badge badge-rank">{rank_text}</span>
                {offer_badge(offer_type)}
                {condition_badge(condition)}
            </div>
            <div class="deal-title">{row.get('Product')}</div>
            <div class="deal-seller">Seller: {row.get('Seller')}</div>
            <div class="deal-price">{headline}</div>
            <div class="deal-meta">
                {details}<br>
                Displayed: {row.get('Displayed price')}<br>
                {format_rating(row)}
            </div>
            <a class="deal-button" href="{safe_link(row.get('Link'))}" target="_blank">
                Open deal
            </a>
        </div>
    """


# ------------------------------------------------------
# SEARCH UI
# ------------------------------------------------------
st.markdown('<div class="search-card">', unsafe_allow_html=True)

search_col, button_col = st.columns([5, 1.2])

with search_col:
    product = st.text_input(
        "Search product",
        placeholder="Example: iPhone 17 Pro Max 1TB, Sony WH-1000XM5, Dyson V15",
        label_visibility="collapsed",
    )

with button_col:
    search_clicked = st.button(
        "Search",
        type="primary",
        use_container_width=True,
    )

st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------------------
# MAIN APP LOGIC
# ------------------------------------------------------
if search_clicked:
    if not product.strip():
        st.error("Enter a product name.")

    elif not SERPAPI_KEY:
        st.error("API key missing. Add SERPAPI_KEY in Streamlit Secrets.")

    elif not offer_types:
        st.error("Select at least one offer type.")

    elif not condition_filter:
        st.error("Select at least one condition.")

    else:
        with st.spinner("Searching deals..."):
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
                    st.warning("No results found. Try a more specific model name.")

                else:
                    df = df[df["Offer type"].isin(offer_types)]
                    df = df[df["Condition"].isin(condition_filter)]

                    if df.empty:
                        st.warning("No results match your filters.")

                    else:
                        df = sort_results(df, sort_mode)
                        df = df.head(max_results).copy()

                        best = df.iloc[0]
                        currency = best.get("Currency", "£")

                        st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)

                        m1, m2, m3, m4 = st.columns(4)

                        with m1:
                            st.metric("Best total", money(best["Estimated total"], currency))

                        with m2:
                            st.metric("Seller", best["Seller"])

                        with m3:
                            st.metric("Type", best["Offer type"].replace(" / subscription", ""))

                        with m4:
                            st.metric("Condition", best["Condition"])

                        st.markdown('<div class="section-title">Best result</div>', unsafe_allow_html=True)
                        st.markdown(result_card(best, best=True), unsafe_allow_html=True)

                        st.markdown('<div class="section-title">Compare prices</div>', unsafe_allow_html=True)

                        display_df = df[
                            [
                                "Product",
                                "Seller",
                                "Condition",
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
                                "Condition": st.column_config.TextColumn("Condition", width="small"),
                                "Offer type": st.column_config.TextColumn("Type", width="medium"),
                                "Displayed price": st.column_config.TextColumn("Displayed", width="small"),
                                "Upfront cost": st.column_config.NumberColumn("Upfront", format="£%.2f"),
                                "Monthly cost": st.column_config.NumberColumn("Monthly", format="£%.2f"),
                                "Duration months": st.column_config.NumberColumn("Months", format="%d"),
                                "Estimated total": st.column_config.NumberColumn("Est. total", format="£%.2f"),
                                "Delivery info": st.column_config.TextColumn("Delivery", width="medium"),
                                "Rating": st.column_config.NumberColumn("Rating", format="%.1f"),
                                "Reviews": st.column_config.NumberColumn("Reviews", format="%d"),
                                "Link": st.column_config.LinkColumn("Open"),
                            },
                        )

                        csv = df.to_csv(index=False).encode("utf-8")

                        st.download_button(
                            "Download CSV",
                            data=csv,
                            file_name="pricesearch_results.csv",
                            mime="text/csv",
                        )

                        st.markdown('<div class="section-title">Top deals</div>', unsafe_allow_html=True)

                        for position, (_, row) in enumerate(df.head(6).iterrows(), start=1):
                            st.markdown(
                                result_card(row, position=position),
                                unsafe_allow_html=True,
                            )

                        st.markdown(
                            """
                            <div class="mini-note">
                                Always check the retailer page before buying. Contract totals are estimated from available shopping data.
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            except requests.HTTPError as e:
                st.error(f"API error: {e}")

            except requests.Timeout:
                st.error("Search timed out. Try again.")

            except Exception as e:
                st.error(f"Something went wrong: {e}")
