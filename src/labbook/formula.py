"""Show an equation twice: once in symbols, once with the reader's own numbers in it.

This is the single device that makes equations stop being frightening. Seeing

    Δv = v_e · ln(m₀ / m_f)
    Δv = 3,581 m/s · ln(1,900 t / 300 t) = 6,609 m/s

next to each other turns the symbols into labels for numbers the reader just
chose with a slider, rather than into notation to be decoded.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from labbook.units import METRIC, Formatter, Quantity


@dataclass(frozen=True, slots=True)
class Term:
    """One named quantity in a formula.

    Attributes:
        symbol: How it appears in the symbolic form, for example ``m₀``.
        value: Its current value, in this library's storage unit.
        quantity: What it measures, which decides its unit and conversion.
        digits: Decimal places, or None to choose from magnitude.
    """

    symbol: str
    value: float
    quantity: Quantity = Quantity.DIMENSIONLESS
    digits: int | None = None

    def text(self, formatter: Formatter = METRIC) -> str:
        """Render this term's value with its unit.

        Args:
            formatter: Unit system to display in.

        Returns:
            A display string such as "1,900 t".
        """
        return formatter.format(self.value, self.quantity, self.digits)


@dataclass(frozen=True, slots=True)
class Formula:
    """An equation the reader can see solved with their own inputs.

    Attributes:
        name: What the equation is called.
        symbolic: The equation in symbols, using each term's ``symbol``.
        terms: The inputs, in the order they appear.
        result: What the equation produces.
        note: Optional one-line explanation of what it means.
    """

    name: str
    symbolic: str
    terms: Sequence[Term]
    result: Term
    note: str = ""

    def __post_init__(self) -> None:
        """Reject a formula with nothing to substitute.

        Raises:
            ValueError: If there are no terms, which would make the substituted
                form identical to the symbolic one and the whole device
                pointless.
        """
        if not self.terms:
            raise ValueError(f"formula {self.name!r} needs at least one term to substitute")

    def substituted(self, formatter: Formatter = METRIC) -> str:
        """The equation with every symbol replaced by its current value.

        The result is substituted too, so the reader sees the whole statement
        become true rather than an expression with an answer bolted on.

        Symbols are replaced longest-first, so a short symbol that is a prefix
        of a longer one cannot corrupt it.

        Args:
            formatter: Unit system to display in.

        Returns:
            The equation as a string of numbers.
        """
        text = self.symbolic
        every = [*self.terms, self.result]
        for term in sorted(every, key=lambda item: len(item.symbol), reverse=True):
            text = text.replace(term.symbol, term.text(formatter))
        return text

    def result_text(self, formatter: Formatter = METRIC) -> str:
        """The result with its unit.

        Args:
            formatter: Unit system to display in.

        Returns:
            A display string.
        """
        return self.result.text(formatter)

    def full(self, formatter: Formatter = METRIC) -> str:
        """Both forms and the answer, ready to render as markdown.

        Args:
            formatter: Unit system to display in.

        Returns:
            Two lines: the symbolic form, then the substituted form.
        """
        return f"{self.symbolic}\n{self.substituted(formatter)}"
