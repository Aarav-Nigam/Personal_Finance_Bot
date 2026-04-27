from __future__ import annotations

import streamlit as st

from ui.theme import COLORS, SIGNAL_COLORS

GLOBAL_CSS = (
    """
<style>
/* --- Metric card overrides --- */
div[data-testid="stMetric"] {
    background: %(card_bg)s;
    border-left: 4px solid %(primary)s;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
div[data-testid="stMetric"] label {
    font-size: 0.82rem !important;
    color: %(muted)s !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    font-weight: 700 !important;
}

/* --- Dataframe improvements --- */
div[data-testid="stDataFrame"] table {
    border-collapse: separate;
    border-spacing: 0;
}
div[data-testid="stDataFrame"] thead th {
    background: %(card_bg)s !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    font-size: 0.75rem !important;
    letter-spacing: 0.3px;
}

/* --- Chat bubble styling --- */
div[data-testid="stChatMessage"] {
    border-radius: 12px;
    border: 1px solid %(border)s;
    margin-bottom: 8px;
}

/* --- Sidebar polish --- */
section[data-testid="stSidebar"] {
    border-right: 1px solid %(border)s;
}

/* --- Custom card component --- */
.pfb-card {
    background: %(card_bg)s;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    margin-bottom: 8px;
}
.pfb-card-profit { border-left: 4px solid %(profit)s; }
.pfb-card-loss { border-left: 4px solid %(loss)s; }
.pfb-card-neutral { border-left: 4px solid %(primary)s; }

.pfb-card .card-icon { font-size: 1.3rem; margin-right: 6px; }
.pfb-card .card-label {
    font-size: 0.78rem;
    color: %(muted)s;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
}
.pfb-card .card-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: %(text)s;
    line-height: 1.2;
}
.pfb-card .card-delta {
    font-size: 0.85rem;
    font-weight: 500;
    margin-top: 2px;
}
.pfb-card .delta-positive { color: %(profit)s; }
.pfb-card .delta-negative { color: %(loss)s; }
.pfb-card .delta-neutral { color: %(muted)s; }

/* --- Signal badge --- */
.signal-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
    color: #fff;
    line-height: 1.4;
}

/* --- Status badge --- */
.status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #fff;
}

/* --- Section header --- */
.section-hdr {
    font-size: 1.15rem;
    font-weight: 700;
    color: %(text)s;
    border-bottom: 2px solid %(primary)s;
    padding-bottom: 6px;
    margin-bottom: 16px;
    margin-top: 8px;
}
.section-hdr .hdr-icon { margin-right: 8px; }

/* --- PnL coloring --- */
.pnl-positive { color: %(profit)s; font-weight: 600; }
.pnl-negative { color: %(loss)s; font-weight: 600; }
.pnl-neutral { color: %(muted)s; }

/* --- Tag pills --- */
.tag-pill {
    display: inline-block;
    padding: 2px 10px;
    margin: 2px 4px 2px 0;
    border-radius: 12px;
    background: %(card_bg)s;
    border: 1px solid %(border)s;
    font-size: 0.78rem;
    color: %(text)s;
}
</style>
"""
    % COLORS
)


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def metric_card(
    title: str,
    value: str,
    delta: str | None = None,
    delta_value: float | None = None,
    icon: str | None = None,
):
    if delta_value is not None and delta_value > 0:
        border_cls = "pfb-card-profit"
        delta_cls = "delta-positive"
    elif delta_value is not None and delta_value < 0:
        border_cls = "pfb-card-loss"
        delta_cls = "delta-negative"
    else:
        border_cls = "pfb-card-neutral"
        delta_cls = "delta-neutral"

    icon_html = f'<span class="card-icon">{icon}</span>' if icon else ""
    delta_html = f'<div class="card-delta {delta_cls}">{delta}</div>' if delta else ""

    html = f"""
    <div class="pfb-card {border_cls}">
        <div class="card-label">{icon_html}{title}</div>
        <div class="card-value">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def signal_badge(label: str) -> str:
    color = SIGNAL_COLORS.get(label, COLORS["muted"])
    return f'<span class="signal-badge" style="background:{color}">{label}</span>'


def status_badge(status: str) -> str:
    status_upper = status.upper() if status else ""
    color_map = {
        "COMPLETE": COLORS["profit"],
        "OPEN": COLORS["primary"],
        "PENDING": COLORS["accent"],
        "REJECTED": COLORS["loss"],
        "CANCELLED": COLORS["muted"],
        "TRIGGER PENDING": COLORS["accent"],
    }
    color = color_map.get(status_upper, COLORS["muted"])
    return f'<span class="status-badge" style="background:{color}">{status}</span>'


def section_header(text: str, icon: str | None = None):
    icon_html = f'<span class="hdr-icon">{icon}</span>' if icon else ""
    st.markdown(f'<div class="section-hdr">{icon_html}{text}</div>', unsafe_allow_html=True)


def pnl_colored(value: float, formatted: str) -> str:
    if value > 0:
        cls = "pnl-positive"
    elif value < 0:
        cls = "pnl-negative"
    else:
        cls = "pnl-neutral"
    return f'<span class="{cls}">{formatted}</span>'


def tag_pills(items: list[str]) -> str:
    return " ".join(f'<span class="tag-pill">{item}</span>' for item in items)
