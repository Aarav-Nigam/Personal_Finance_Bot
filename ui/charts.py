from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go

from ui.theme import COLORS, apply_plotly_defaults


def themed_pie(
    names: list,
    values: list,
    title: str,
    hole: float = 0.4,
) -> go.Figure:
    fig = px.pie(names=names, values=values, title=title, hole=hole)
    fig.update_traces(textinfo="label+percent", textposition="outside")
    fig.update_layout(showlegend=False)
    return apply_plotly_defaults(fig)


def themed_bar(
    x: list,
    y: list,
    title: str,
    color: str | None = None,
    horizontal: bool = False,
) -> go.Figure:
    orientation = "h" if horizontal else "v"
    bar_color = color or COLORS["primary"]
    fig = go.Figure(
        go.Bar(
            x=y if horizontal else x,
            y=x if horizontal else y,
            orientation=orientation,
            marker_color=bar_color,
        )
    )
    fig.update_layout(title=title)
    return apply_plotly_defaults(fig)


def pnl_bar(
    x: list,
    y: list,
    title: str,
) -> go.Figure:
    colors = [COLORS["profit"] if v >= 0 else COLORS["loss"] for v in y]
    fig = go.Figure(go.Bar(x=x, y=y, marker_color=colors))
    fig.update_layout(title=title)
    return apply_plotly_defaults(fig)


def margin_gauge(used: float, available: float) -> go.Figure:
    total = used + available
    pct = (used / total * 100) if total > 0 else 0
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=pct,
            number={"suffix": "%"},
            title={"text": "Margin Utilization"},
            gauge={
                "axis": {"range": [0, 100], "ticksuffix": "%"},
                "bar": {"color": COLORS["primary"]},
                "steps": [
                    {"range": [0, 50], "color": "#1B3A26"},
                    {"range": [50, 80], "color": "#3A2E1B"},
                    {"range": [80, 100], "color": "#3A1B1B"},
                ],
                "threshold": {
                    "line": {"color": COLORS["loss"], "width": 3},
                    "thickness": 0.8,
                    "value": 80,
                },
            },
        )
    )
    fig.update_layout(height=280)
    return apply_plotly_defaults(fig)


def area_line(
    x: list,
    y: list,
    title: str,
    color: str | None = None,
) -> go.Figure:
    line_color = color or COLORS["primary"]
    fig = go.Figure(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            fill="tozeroy",
            line=dict(color=line_color, width=2),
            fillcolor="rgba(66,165,245,0.15)",
        )
    )
    fig.update_layout(title=title)
    return apply_plotly_defaults(fig)
