"""The Starship case study: weighing a rocket, and what its weight implies.

Kept separate from the physics core because it is presentation of one specific
argument, not general mechanics. Kept out of the page files because it is the
part of the app most likely to be quoted back at somebody, and it should
therefore be tested rather than assembled inline.

The honesty rule this module exists to enforce: the mass arriving in orbit is
fixed by the rocket equation and does not move. Only its composition is up for
debate, and the input that decides the composition is unpublished.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from rocketry.library import Library
from rocketry.tsiolkovsky import mass_after_burn, propellant_burnt
from rocketry.vehicle import LEO_MISSION_DELTA_V, VehicleAnalysis, scenario


@dataclass(frozen=True, slots=True)
class Weighing:
    """What an observed burn reveals about a vehicle's mass.

    Attributes:
        propellant_t: Propellant the burn consumed, tonnes.
        delta_v: Velocity change it produced, m/s.
        isp: Specific impulse of the engine used, seconds.
        mass_after_t: What the vehicle weighed when the burn ended, tonnes.
    """

    propellant_t: float
    delta_v: float
    isp: float
    mass_after_t: float

    @property
    def mass_before_t(self) -> float:
        """What it weighed when the burn started, tonnes."""
        return self.mass_after_t + self.propellant_t

    def dry_mass_t(self, residual_t: float) -> float:
        """Dry mass implied by assuming how much propellant was still aboard.

        This is the step where measurement stops and assumption begins, and it
        is the reason two people can watch the same burn and disagree by 100
        tonnes.

        Args:
            residual_t: Propellant still in the tanks after the burn, tonnes.

        Returns:
            Implied dry mass, tonnes.
        """
        return self.mass_after_t - residual_t

    def burn_seconds(self, thrust_tf: float, engine_isp: float) -> float:
        """How long an engine would have to run to consume this propellant.

        Args:
            thrust_tf: Engine thrust, tonnes-force.
            engine_isp: Engine specific impulse, seconds.

        Returns:
            Burn duration, seconds.
        """
        per_second = propellant_burnt(thrust_tf=thrust_tf, isp=engine_isp, seconds=1.0)
        return self.propellant_t / per_second if per_second else 0.0


def weigh_from_burn(*, propellant_t: float, delta_v: float, isp: float) -> Weighing:
    """Weigh a vehicle from a burn you watched from the ground.

    Given how much propellant a burn used and how much it changed the vehicle's
    speed, the rocket equation gives its mass. No access to the vehicle
    required, which is what makes the method interesting.

    Args:
        propellant_t: Propellant consumed, tonnes.
        delta_v: Observed velocity change, m/s.
        isp: Specific impulse of the engine used, seconds.

    Returns:
        The weighing.
    """
    return Weighing(
        propellant_t=propellant_t,
        delta_v=delta_v,
        isp=isp,
        mass_after_t=mass_after_burn(propellant_t, delta_v, isp),
    )


@dataclass(frozen=True, slots=True)
class DryMassEstimate:
    """One published or derived view of how heavy Starship is.

    Attributes:
        dry_mass_t: The estimate, tonnes.
        label: Short name for a chart marker.
        source: Where it comes from.
        contested: Whether it is disputed rather than measured.
    """

    dry_mass_t: float
    label: str
    source: str
    contested: bool = True


ESTIMATES: tuple[DryMassEstimate, ...] = (
    DryMassEstimate(
        dry_mass_t=85.0,
        label="Wikipedia, V2",
        source="Listed for Starship Block 2. No primary source for the figure.",
    ),
    DryMassEstimate(
        dry_mass_t=100.0,
        label="Wikipedia, V1",
        source="Listed for Starship Block 1.",
    ),
    DryMassEstimate(
        dry_mass_t=120.0,
        label="SpaceX target, 2019",
        source="Musk, September 2019: aiming for 120 t by Mk4 or Mk5.",
    ),
    DryMassEstimate(
        dry_mass_t=160.0,
        label="What the 100 t claim needs",
        source="Derived: 300 t reaches orbit, minus 100 t payload and 40 t residual.",
    ),
    DryMassEstimate(
        dry_mass_t=200.0,
        label="Musk, 2019, measured",
        source="Musk, September 2019: 'Mk1 ship is around 200 tons dry.' No heat shield.",
        contested=False,
    ),
    DryMassEstimate(
        dry_mass_t=220.0,
        label="The article's estimate",
        source="Derived from a 14 s relight, the hover-thrust bracket and Musk's 2019 figure.",
    ),
)
"""Every credible view, lightest first, so the disagreement is visible at a glance."""


@dataclass(frozen=True, slots=True)
class PayloadPoint:
    """Payload at one assumed dry mass.

    Attributes:
        dry_mass_t: The assumption, tonnes.
        payload_t: What the vehicle then carries, tonnes.
        mass_in_orbit_t: Everything that arrives, tonnes: payload, the stage
            itself, and the propellant it still has for coming home.
        analysis: The full vehicle analysis behind the point.
    """

    dry_mass_t: float
    payload_t: float
    mass_in_orbit_t: float
    analysis: VehicleAnalysis


def payload_curve(
    library: Library,
    vehicle_key: str,
    dry_masses: Iterable[float],
    target_delta_v: float = LEO_MISSION_DELTA_V,
) -> list[PayloadPoint]:
    """Payload as a function of how heavy you believe the upper stage is.

    The mission is held fixed and the payload is solved for, which is the only
    way round that answers the question a reader actually has. The mass reaching
    orbit then comes out identical at every point on the curve. That is not an
    artefact of the code; it is the rocket equation, and it is the single most
    important thing this app has to convey.

    Args:
        library: The rocket library.
        vehicle_key: Vehicle to examine.
        dry_masses: Upper stage dry masses to try, tonnes.
        target_delta_v: Velocity the stack must produce, m/s.

    Returns:
        One point per assumption, lightest first.
    """
    upper_stage_key = library.vehicle(vehicle_key).stages[-1]
    points: list[PayloadPoint] = []
    for dry_mass in sorted(dry_masses):
        case = scenario(library, vehicle_key, **{upper_stage_key: {"dry_mass_t": dry_mass}})
        payload = case.solve_payload(target_delta_v)
        analysis = case.at_payload(payload)
        last = analysis.stages[-1]
        points.append(
            PayloadPoint(
                dry_mass_t=dry_mass,
                payload_t=payload,
                mass_in_orbit_t=last.burnout_mass_t,
                analysis=analysis,
            )
        )
    return points
