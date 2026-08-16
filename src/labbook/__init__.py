"""Presentation layer: units, tables, charts and export.

This is the half of the project that turns physics into something a human can
read. It is used by two consumers that must never disagree with each other:

1. The Streamlit application in ``app/``.
2. Scripted analysis in ``studies/``, one folder per question, written by a
   person or by a coding agent.

Both import the same formatters and the same chart builders, so an answer
produced in a script looks and reads exactly like the same answer in the app.

Unlike :mod:`rocketry`, this package may depend on plotly and pandas. The
dependency never points the other way.
"""

from labbook.export import beside, save_data, save_figure, save_table
from labbook.tables import Align, Col, key_values, table
from labbook.units import METRIC, US, Formatter, Measurement, Quantity, UnitSystem, convert

__all__ = [
    "METRIC",
    "US",
    "Align",
    "Col",
    "Formatter",
    "Measurement",
    "Quantity",
    "UnitSystem",
    "beside",
    "convert",
    "key_values",
    "save_data",
    "save_figure",
    "save_table",
    "table",
]
