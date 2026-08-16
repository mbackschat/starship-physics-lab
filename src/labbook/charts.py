"""Chart builders shared by the application and by analysis scripts.

Every chart obeys the same rules so that a figure produced in a script is
indistinguishable from the same figure in the app: the validated palette from
:mod:`labbook.palette`, recessive grid and axes, thin marks, direct labels, and
units taken from a :class:`labbook.units.Formatter`.
"""

from collections.abc import Sequence

import plotly.graph_objects as go

from labbook.palette import (
    AXIS,
    GRIDLINE,
    HIGHLIGHT,
    INK_MUTED,
    INK_PRIMARY,
    INK_SECONDARY,
    SURFACE,
    Mode,
    Series,
    colour,
)
from labbook.units import METRIC, Formatter, Quantity


def base_layout(
    figure: go.Figure,
    *,
    title: str,
    x_label: str,
    y_label: str,
    mode: Mode = Mode.LIGHT,
    subtitle: str = "",
    show_legend: bool = True,
) -> go.Figure:
    """Apply the project's shared chart styling.

    Args:
        figure: The figure to style.
        title: Chart title.
        x_label: Horizontal axis label, including its unit.
        y_label: Vertical axis label, including its unit.
        mode: Light or dark surface.
        subtitle: Optional second line under the title, in secondary ink.
        show_legend: Whether to draw a legend. A single series carries its
            identity in the title and needs none; two or more always do.

    Returns:
        The same figure, styled.
    """
    heading = title if not subtitle else f"{title}<br><sub>{subtitle}</sub>"
    figure.update_layout(
        title={"text": heading, "font": {"size": 18, "color": INK_PRIMARY[mode]}, "x": 0.01},
        paper_bgcolor=SURFACE[mode],
        plot_bgcolor=SURFACE[mode],
        font={"color": INK_SECONDARY[mode], "size": 13},
        margin={"l": 70, "r": 30, "t": 110 if subtitle else 80, "b": 60},
        showlegend=show_legend,
        legend={"orientation": "h", "yanchor": "top", "y": -0.22, "x": 0},
        hovermode="x unified",
    )
    axis_style = {
        "gridcolor": GRIDLINE[mode],
        "linecolor": AXIS[mode],
        "zerolinecolor": AXIS[mode],
        "tickfont": {"color": INK_MUTED[mode], "size": 12},
        "title_font": {"color": INK_SECONDARY[mode], "size": 13},
    }
    figure.update_xaxes(title_text=x_label, **axis_style)
    figure.update_yaxes(title_text=y_label, **axis_style)
    return figure


def staging_sweep(
    sweep: Sequence[tuple[float, float]],
    *,
    markers: Sequence[tuple[str, float, float]] = (),
    formatter: Formatter = METRIC,
    mode: Mode = Mode.LIGHT,
    title: str = "Payload against staging speed",
    subtitle: str = "",
) -> go.Figure:
    """Plot payload as a function of where the stages separate.

    The central chart of the whole project: it shows that the staging split is
    worth roughly a factor of two in payload, and where real rockets sit on the
    curve.

    Args:
        sweep: Pairs of staging speed in km/h and payload in tonnes.
        markers: Named points to label on the curve, as (label, speed, payload).
        formatter: Unit system to display in.
        mode: Light or dark surface.
        title: Chart title.
        subtitle: Optional second line under the title.

    Returns:
        The figure.
    """
    speeds = formatter.values([point[0] for point in sweep], Quantity.SPEED)
    payloads = formatter.values([point[1] for point in sweep], Quantity.MASS)
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=speeds,
            y=payloads,
            mode="lines",
            name="Payload",
            showlegend=False,
            line={"color": colour(Series.PAYLOAD, mode), "width": 2},
            hovertemplate="%{x:,.0f} → %{y:,.0f}<extra></extra>",
        )
    )
    if sweep:
        peak = max(sweep, key=lambda point: point[1])
        figure.add_trace(
            go.Scatter(
                x=[formatter.value(peak[0], Quantity.SPEED)],
                y=[formatter.value(peak[1], Quantity.MASS)],
                mode="markers+text",
                name="Best split",
                showlegend=False,
                marker={
                    "color": colour(Series.PAYLOAD, mode),
                    "size": 11,
                    "line": {"color": SURFACE[mode], "width": 2},
                },
                text=["  best split"],
                textposition="top center",
                textfont={"color": INK_SECONDARY[mode], "size": 12},
                hoverinfo="skip",
            )
        )
    for label, speed, payload in markers:
        figure.add_trace(
            go.Scatter(
                x=[formatter.value(speed, Quantity.SPEED)],
                y=[formatter.value(payload, Quantity.MASS)],
                mode="markers+text",
                name=label,
                marker={
                    "color": HIGHLIGHT,
                    "size": 10,
                    "symbol": "diamond",
                    "line": {"color": SURFACE[mode], "width": 2},
                },
                text=[f"  {label}"],
                textposition="middle right",
                textfont={"color": INK_SECONDARY[mode], "size": 12},
                showlegend=False,
                hoverinfo="skip",
            )
        )
    return base_layout(
        figure,
        title=title,
        subtitle=subtitle,
        x_label=formatter.axis_label("Staging speed", Quantity.SPEED),
        y_label=formatter.axis_label("Payload", Quantity.MASS),
        mode=mode,
        show_legend=False,
    )


def mass_breakdown(
    labels: Sequence[str],
    components: dict[Series, Sequence[float]],
    *,
    formatter: Formatter = METRIC,
    mode: Mode = Mode.LIGHT,
    title: str = "What a rocket is made of",
    subtitle: str = "",
) -> go.Figure:
    """Stacked horizontal bars splitting each vehicle into its parts.

    Args:
        labels: One label per vehicle, top to bottom.
        components: Series to per-vehicle values in tonnes. Stacked in the order
            given, so the caller controls reading order; colours always come
            from the fixed categorical assignment in :mod:`labbook.palette`.
        formatter: Unit system to display in.
        mode: Light or dark surface.
        title: Chart title.
        subtitle: Optional second line under the title.

    Returns:
        The figure.
    """
    figure = go.Figure()
    for series, values in components.items():
        figure.add_trace(
            go.Bar(
                y=list(labels),
                x=formatter.values(list(values), Quantity.MASS),
                name=series.label,
                orientation="h",
                marker={
                    "color": colour(series, mode),
                    "line": {"color": SURFACE[mode], "width": 2},
                },
                hovertemplate=f"{series.label}: %{{x:,.0f}}<extra></extra>",
            )
        )
    figure.update_layout(barmode="stack", bargap=0.35, margin={"b": 110})
    return base_layout(
        figure,
        title=title,
        subtitle=subtitle,
        x_label=formatter.axis_label("Mass", Quantity.MASS),
        y_label="",
        mode=mode,
    )
