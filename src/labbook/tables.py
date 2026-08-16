"""Turn results into markdown tables that paste straight into a document or a chat.

Built for scripted analysis. A one-off question should be able to end like
this::

    print(table(results, [
        Col("name", "Vehicle"),
        Col("payload", "Payload", Quantity.MASS, digits=1),
    ]))

Columns declare what they measure, so switching between metric and US units is
one argument and never a find-and-replace.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from labbook.units import METRIC, Formatter, Quantity


class Align(StrEnum):
    """Column alignment in the rendered table."""

    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"

    @property
    def separator(self) -> str:
        """The markdown separator row fragment for this alignment."""
        match self:
            case Align.LEFT:
                return ":---"
            case Align.RIGHT:
                return "---:"
            case Align.CENTER:
                return ":---:"


@dataclass(frozen=True, slots=True)
class Col:
    """One column of a report table.

    Attributes:
        key: Attribute or mapping key to read from each record.
        label: Column heading. Defaults to the key, title-cased.
        quantity: What the value measures. Numbers are converted and given a
            unit; the unit is appended to the heading rather than repeated in
            every cell.
        digits: Decimal places, or None to choose from magnitude.
        align: Column alignment. Numeric columns default to right.
    """

    key: str
    label: str = ""
    quantity: Quantity = Quantity.DIMENSIONLESS
    digits: int | None = None
    align: Align | None = None

    def heading(self, formatter: Formatter) -> str:
        """Column heading, including the unit when there is one.

        Args:
            formatter: The unit system in use.

        Returns:
            The heading text.
        """
        label = self.label or self.key.replace("_", " ").capitalize()
        unit = formatter.unit(self.quantity)
        return f"{label} ({unit})" if unit else label

    def render(self, record: Any, formatter: Formatter) -> str:
        """Render one cell.

        Args:
            record: The row's source object.
            formatter: The unit system in use.

        Returns:
            The cell text. Missing values render as an em-free placeholder.
        """
        value = _read(record, self.key)
        if value is None:
            return "-"
        if isinstance(value, bool):
            return "yes" if value else "no"
        if isinstance(value, int | float):
            if self.quantity is Quantity.PERCENT:
                return f"{value * 100:,.{self.digits if self.digits is not None else 1}f}"
            converted = formatter.value(float(value), self.quantity)
            digits = self.digits if self.digits is not None else _auto_digits(converted)
            return f"{converted:,.{digits}f}"
        return str(value)

    def resolved_align(self) -> Align:
        """Alignment to use, defaulting numeric columns to the right.

        Returns:
            The alignment.
        """
        if self.align is not None:
            return self.align
        return Align.LEFT if self.quantity is Quantity.DIMENSIONLESS else Align.RIGHT


def table(
    records: Iterable[Any],
    columns: Sequence[Col],
    *,
    formatter: Formatter = METRIC,
    title: str = "",
) -> str:
    """Render records as a markdown table.

    Args:
        records: Rows. Each may be a mapping, a dataclass or a pydantic model.
        columns: Column specifications, in order.
        formatter: Unit system to display in.
        title: Optional heading rendered above the table.

    Returns:
        Markdown text, ready to print or write to a file.
    """
    rows = list(records)
    headings = [column.heading(formatter) for column in columns]
    body = [[column.render(record, formatter) for column in columns] for record in rows]
    widths = [
        max(len(heading), *(len(row[i]) for row in body)) if body else len(heading)
        for i, heading in enumerate(headings)
    ]

    def line(cells: Sequence[str]) -> str:
        padded = [cell.ljust(widths[i]) for i, cell in enumerate(cells)]
        return "| " + " | ".join(padded) + " |"

    separator = "| " + " | ".join(
        column.resolved_align().separator.ljust(widths[i]) for i, column in enumerate(columns)
    ) + " |"

    parts = [f"### {title}", ""] if title else []
    parts.extend([line(headings), separator, *(line(row) for row in body)])
    return "\n".join(parts)


def key_values(
    pairs: Mapping[str, Any] | Sequence[tuple[str, Any]],
    *,
    formatter: Formatter = METRIC,
    title: str = "",
) -> str:
    """Render a set of labelled numbers as a two-column markdown table.

    For summarising a single result rather than comparing many.

    Args:
        pairs: Label to value. A value may be a plain object, or a tuple of
            (value, quantity) to have it converted and given a unit.
        formatter: Unit system to display in.
        title: Optional heading rendered above the table.

    Returns:
        Markdown text.
    """
    items = pairs.items() if isinstance(pairs, Mapping) else pairs
    rows: list[dict[str, str]] = []
    for label, raw in items:
        if isinstance(raw, tuple) and len(raw) == 2 and isinstance(raw[1], Quantity):
            value, quantity = raw
            rendered = formatter.format(float(value), quantity)
        elif isinstance(raw, float):
            rendered = f"{raw:,.{_auto_digits(raw)}f}"
        else:
            rendered = str(raw)
        rows.append({"label": label, "value": rendered})
    return table(
        rows,
        [Col("label", "Quantity"), Col("value", "Value", align=Align.RIGHT)],
        formatter=formatter,
        title=title,
    )


def _read(record: Any, key: str) -> Any:
    """Read a field from a mapping, dataclass, pydantic model or plain object.

    Args:
        record: The source object.
        key: Field name or mapping key.

    Returns:
        The value, or None if absent.
    """
    if isinstance(record, Mapping):
        return record.get(key)
    if isinstance(record, BaseModel):
        return getattr(record, key, None)
    if (
        is_dataclass(record)
        and not isinstance(record, type)
        and any(field.name == key for field in fields(record))
    ):
        return getattr(record, key)
    return getattr(record, key, None)


def _auto_digits(value: float) -> int:
    """Choose decimal places from magnitude.

    Args:
        value: The number about to be shown.

    Returns:
        Decimal places.
    """
    magnitude = abs(value)
    if magnitude >= 100:
        return 0
    if magnitude >= 10:
        return 1
    return 2
