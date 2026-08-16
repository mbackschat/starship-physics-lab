"""What bringing a stage home costs, in propellant carried uphill.

See docs/physics-reference.md section 2.7, which is the source of every budget
below and is checked against them by
`tests/test_scenarios.py::TestRecoveryProfilesMatchTheReference`.

Super Heavy's tower catch was calibrated against the article from the start and
reproduces its 1.10 t of propellant per tonne of dry mass. Falcon 9's profiles
were not: they were filled in at the bottom of every documented range, which
made a droneship recovery cost 0.40 t/t where the same section of the reference
concludes roughly 1.0 t/t. Nothing held the two together, so the library quietly
said reuse was half as expensive as the project's own verification did.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from rocketry.constants import G0
from rocketry.tsiolkovsky import mass_ratio

if TYPE_CHECKING:  # pragma: no cover
    from rocketry.models import Recovery


@dataclass(frozen=True, slots=True)
class Burn:
    """One propulsive manoeuvre.

    Attributes:
        delta_v: Velocity change of the manoeuvre, m/s.
        isp: Specific impulse achieved during it, seconds. Landing burns run
            deeply throttled and should use a lower value than the engine's
            rating.
        label: Optional human-readable name, used by the UI.
    """

    delta_v: float
    isp: float
    label: str = ""

    def __post_init__(self) -> None:
        """Reject a manoeuvre that is not one.

        Recovery burns are read from YAML, where a sign slip is easy and its
        consequence is not obvious: a negative delta-v gives a negative reserve,
        so a stage reports more propellant available for ascent than it carries.
        `Stage` already refuses to promise away propellant it does not have, and
        this closes the same hole one layer down.

        Raises:
            ValueError: If the burn would create propellant or run an impossible
                engine.
        """
        if self.delta_v < 0:
            raise ValueError(
                f"a burn cannot have negative delta_v, got {self.delta_v}. A recovery "
                "burn slows the stage down; it is still a positive velocity change."
            )
        if self.isp <= 0:
            raise ValueError(f"a burn needs a positive isp, got {self.isp}")


def recovery_propellant(dry_mass: float, burns: Sequence[Burn]) -> float:
    """Propellant a stage must hold back to perform a sequence of burns.

    Burns compose multiplicatively, and each one has to lift the propellant for
    every burn that comes after it. Pass them in reverse chronological order,
    last burn first, which is how the maths naturally unwinds.

    Args:
        dry_mass: Stage mass once everything is burnt, tonnes.
        burns: Manoeuvres in reverse order, last burn first.

    Returns:
        Propellant that must be reserved, tonnes.
    """
    ratio = 1.0
    for burn in burns:
        ratio *= mass_ratio(burn.delta_v, burn.isp)
    return dry_mass * (ratio - 1.0)


def mass_at_separation(dry_mass: float, burns: Sequence[Burn]) -> float:
    """Total stage mass at separation, including everything it needs to get home.

    Args:
        dry_mass: Stage mass once everything is burnt, tonnes.
        burns: Recovery manoeuvres in reverse order, last burn first.

    Returns:
        Stage mass at the moment of separation, tonnes.
    """
    return dry_mass + recovery_propellant(dry_mass, burns)


def landing_delta_v(
    residual_velocity: float, burn_seconds: float, throttle_penalty: float = 0.0
) -> float:
    """Build a landing budget from its parts rather than quoting one number.

    A landing burn pays for three things: killing the speed it arrives with,
    fighting gravity for the whole duration of the burn, and running engines
    deeply throttled where they are least efficient.

    Args:
        residual_velocity: Speed at the start of the landing burn, m/s.
        burn_seconds: Duration of the burn, seconds.
        throttle_penalty: Extra velocity budget covering throttling and
            manoeuvring inefficiency, m/s.

    Returns:
        Total landing budget, m/s.
    """
    return residual_velocity + G0 * burn_seconds + throttle_penalty


class RecoveryProfile(StrEnum):
    """How a first stage gets home, from cheapest to most demanding."""

    EXPENDABLE = "expendable"
    """It does not. Nothing is held back, and the stage is lost."""

    DRONESHIP = "droneship"
    """Carry on downrange and land on a ship. Only survival, no return trip."""

    RTLS = "rtls"
    """Fly back to where it launched from. The expensive one."""

    TOWER_CATCH = "tower_catch"
    """Fly back and be caught by the launch tower. No legs, same flight cost."""


@dataclass(frozen=True, slots=True)
class ProfileDescription:
    """What a recovery profile costs, and how to explain it.

    Attributes:
        profile: Which profile this describes.
        label: Short human-readable name.
        explanation: One sentence a beginner can act on.
        burns: The manoeuvres it requires, last burn first.
    """

    profile: RecoveryProfile
    label: str
    explanation: str
    burns: tuple[Burn, ...]

    @property
    def total_delta_v(self) -> float:
        """Sum of the manoeuvres, m/s. Not their cost, only their size."""
        return sum(burn.delta_v for burn in self.burns)

    def propellant_per_tonne(self) -> float:
        """Propellant reserved per tonne of stage dry mass, tonnes per tonne."""
        return recovery_propellant(1.0, self.burns)

    def as_recovery(self) -> "Recovery | None":
        """Build a library ``Recovery`` from this profile.

        Returns:
            The recovery description, or None for an expendable stage.
        """
        from rocketry.models import Recovery, RecoveryMode

        if self.profile is RecoveryProfile.EXPENDABLE:
            return None
        return Recovery(mode=RecoveryMode(self.profile.value), burns=self.burns)


RECOVERY_PROFILES: dict[RecoveryProfile, ProfileDescription] = {
    RecoveryProfile.EXPENDABLE: ProfileDescription(
        profile=RecoveryProfile.EXPENDABLE,
        label="Expendable",
        explanation=(
            "Nothing is held back, so every tonne of propellant accelerates the "
            "payload. The stage is destroyed on reentry."
        ),
        burns=(),
    ),
    RecoveryProfile.DRONESHIP: ProfileDescription(
        profile=RecoveryProfile.DRONESHIP,
        label="Land on a ship downrange",
        explanation=(
            "The stage keeps flying the way it was already going and lands at "
            "sea. It only has to survive reentry and stop, not turn around."
        ),
        burns=(
            Burn(delta_v=600.0, isp=300.0, label="landing burn"),
            Burn(delta_v=1300.0, isp=311.0, label="entry burn"),
        ),
    ),
    RecoveryProfile.RTLS: ProfileDescription(
        profile=RecoveryProfile.RTLS,
        label="Fly back to the launch site",
        explanation=(
            "The stage must cancel everything it gained downrange and travel all "
            "the way back. That propellant is carried uphill first."
        ),
        burns=(
            Burn(delta_v=600.0, isp=300.0, label="landing burn"),
            Burn(delta_v=500.0, isp=311.0, label="entry burn"),
            Burn(delta_v=1500.0, isp=311.0, label="boostback burn"),
        ),
    ),
    RecoveryProfile.TOWER_CATCH: ProfileDescription(
        profile=RecoveryProfile.TOWER_CATCH,
        label="Fly back and be caught by the tower",
        explanation=(
            "The same flight as returning to the launch site, without landing "
            "legs to carry. Super Heavy's profile."
        ),
        burns=(
            Burn(delta_v=600.0, isp=330.0, label="landing burn"),
            Burn(delta_v=1800.0, isp=330.0, label="boostback burn"),
        ),
    ),
}


def profile_for(profile: RecoveryProfile) -> ProfileDescription:
    """Look up what a recovery profile costs.

    Args:
        profile: Which profile.

    Returns:
        Its description and burns.
    """
    return RECOVERY_PROFILES[profile]
