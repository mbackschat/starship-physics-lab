"""Recheck the source article's arithmetic, live, from the physics core.

Every claim here is recomputed when the page loads rather than quoted from a
stored answer. That is the point: if somebody changes an engine's specific
impulse in the library, this page changes with it, and the tests fail if a
verdict stops matching its own arithmetic.

The full written log is in docs/physics-reference.md section 3. This is the
executable half of it.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from rocketry.constants import G0, KMH_TO_MS, V_EQUATORIAL
from rocketry.dynamics import acceleration_after, gravity_thrust_fraction, thrust_to_weight
from rocketry.reuse import Burn, recovery_propellant
from rocketry.tsiolkovsky import binary_velocity, delta_v, mass_after_burn, propellant_burnt


class Verdict(StrEnum):
    """Whether a claim survived being recomputed."""

    CONFIRMED = "confirmed"
    """Reproduces within its stated tolerance."""

    WRONG = "wrong"
    """Does not reproduce. The article's number is in error."""

    @property
    def label(self) -> str:
        """Human-readable verdict."""
        match self:
            case Verdict.CONFIRMED:
                return "Reproduces"
            case Verdict.WRONG:
                return "Does not reproduce"


@dataclass(frozen=True, slots=True)
class Claim:
    """One checkable number from the article.

    Attributes:
        topic: What the number is about.
        statement: What the article says, in words.
        article_value: The number the article prints.
        compute: Recomputes it from the physics core.
        unit: What the number is measured in.
        tolerance: Relative error still counted as reproducing.
        section: Where docs/physics-reference.md verifies it.
        note: Optional explanation, used mainly for the errors.
    """

    topic: str
    statement: str
    article_value: float
    compute: Callable[[], float]
    unit: str
    section: str
    tolerance: float = 0.02
    note: str = ""


@dataclass(frozen=True, slots=True)
class Result:
    """A claim, recomputed.

    Attributes:
        claim: What was checked.
        computed: What the physics core says.
        verdict: Whether the two agree.
    """

    claim: Claim
    computed: float
    verdict: Verdict

    @property
    def relative_error(self) -> float:
        """How far apart the two are, as a fraction of the article's number."""
        if not self.claim.article_value:
            return 0.0
        return abs(self.computed - self.claim.article_value) / abs(self.claim.article_value)


CLAIMS: tuple[Claim, ...] = (
    Claim(
        topic="Raptor 3 propellant flow",
        statement="250 tf at 327 s burns 0.764 t of propellant per second",
        article_value=0.764,
        compute=lambda: propellant_burnt(thrust_tf=250, isp=327, seconds=1.0),
        unit="t/s",
        section="3.1",
    ),
    Claim(
        topic="Binary velocity constant",
        statement="A doubling of the mass ratio buys 2,428 m/s at Isp 350",
        article_value=2428.0,
        compute=lambda: binary_velocity(350),
        unit="m/s",
        section="4, correction C1",
        note=(
            "The article uses a constant of 6.937. The correct one is g0 times "
            "the natural log of 2, which is 6.798. A 2 % error, and the idea "
            "itself is a good one."
        ),
    ),
    Claim(
        topic="Starship ideal delta-v",
        statement="300 t reaching orbit on 1,600 t of propellant at 365 s gives 6,609 m/s",
        article_value=6609.0,
        compute=lambda: delta_v(m0=1900, mf=300, isp=365),
        unit="m/s",
        section="3.3",
    ),
    Claim(
        topic="Super Heavy ideal delta-v",
        statement="Burning 3,320 t of a 5,850 t stack at 340 s gives 2,795 m/s",
        article_value=2795.0,
        compute=lambda: delta_v(m0=5850, mf=2530, isp=340),
        unit="m/s",
        section="3.3",
    ),
    Claim(
        topic="Super Heavy's share of the work",
        statement="The booster provides only 30 % of the stack's total velocity",
        article_value=0.30,
        compute=lambda: delta_v(m0=5850, mf=2530, isp=340)
        / (delta_v(m0=5850, mf=2530, isp=340) + delta_v(m0=1900, mf=300, isp=365)),
        unit="",
        section="3.3",
    ),
    Claim(
        topic="Falcon 9 upper stage delta-v",
        statement="17.5 t of payload on 107 t of propellant at 348 s gives 6,100 m/s",
        article_value=6100.0,
        compute=lambda: delta_v(m0=128.5, mf=21.5, isp=348),
        unit="m/s",
        section="3.4",
    ),
    Claim(
        topic="Weighing Starship from a 14 s burn",
        statement="10.7 t burnt for 139 m/s means the ship weighed about 259 t",
        article_value=259.0,
        compute=lambda: mass_after_burn(10.7, 138.9, 350),
        unit="t",
        section="3.2",
    ),
    Claim(
        topic="Super Heavy's return budget",
        statement="Coming home costs at least 1.1 t of propellant per tonne of booster",
        article_value=1.10,
        compute=lambda: recovery_propellant(1.0, [Burn(600, 330), Burn(1800, 330)]),
        unit="t/t",
        section="3.3",
    ),
    Claim(
        topic="Liftoff thrust-to-weight",
        statement="33 engines at 250 tf lift 5,850 t at a ratio of 1.41",
        article_value=1.41,
        compute=lambda: thrust_to_weight(thrust_tf=33 * 250, mass_t=5850),
        unit="",
        section="3.3",
    ),
    Claim(
        topic="Thrust spent on not falling",
        statement="At liftoff, 70 % of the thrust is spent merely holding the rocket up",
        article_value=0.70,
        compute=lambda: gravity_thrust_fraction(thrust_to_weight(33 * 250, 5850)),
        unit="",
        section="3.3",
    ),
    Claim(
        topic="Falcon 9 acceleration at T+40 s",
        statement="Falcon 9 reaches 0.875 g after 40 seconds",
        article_value=0.875,
        compute=lambda: acceleration_after(
            seconds=40, twr_initial=1.412, mass_flow_fraction=0.00501
        ),
        unit="g",
        section="4, correction C4",
        note=(
            "Using the article's own premise that both rockets lift off at the "
            "same ratio, the answer is 0.77 g. Its figure quietly assumes 1.51 "
            "instead of 1.41. The mechanism it describes is real; the size of "
            "the effect is about a third of what it claims."
        ),
    ),
    Claim(
        topic="Starship acceleration at T+40 s",
        statement="Starship reaches only 0.69 g after 40 seconds",
        article_value=0.69,
        compute=lambda: acceleration_after(
            seconds=40, twr_initial=1.410, mass_flow_fraction=0.00431
        ),
        unit="g",
        section="3.4",
    ),
    Claim(
        topic="Earth's help at the equator",
        statement="A due east launch is handed about 465 m/s by the planet's rotation",
        article_value=465.0,
        compute=lambda: V_EQUATORIAL,
        unit="m/s",
        section="2.5",
    ),
    Claim(
        topic="Super Heavy boostback budget",
        statement="Stopping 5,400 km/h and reversing 1,000 km/h needs about 1,800 m/s",
        article_value=1800.0,
        compute=lambda: (5400 + 1000) * KMH_TO_MS,
        unit="m/s",
        section="3.3",
    ),
    Claim(
        topic="Reentry loading versus Falcon 9",
        statement="Super Heavy would need a 12.5 m diameter to reenter as gently",
        article_value=12.5,
        compute=lambda: 3.66 * math.sqrt(12.0),
        unit="m",
        section="3.5",
    ),
    Claim(
        topic="A 20 s hover costs this much velocity",
        statement="Twenty seconds of landing burn hands 200 m/s straight to gravity",
        article_value=200.0,
        compute=lambda: 20.0 * G0,
        unit="m/s",
        section="3.2",
    ),
)


def check(claim: Claim) -> Result:
    """Recompute one claim and judge it.

    Args:
        claim: What to check.

    Returns:
        The claim, the computed value and the verdict.
    """
    computed = claim.compute()
    error = abs(computed - claim.article_value) / abs(claim.article_value)
    verdict = Verdict.CONFIRMED if error <= claim.tolerance else Verdict.WRONG
    return Result(claim=claim, computed=computed, verdict=verdict)


def check_all() -> list[Result]:
    """Recompute every claim.

    Returns:
        One result per claim, in the order they are listed.
    """
    return [check(claim) for claim in CLAIMS]
