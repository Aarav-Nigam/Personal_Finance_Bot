from __future__ import annotations

import plotly.graph_objects as go

COLORS = {
    "profit": "#00E676",
    "loss": "#FF5252",
    "primary": "#42A5F5",
    "accent": "#FFB74D",
    "card_bg": "#1A1D23",
    "muted": "#9E9E9E",
    "text": "#E0E0E0",
    "bg": "#0E1117",
    "border": "#2D3139",
    "strong_buy": "#00E676",
    "buy": "#66BB6A",
    "hold": "#FFD54F",
    "sell": "#FF7043",
    "strong_sell": "#FF5252",
}

SIGNAL_COLORS = {
    "Strong Buy": COLORS["strong_buy"],
    "Buy": COLORS["buy"],
    "Hold": COLORS["hold"],
    "Sell": COLORS["sell"],
    "Strong Sell": COLORS["strong_sell"],
}

PLOTLY_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(family="Inter, -apple-system, sans-serif", size=13, color=COLORS["text"]),
        colorway=[
            COLORS["primary"],
            COLORS["profit"],
            COLORS["accent"],
            COLORS["loss"],
            "#B388FF",
            "#4DD0E1",
            "#A1887F",
            "#F48FB1",
        ],
        xaxis=dict(gridcolor="#2D3139", zeroline=False),
        yaxis=dict(gridcolor="#2D3139", zeroline=False),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(
            bgcolor="rgba(26,29,35,0.9)",
            bordercolor=COLORS["border"],
            borderwidth=1,
            font=dict(color=COLORS["text"]),
        ),
    )
)


def apply_plotly_defaults(fig: go.Figure) -> go.Figure:
    fig.update_layout(template=PLOTLY_TEMPLATE)
    return fig
