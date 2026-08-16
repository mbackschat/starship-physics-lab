"""Chart builders shared by the application and by analysis scripts.

Every chart obeys the same rules so that a figure produced in a script is
indistinguishable from the same figure in the app: the validated palette from
:mod:`labbook.palette`, recessive grid and axes, thin marks, direct labels, and
units taken from a :class:`labbook.units.Formatter`.
"""

from collections.abc import Sequence

import plotly.graph_objects as go

from labbook.curves import BurnSample, LoadingSample
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
from rocketry.ascent import AscentSample


def base_layout(
    figure: go.Figure,
    *,
    title: str,
    x_label: str,
    y_label: str,
    mode: Mode = Mode.LIGHT,
    subtitle: str = "",
    show_legend: bool = True,
    bottom_margin: int = 60,
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
        bottom_margin: Space below the plot, pixels. Charts with a legend need
            more, or it lands on top of the axis title.

    Returns:
        The same figure, styled.
    """
    heading = title if not subtitle else f"{title}<br><sub>{subtitle}</sub>"
    figure.update_layout(
        title={"text": heading, "font": {"size": 18, "color": INK_PRIMARY[mode]}, "x": 0.01},
        paper_bgcolor=SURFACE[mode],
        plot_bgcolor=SURFACE[mode],
        font={"color": INK_SECONDARY[mode], "size": 13},
        margin={"l": 70, "r": 30, "t": 110 if subtitle else 80, "b": bottom_margin},
        showlegend=show_legend,
        # Anchored to the figure container, not the plot area: a fraction of
        # plot height moves with chart size and lands on the axis title.
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 0.0,
            "yref": "container",
            "x": 0.0,
            "xref": "container",
        },
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
    figure.update_layout(barmode="stack", bargap=0.35)
    return base_layout(
        figure,
        title=title,
        subtitle=subtitle,
        x_label=formatter.axis_label("Mass", Quantity.MASS),
        y_label="",
        mode=mode,
        bottom_margin=120,
    )


def trajectory(
    samples: Sequence[AscentSample],
    *,
    events: Sequence[tuple[str, float, float]] = (),
    formatter: Formatter = METRIC,
    mode: Mode = Mode.LIGHT,
    title: str = "Flight path",
    subtitle: str = "",
    up_to_seconds: float | None = None,
) -> go.Figure:
    """Altitude against downrange distance, with stage separations marked.

    Args:
        samples: Ascent samples, each with downrange_m, altitude_m and time_s.
        events: Points to mark, as (label, downrange_m, altitude_m).
        formatter: Unit system to display in.
        mode: Light or dark surface.
        title: Chart title.
        subtitle: Optional second line under the title.
        up_to_seconds: Draw only up to this time, for scrubbing through a flight.

    Returns:
        The figure.
    """
    shown = [
        sample for sample in samples if up_to_seconds is None or sample.time_s <= up_to_seconds
    ]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[formatter.value(sample.downrange_m / 1000.0, Quantity.DISTANCE) for sample in shown],
            y=[formatter.value(sample.altitude_m / 1000.0, Quantity.DISTANCE) for sample in shown],
            mode="lines",
            line={"color": colour(Series.PAYLOAD, mode), "width": 2},
            showlegend=False,
            hovertemplate="%{x:,.0f} downrange, %{y:,.0f} up<extra></extra>",
        )
    )
    if shown:
        last = shown[-1]
        figure.add_trace(
            go.Scatter(
                x=[formatter.value(last.downrange_m / 1000.0, Quantity.DISTANCE)],
                y=[formatter.value(last.altitude_m / 1000.0, Quantity.DISTANCE)],
                mode="markers",
                marker={
                    "color": HIGHLIGHT,
                    "size": 12,
                    "line": {"color": SURFACE[mode], "width": 2},
                },
                showlegend=False,
                hoverinfo="skip",
            )
        )
    for label, downrange_m, altitude_m in events:
        figure.add_trace(
            go.Scatter(
                x=[formatter.value(downrange_m / 1000.0, Quantity.DISTANCE)],
                y=[formatter.value(altitude_m / 1000.0, Quantity.DISTANCE)],
                mode="markers+text",
                marker={"color": INK_MUTED[mode], "size": 9, "symbol": "x"},
                text=[f"  {label}"],
                textposition="middle right",
                textfont={"color": INK_SECONDARY[mode], "size": 11},
                showlegend=False,
                hoverinfo="skip",
            )
        )
    return base_layout(
        figure,
        title=title,
        subtitle=subtitle,
        x_label=formatter.axis_label("Downrange distance", Quantity.DISTANCE),
        y_label=formatter.axis_label("Altitude", Quantity.DISTANCE),
        mode=mode,
        show_legend=False,
    )


def burn_animation(
    trace: Sequence[BurnSample],
    *,
    formatter: Formatter = METRIC,
    mode: Mode = Mode.LIGHT,
    title: str = "During the burn",
    subtitle: str = "",
    frames: int = 40,
) -> go.Figure:
    """Play a burn through, so the curve is watched being drawn rather than read.

    The shape is the lesson and it surprises people: the line steepens. Equal
    chunks of propellant buy more and more speed, because the vehicle keeps
    throwing away the mass it no longer has to accelerate. Readers who have just
    met the logarithm expect the opposite, which is why this one moves.

    Args:
        trace: Samples through the burn, from :func:`labbook.curves.burn_trace`.
        formatter: Unit system to display in.
        mode: Light or dark surface.
        title: Chart title.
        subtitle: Optional second line under the title.
        frames: How many animation steps to emit. Every frame carries the curve
            so far, so this is the one real cost of the animation.

    Returns:
        The figure, with a play button.
    """
    x = formatter.values([sample.burnt_t for sample in trace], Quantity.MASS)
    y = formatter.values([sample.velocity_ms for sample in trace], Quantity.VELOCITY)
    live = colour(Series.PAYLOAD, mode)

    figure = go.Figure(
        data=[
            # The finished curve, held back so the moving line has somewhere to
            # go. Without it the axes rescale on every frame and the steepening
            # is hidden by the rescaling.
            go.Scatter(
                x=x, y=y, mode="lines", hoverinfo="skip", showlegend=False,
                line={"color": INK_MUTED[mode], "width": 1, "dash": "dot"},
            ),
            go.Scatter(
                x=x[:1], y=y[:1], mode="lines", showlegend=False, hoverinfo="skip",
                line={"color": live, "width": 3},
            ),
            go.Scatter(
                x=x[:1], y=y[:1], mode="markers", showlegend=False, hoverinfo="skip",
                marker={
                    "color": HIGHLIGHT,
                    "size": 11,
                    "line": {"color": SURFACE[mode], "width": 2},
                },
            ),
        ]
    )

    steps = _frame_indices(len(trace), frames)
    figure.frames = [
        go.Frame(
            name=str(index),
            traces=[1, 2],
            data=[
                go.Scatter(x=x[: index + 1], y=y[: index + 1]),
                go.Scatter(x=[x[index]], y=[y[index]]),
            ],
        )
        for index in steps
    ]
    figure.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "direction": "right",
                "showactive": False,
                # Anchored right. The title is set flush left by base_layout, so
                # a left-anchored button lands on top of it.
                "x": 1.0,
                "y": 1.02,
                "xanchor": "right",
                "yanchor": "bottom",
                "pad": {"r": 4, "t": 4},
                "bgcolor": SURFACE[mode],
                "bordercolor": AXIS[mode],
                "font": {"color": INK_SECONDARY[mode], "size": 12},
                "buttons": [
                    {
                        "label": "▶  Burn it",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": 45, "redraw": False},
                                "fromcurrent": True,
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                    {
                        "label": "↺",
                        "method": "animate",
                        "args": [
                            [str(steps[0])],
                            {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"},
                        ],
                    },
                ],
            }
        ]
    )
    return base_layout(
        figure,
        title=title,
        subtitle=subtitle,
        x_label=formatter.axis_label("Propellant burnt", Quantity.MASS),
        y_label=formatter.axis_label("Speed gained", Quantity.VELOCITY),
        mode=mode,
        show_legend=False,
    )


def loading_curve(
    sweep: Sequence[LoadingSample],
    *,
    formatter: Formatter = METRIC,
    mode: Mode = Mode.LIGHT,
    title: str = "Before the burn",
    subtitle: str = "",
    at_t: float | None = None,
) -> go.Figure:
    """Plot what each extra tonne of propellant *loaded* is worth to a designer.

    The companion to :func:`burn_animation` and the mirror image of it. This one
    flattens. Showing the two together is the point: they are the same equation
    answering two different questions, and fusing them is the usual mistake.

    Args:
        sweep: Samples from :func:`labbook.curves.loading_sweep`.
        formatter: Unit system to display in.
        mode: Light or dark surface.
        title: Chart title.
        subtitle: Optional second line under the title.
        at_t: Mark the reader's own rocket at this propellant load, tonnes.

    Returns:
        The figure.
    """
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=formatter.values([sample.propellant_t for sample in sweep], Quantity.MASS),
            y=formatter.values([sample.delta_v_ms for sample in sweep], Quantity.VELOCITY),
            mode="lines",
            showlegend=False,
            line={"color": colour(Series.PROPELLANT, mode), "width": 3},
            hovertemplate="%{x:,.0f} loaded → %{y:,.0f}<extra></extra>",
        )
    )
    if at_t is not None:
        here = min(sweep, key=lambda sample: abs(sample.propellant_t - at_t))
        figure.add_trace(
            go.Scatter(
                x=[formatter.value(here.propellant_t, Quantity.MASS)],
                y=[formatter.value(here.delta_v_ms, Quantity.VELOCITY)],
                mode="markers+text",
                showlegend=False,
                hoverinfo="skip",
                marker={
                    "color": HIGHLIGHT,
                    "size": 11,
                    "line": {"color": SURFACE[mode], "width": 2},
                },
                text=["  yours"],
                textposition="middle right",
                textfont={"color": INK_SECONDARY[mode], "size": 12},
            )
        )
    return base_layout(
        figure,
        title=title,
        subtitle=subtitle,
        x_label=formatter.axis_label("Propellant loaded", Quantity.MASS),
        y_label=formatter.axis_label("Speed the finished rocket reaches", Quantity.VELOCITY),
        mode=mode,
        show_legend=False,
    )


def _frame_indices(count: int, frames: int) -> list[int]:
    """Pick which samples to emit as animation frames.

    Args:
        count: How many samples the trace holds.
        frames: How many frames are wanted.

    Returns:
        Indices into the trace, always including the first and the last so the
        animation starts at rest and finishes on the real answer.
    """
    if count <= frames:
        return list(range(count))
    step = (count - 1) / (frames - 1)
    return sorted({round(index * step) for index in range(frames)} | {0, count - 1})


def _share(value: float, total: float) -> str:
    """Format a share, never rounding a real contribution down to zero.

    Args:
        value: The part.
        total: The whole.

    Returns:
        A percentage string.
    """
    fraction = value / total if total else 0.0
    return f"{fraction:.1%}" if 0 < fraction < 0.01 else f"{fraction:.0%}"


def loss_waterfall(
    breakdown: dict[str, float],
    *,
    formatter: Formatter = METRIC,
    mode: Mode = Mode.LIGHT,
    title: str = "Where the engines' work went",
    subtitle: str = "",
) -> go.Figure:
    """One stacked bar splitting the engines' total output into speed and losses.

    The single most illuminating picture in the whole subject: it shows that a
    launch spends roughly a fifth of everything it produces just holding itself
    up against gravity.

    Args:
        breakdown: Label to velocity in m/s, in stacking order.
        formatter: Unit system to display in.
        mode: Light or dark surface.
        title: Chart title.
        subtitle: Optional second line under the title.

    Returns:
        The figure.
    """
    palette = {
        "Speed gained": colour(Series.PAYLOAD, mode),
        "Gravity loss": colour(Series.PROPELLANT, mode),
        "Drag loss": colour(Series.STRUCTURE, mode),
        "Steering loss": colour(Series.RECOVERY, mode),
    }
    total = sum(breakdown.values()) or 1.0
    figure = go.Figure()
    for label, value in breakdown.items():
        figure.add_trace(
            go.Bar(
                y=["budget"],
                x=[formatter.value(value, Quantity.VELOCITY)],
                name=f"{label} ({_share(value, total)})",
                orientation="h",
                marker={
                    "color": palette.get(label, colour(Series.OTHER, mode)),
                    "line": {"color": SURFACE[mode], "width": 2},
                },
                hovertemplate=f"{label}: %{{x:,.0f}}<extra></extra>",
            )
        )
    figure.update_layout(barmode="stack", bargap=0.55)
    figure.update_yaxes(showticklabels=False)
    return base_layout(
        figure,
        title=title,
        subtitle=subtitle,
        x_label=formatter.axis_label("Velocity the engines produced", Quantity.VELOCITY),
        y_label="",
        mode=mode,
        bottom_margin=120,
    )


def payload_against_dry_mass(
    points: Sequence[tuple[float, float]],
    *,
    arriving: Sequence[tuple[float, float]] = (),
    markers: Sequence[tuple[str, float, float]] = (),
    formatter: Formatter = METRIC,
    mode: Mode = Mode.LIGHT,
    title: str = "Payload against how heavy the ship is",
    subtitle: str = "",
) -> go.Figure:
    """Payload as a function of an assumed dry mass, with the total that arrives.

    Two lines, and the relationship between them is the entire argument: the
    total arriving in orbit is flat, so every tonne saved on the vehicle becomes
    a tonne of cargo.

    Args:
        points: Pairs of dry mass and payload, both tonnes.
        arriving: Pairs of dry mass and total mass reaching orbit, both tonnes.
        markers: Published estimates to label, as (label, dry mass, payload).
        formatter: Unit system to display in.
        mode: Light or dark surface.
        title: Chart title.
        subtitle: Optional second line under the title.

    Returns:
        The figure.
    """
    figure = go.Figure()
    if arriving:
        figure.add_trace(
            go.Scatter(
                x=formatter.values([point[0] for point in arriving], Quantity.MASS),
                y=formatter.values([point[1] for point in arriving], Quantity.MASS),
                mode="lines",
                name="Total reaching orbit",
                line={"color": colour(Series.OTHER, mode), "width": 2, "dash": "dot"},
                hovertemplate="%{y:,.0f} arrives<extra></extra>",
            )
        )
    figure.add_trace(
        go.Scatter(
            x=formatter.values([point[0] for point in points], Quantity.MASS),
            y=formatter.values([point[1] for point in points], Quantity.MASS),
            mode="lines",
            name="Payload",
            line={"color": colour(Series.PAYLOAD, mode), "width": 3},
            hovertemplate="%{y:,.0f} of cargo<extra></extra>",
        )
    )
    for label, dry_mass, payload in markers:
        figure.add_trace(
            go.Scatter(
                x=[formatter.value(dry_mass, Quantity.MASS)],
                y=[formatter.value(payload, Quantity.MASS)],
                mode="markers+text",
                marker={
                    "color": HIGHLIGHT,
                    "size": 10,
                    "symbol": "diamond",
                    "line": {"color": SURFACE[mode], "width": 2},
                },
                text=[f"  {label}"],
                textposition="middle right",
                textfont={"color": INK_SECONDARY[mode], "size": 11},
                showlegend=False,
                hoverinfo="skip",
            )
        )
    figure.add_hline(y=0, line={"color": AXIS[mode], "width": 1})
    return base_layout(
        figure,
        title=title,
        subtitle=subtitle,
        x_label=formatter.axis_label("Assumed ship dry mass", Quantity.MASS),
        y_label=formatter.axis_label("Mass", Quantity.MASS),
        mode=mode,
        bottom_margin=120,
    )
