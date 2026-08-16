"""Validated descriptions of engines, stages, vehicles and flights.

Every entry carries its provenance. That is not decoration: the central
argument about Starship rests on an unpublished number, and a model that cannot
tell a measurement from a guess would hide exactly the thing that matters.
"""

import datetime as dt
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from rocketry.limits import ModellingLimit, limit_for
from rocketry.reuse import Burn, recovery_propellant


class Provenance(StrEnum):
    """Where a number came from, and therefore how much weight it can bear."""

    PUBLISHED = "published"
    """Stated by the operator or a primary reference."""

    ESTIMATED = "estimated"
    """Derived from evidence by a third party. Defensible, not authoritative."""

    CONTESTED = "contested"
    """Credible sources disagree materially. Must be shown as a range."""

    DERIVED = "derived"
    """Computed from other entries in this library."""

    ANNOUNCED = "announced"
    """Stated as a future intention. Not yet demonstrated."""


class VehicleCategory(StrEnum):
    """What kind of thing an entry is, which decides how the UI presents it."""

    FLOWN = "flown"
    """Has actually launched."""

    ANNOUNCED = "announced"
    """Officially planned but not yet flown."""

    CONCEPT = "concept"
    """A thought experiment. Never existed and may never."""

    HISTORIC = "historic"
    """Flew, and is now retired."""


class RecoveryMode(StrEnum):
    """How a stage comes back, which determines what it must hold back."""

    EXPENDABLE = "expendable"
    RTLS = "rtls"
    DRONESHIP = "droneship"
    TOWER_CATCH = "tower_catch"
    CABLE_NET = "cable_net"
    RUNWAY = "runway"


class Sourced(BaseModel):
    """Mixin for anything that must justify its numbers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provenance: Provenance
    source: str = ""
    note: str = ""
    in_article: bool = False
    """Whether the source article discusses this entry.

    Article entries are highlighted in the UI, because they are the ones whose
    numbers a reader may want to check against the text.
    """

    @property
    def is_trustworthy(self) -> bool:
        """Whether this entry can be quoted as fact rather than as an estimate."""
        return self.provenance is Provenance.PUBLISHED


class Engine(Sourced):
    """A rocket engine.

    Thrust in tonnes-force, specific impulse in seconds, mass in kg. Sea-level
    values are None for engines with nozzles too large to run in atmosphere.
    """

    key: str = ""
    name: str
    propellants: str
    thrust_sl_tf: float | None = None
    thrust_vac_tf: float = Field(gt=0)
    isp_sl_s: float | None = None
    isp_vac_s: float = Field(gt=0)
    mass_kg: float | None = None
    min_throttle: float = Field(default=1.0, gt=0, le=1.0)

    @property
    def sea_level_capable(self) -> bool:
        """Whether this engine can be fired at sea level."""
        return self.thrust_sl_tf is not None

    def mass_flow_t_per_s(self, *, vacuum: bool = False) -> float:
        """Propellant consumed per second at full thrust.

        Args:
            vacuum: Use vacuum figures rather than sea level.

        Returns:
            Mass flow, tonnes per second.
        """
        if vacuum or not self.sea_level_capable:
            return self.thrust_vac_tf / self.isp_vac_s
        assert self.thrust_sl_tf is not None and self.isp_sl_s is not None
        return self.thrust_sl_tf / self.isp_sl_s


class Recovery(BaseModel):
    """How a stage returns, and what that costs it.

    Burns are stored in reverse chronological order, last burn first, because
    that is the order in which their mass ratios compose.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    mode: RecoveryMode
    burns: tuple[Burn, ...] = ()

    @property
    def total_delta_v(self) -> float:
        """Sum of all recovery manoeuvres, m/s. Not what they cost, only their size."""
        return sum(burn.delta_v for burn in self.burns)


class Stage(Sourced):
    """One stage of a launch vehicle.

    Masses in tonnes, diameter in metres, specific impulse in seconds.
    """

    key: str = ""
    name: str
    dry_mass_t: float = Field(gt=0)
    propellant_t: float = Field(ge=0)
    engine: str
    engine_count: int = Field(gt=0)
    diameter_m: float = Field(gt=0)
    isp_ascent_s: float = Field(gt=0)
    residual_propellant_t: float = Field(default=0.0, ge=0)
    recovery: Recovery | None = None

    @property
    def wet_mass_t(self) -> float:
        """Stage mass with full tanks, tonnes."""
        return self.dry_mass_t + self.propellant_t

    @property
    def dry_mass_fraction(self) -> float:
        """Dry mass as a fraction of wet mass.

        The headline measure of construction quality, and the reason the Ariane 6
        comparison is instructive: a worse fraction can still lift more.
        """
        return self.dry_mass_t / self.wet_mass_t if self.wet_mass_t else 0.0

    @property
    def is_reusable(self) -> bool:
        """Whether this stage is designed to come back."""
        return self.recovery is not None and self.recovery.mode is not RecoveryMode.EXPENDABLE

    @property
    def recovery_reserve_t(self) -> float:
        """Propellant this stage must hold back for its recovery burns, tonnes."""
        if self.recovery is None:
            return 0.0
        return recovery_propellant(self.dry_mass_t, list(self.recovery.burns))

    @property
    def ascent_propellant_t(self) -> float:
        """Propellant actually available to accelerate the payload, tonnes."""
        return self.propellant_t - self.recovery_reserve_t - self.residual_propellant_t

    @model_validator(mode="after")
    def _propellant_must_cover_its_commitments(self) -> "Stage":
        """Reject a stage that has promised away more propellant than it carries.

        Recovery reserves grow exponentially with the manoeuvres asked of them,
        so a plausible-looking set of burns can quietly exceed the tanks. Caught
        here, at load time, with the numbers in the message; otherwise it
        surfaces much later as an impossible mass ratio deep in a calculation.

        Returns:
            The validated stage.

        Raises:
            ValueError: If reserves plus residuals exceed the propellant load.
        """
        committed = self.recovery_reserve_t + self.residual_propellant_t
        if committed > self.propellant_t:
            raise ValueError(
                f"stage {self.name!r} carries {self.propellant_t:.1f} t of propellant but has "
                f"committed {committed:.1f} t ({self.recovery_reserve_t:.1f} t of recovery "
                f"reserve plus {self.residual_propellant_t:.1f} t of residual). Either give it "
                f"more propellant, reduce its recovery burns, or lower its dry mass."
            )
        return self


class Vehicle(Sourced):
    """A complete launch vehicle, stages listed bottom-up."""

    key: str = ""
    name: str
    operator: str
    stages: tuple[str, ...]
    fairing_t: float = Field(default=0.0, ge=0)
    payload_leo_t: float | None = None
    payload_claim_provenance: Provenance = Provenance.PUBLISHED
    launch_latitude_deg: float = 0.0
    launch_site: str = ""
    staging_speed_kmh: float = 0.0
    category: VehicleCategory = VehicleCategory.FLOWN
    modelling_limits: tuple[ModellingLimit, ...] = ()

    @property
    def payload_is_evidence(self) -> bool:
        """Whether reproducing this vehicle's published payload proves anything.

        A vehicle the model cannot represent may still land on the right number,
        and then agreement is a coincidence rather than a calibration. See
        :mod:`rocketry.limits`.
        """
        return not any(limit_for(limit).affects_payload for limit in self.modelling_limits)


class FlightEvents(BaseModel):
    """Timeline markers from a flight, seconds after liftoff."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stage_separation_s: float | None = None
    seco_s: float | None = None
    relight_s: float | None = None
    splashdown_s: float | None = None


class Flight(Sourced):
    """One observed flight, or one planned flight with its fields still empty.

    A flight that has not happened yet belongs here with nulls, so that its
    absence is visible in every chart rather than silently omitted.
    """

    number: int
    vehicle: str
    date: dt.date | None = None
    date_precision: str = ""
    payload_t: float | None = None
    payload_description: str = ""
    reached_orbit: bool | None = None
    trajectory: str = ""
    max_velocity_kmh: float | None = None
    booster_outcome: str | None = None
    ship_outcome: str | None = None
    events: FlightEvents | None = None

    @property
    def has_flown(self) -> bool:
        """Whether this flight has actually happened."""
        return self.reached_orbit is not None or self.max_velocity_kmh is not None
