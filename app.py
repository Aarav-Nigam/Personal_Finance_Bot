import io

import pandas as pd
import streamlit as st

from config.settings import settings

st.set_page_config(
    page_title="PersonalFinanceBot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "holdings_df" not in st.session_state:
    st.session_state.holdings_df = None
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = settings.LLM_PROVIDER
if "kite_connected" not in st.session_state:
    st.session_state.kite_connected = False

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("📊 PersonalFinanceBot")
st.sidebar.caption("v0.1.0 — Free & Open Source")


def _parse_csv(uploaded_file) -> pd.DataFrame:
    raw = pd.read_csv(io.BytesIO(uploaded_file.getvalue()))
    cols_lower = {c: c.lower().strip() for c in raw.columns}
    raw = raw.rename(columns=cols_lower)

    col_map = {}
    for c in raw.columns:
        if "instrument" in c or "symbol" in c or "trading" in c:
            col_map["tradingsymbol"] = c
        elif c in ("qty", "quantity"):
            col_map["quantity"] = c
        elif "avg" in c and ("cost" in c or "price" in c):
            col_map["average_price"] = c
        elif c in ("ltp", "last_price", "cur. val"):
            col_map["last_price"] = c

    df = pd.DataFrame()
    df["tradingsymbol"] = raw[col_map.get("tradingsymbol", raw.columns[0])].astype(str)
    df["quantity"] = pd.to_numeric(raw[col_map.get("quantity", raw.columns[1])], errors="coerce")
    df["average_price"] = pd.to_numeric(
        raw[col_map.get("average_price", raw.columns[2])], errors="coerce"
    )
    if "last_price" in col_map:
        df["last_price"] = pd.to_numeric(raw[col_map["last_price"]], errors="coerce")
    else:
        df["last_price"] = df["average_price"]
    df = df.dropna(subset=["quantity", "average_price"])
    if "instrument_type" not in df.columns:
        df["instrument_type"] = "EQ"
    return df


if st.session_state.holdings_df is None:
    try:
        from analytics.portfolio import load_holdings

        df = load_holdings()
        if not df.empty:
            st.session_state.holdings_df = df
            st.session_state.kite_connected = True
    except Exception:
        st.session_state.kite_connected = False

if not st.session_state.kite_connected:
    st.sidebar.warning("Kite not connected. Upload a CSV or run `python scripts/kite_auth.py`.")
    uploaded = st.sidebar.file_uploader("Upload holdings CSV", type=["csv"])
    if uploaded is not None:
        st.session_state.holdings_df = _parse_csv(uploaded)
else:
    st.sidebar.success("Connected to Kite")

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
pg = st.navigation(
    {
        "": [
            st.Page("home.py", title="Home", icon="🏠", default=True),
        ],
        "Analysis": [
            st.Page("pages/1_Portfolio.py", title="Portfolio", icon="💼"),
            st.Page("pages/2_Stocks.py", title="Stock Analysis", icon="📈"),
            st.Page("pages/3_Mutual_Funds.py", title="Mutual Funds", icon="📊"),
            st.Page("pages/4_Signals.py", title="Signals", icon="🔔"),
        ],
        "Tools": [
            st.Page("pages/5_Tax.py", title="Tax Calculator", icon="🧾"),
            st.Page("pages/6_AI_Advisor.py", title="AI Advisor", icon="🤖"),
        ],
        "Account": [
            st.Page("pages/7_Positions.py", title="Positions & Orders", icon="📋"),
            st.Page("pages/8_Account.py", title="Account & Funds", icon="👤"),
        ],
    }
)

pg.run()
