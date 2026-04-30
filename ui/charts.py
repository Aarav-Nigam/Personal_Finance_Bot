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


def correlation_heatmap(corr_df, title: str = "Holdings Correlation") -> go.Figure:
    import pandas as pd

    if not isinstance(corr_df, pd.DataFrame) or corr_df.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return apply_plotly_defaults(fig)

    fig = go.Figure(
        go.Heatmap(
            z=corr_df.values,
            x=corr_df.columns.tolist(),
            y=corr_df.index.tolist(),
            colorscale=[
                [0, COLORS["loss"]],
                [0.5, COLORS["bg"]],
                [1, COLORS["profit"]],
            ],
            zmin=-1,
            zmax=1,
            text=corr_df.round(2).values,
            texttemplate="%{text}",
            textfont={"size": 10},
        )
    )
    fig.update_layout(title=title, height=max(350, len(corr_df) * 45))
    return apply_plotly_defaults(fig)


def sub_score_bar(sub_scores: dict, title: str = "Signal Breakdown") -> go.Figure:
    from ui.glossary import TERMS

    categories = [c.capitalize() for c in sub_scores.keys()]
    values = list(sub_scores.values())
    colors = [COLORS["profit"] if v >= 0 else COLORS["loss"] for v in values]
    hover_texts = [TERMS.get(c.capitalize(), c.capitalize()) for c in sub_scores.keys()]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=categories,
            orientation="h",
            marker_color=colors,
            text=[f"{v:+.1f}" for v in values],
            textposition="outside",
            hovertext=hover_texts,
            hoverinfo="y+x+text",
        )
    )
    fig.update_layout(
        title=title,
        xaxis=dict(range=[-10, 10], title="Score"),
        height=220,
        margin=dict(l=100, r=40, t=40, b=30),
    )
    return apply_plotly_defaults(fig)
