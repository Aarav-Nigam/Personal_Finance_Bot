from __future__ import annotations

import plotly.graph_objects as go

COLORS = {
    "profit": "#00C853",
    "loss": "#FF1744",
    "primary": "#1E88E5",
    "accent": "#FF9800",
    "card_bg": "#F8F9FA",
    "muted": "#9E9E9E",
    "text": "#212121",
    "bg": "#FFFFFF",
    "border": "#E0E0E0",
    "strong_buy": "#1B5E20",
    "buy": "#2E7D32",
    "hold": "#F9A825",
    "sell": "#E65100",
    "strong_sell": "#B71C1C",
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
            "#7C4DFF",
            "#00BCD4",
            "#8D6E63",
            "#EC407A",
        ],
        xaxis=dict(gridcolor="#EEEEEE", zeroline=False),
        yaxis=dict(gridcolor="#EEEEEE", zeroline=False),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=COLORS["border"],
            borderwidth=1,
        ),
    )
)


def apply_plotly_defaults(fig: go.Figure) -> go.Figure:
    fig.update_layout(template=PLOTLY_TEMPLATE)
    return fig
