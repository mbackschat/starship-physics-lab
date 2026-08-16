"""Fly the rocket, and account for every metre per second it does not get.

The rocket equation says what a vehicle could do in empty space. This says what
it actually achieves once gravity, air and steering have taken their cut, and
where each of those cuts went.

The decomposition is exact rather than approximate. Integrating the equation of
motion along the velocity vector gives

    v_final = dv_ideal - gravity loss - drag loss - steering loss

which is the identity the tests hold the model to, and the chart a beginner
should see: one bar of what you paid for, three bars of where it went.

Integrated with a fixed-step RK4 written out longhand. That is not stubbornness:
this runs in the reader's browser under WebAssembly, and pulling scipy in for
one solver would add roughly 15 MB to the download.
"""

import math
from dataclasses import dataclass, field
from typing import Final

from rocketry.atmosphere import density, pressure_ratio
from rocketry.constants import G0, R_EARTH_M
from rocketry.models import Engine, Stage
from rocketry.vehicle import VehicleAnalysis

_STATE_SIZE = 9

MAX_GUIDED_PITCH_RAD: Final[float] = math.pi / 4.0
"""Steepest angle the closed loop will thrust at, radians. Forty-five degrees.

Past 45 degrees more of the thrust is holding the rocket up than accelerating
it, and a stage that cannot hold itself up even at 45 degrees is better off
getting fast, because **speed is what holds you up**. Without this cap the
guidance saturates pointing straight up and stays there: Saturn V's third stage
spent its entire burn hovering and gained 4 m/s of the 2,000 it should have.
"""


@dataclass(frozen=True, slots=True)
class AscentSettings:
    """How the rocket is flown, and how finely it is simulated.

    The defaults describe a competently flown gravity turn. They are exposed so
    a reader can fly it badly on purpose and watch the losses grow, which
    teaches more than any amount of prose about why the turn matters.

    Attributes:
    Real vehicles fly **open loop** through the atmosphere, where the pitch
    program must not fight the airflow, and hand over to **closed-loop guidance**
    above it. This models both, because modelling only the first produced a
    ballistic arc: every vehicle in the library climbed past 200 km and then fell
    while still burning, and four of them reached the ground.

    Attributes:
        turn_start_speed: Speed at which the vehicle stops going straight up,
            m/s.
        turn_complete_speed: Speed by which the pitch program has finished
            tipping over, m/s. Calibrated so Falcon 9 stages at 76 km and 2,260
            m/s, against a published 65 to 85 km at roughly 2,300.
        turn_shape: How eagerly it tips. Above 1 tips over quickly and flies
            flat; below 1 hangs on to the vertical and pays for it in gravity
            loss.
        drag_coefficient: Drag coefficient of the stack, dimensionless.
        guidance_handover_altitude: Height above which the closed loop takes
            over from the pitch program, metres. Only ever on a stage above the
            first, so a rocket flown into the ground low down still hits it,
            which is a lesson rather than a bug.
        insertion_altitude: Height the closed loop aims to arrive at with no
            climb rate left, metres. The 200 km the rest of the project uses for
            low Earth orbit.
        time_step: Integration step, seconds.
        sample_every: How often to record a point for plotting, seconds.
    """

    turn_start_speed: float = 60.0
    turn_complete_speed: float = 2000.0
    turn_shape: float = 1.0
    drag_coefficient: float = 0.5
    guidance_handover_altitude: float = 60_000.0
    insertion_altitude: float = 200_000.0
    time_step: float = 0.25
    sample_every: float = 1.0


@dataclass(frozen=True, slots=True)
class AscentSample:
    """One recorded moment of the flight.

    Attributes:
        time_s: Seconds since liftoff.
        altitude_m: Height above sea level, metres.
        downrange_m: Horizontal distance from the pad, metres.
        speed_ms: Speed relative to the ground, m/s.
        vertical_speed_ms: Rate of climb, m/s.
        mass_t: Current vehicle mass, tonnes.
        thrust_tf: Current thrust, tonnes-force.
        twr: Thrust-to-weight ratio right now.
        acceleration_g: Net acceleration felt, in g.
        dynamic_pressure_pa: Aerodynamic pressure on the vehicle, Pa.
        flight_path_angle_deg: Angle of the velocity above the horizon.
        stage_index: Which stage is burning, counting from zero.
    """

    time_s: float
    altitude_m: float
    downrange_m: float
    speed_ms: float
    vertical_speed_ms: float
    mass_t: float
    thrust_tf: float
    twr: float
    acceleration_g: float
    dynamic_pressure_pa: float
    flight_path_angle_deg: float
    stage_index: int


@dataclass(frozen=True, slots=True)
class StageEvent:
    """A stage separation.

    Attributes:
        time_s: Seconds since liftoff.
        stage_index: Index of the stage that just finished.
        name: Name of that stage.
        altitude_m: Height at separation, metres.
        downrange_m: Horizontal distance from the pad at separation, metres.
        speed_ms: Speed at separation, m/s.
    """

    time_s: float
    stage_index: int
    name: str
    altitude_m: float
    downrange_m: float
    speed_ms: float


@dataclass(frozen=True, slots=True)
class AscentResult:
    """The flight, and the accounting.

    Attributes:
        samples: Recorded points, in time order.
        events: Stage separations.
        ideal_delta_v: What the engines produced, m/s.
        gravity_loss: Spent holding the vehicle up, m/s.
        drag_loss: Spent pushing air aside, m/s.
        steering_loss: Spent thrusting off the direction of travel, m/s.
        final_speed: Speed at the end of the last burn, m/s.
        final_altitude_m: Height at the end of the last burn, metres.
        crashed: Whether it came back down before finishing its burn. A badly
            flown rocket really does do this, and saying so plainly beats
            returning a trajectory that quietly means nothing.
    """

    samples: tuple[AscentSample, ...]
    events: tuple[StageEvent, ...]
    ideal_delta_v: float
    gravity_loss: float
    drag_loss: float
    steering_loss: float
    final_speed: float
    final_altitude_m: float
    crashed: bool = False

    @property
    def reached_space(self) -> bool:
        """Whether it got above the Karman line at 100 km."""
        return self.final_altitude_m >= 100_000.0

    @property
    def total_losses(self) -> float:
        """Everything the atmosphere and gravity took, m/s."""
        return self.gravity_loss + self.drag_loss + self.steering_loss

    @property
    def loss_fraction(self) -> float:
        """Share of the engines' work that never became speed."""
        return self.total_losses / self.ideal_delta_v if self.ideal_delta_v else 0.0

    @property
    def max_dynamic_pressure_pa(self) -> float:
        """The worst aerodynamic loading of the flight, Pa."""
        return max((sample.dynamic_pressure_pa for sample in self.samples), default=0.0)

    @property
    def breakdown(self) -> dict[str, float]:
        """Where the engines' work went, ready to chart."""
        return {
            "Speed gained": self.final_speed,
            "Gravity loss": self.gravity_loss,
            "Drag loss": self.drag_loss,
            "Steering loss": self.steering_loss,
        }


@dataclass(slots=True)
class _Burn:
    """A single stage burning, with everything the integrator needs precomputed."""

    index: int
    stage: Stage
    engine: Engine
    burnout_mass_t: float
    jettison_t: float
    area_m2: float
    settings: AscentSettings
    seconds_after_burnout: float = 0.0
    """Burn time still to come once this stage is done, seconds.

    The closed loop aims at the *end of the ascent*, not the end of the current
    stage. Levelling off at every separation would be wrong: a second stage is
    supposed to hand over still climbing.
    """
    thrust_sl_n: float = field(init=False)
    thrust_vac_n: float = field(init=False)
    isp_sl_s: float = field(init=False)
    isp_vac_s: float = field(init=False)

    def __post_init__(self) -> None:
        """Resolve engine performance once rather than inside the inner loop."""
        count = self.stage.engine_count
        vac = self.engine.thrust_vac_tf * count
        sea = (self.engine.thrust_sl_tf or self.engine.thrust_vac_tf) * count
        self.thrust_vac_n = vac * 1000.0 * G0
        self.thrust_sl_n = sea * 1000.0 * G0
        self.isp_vac_s = self.engine.isp_vac_s
        self.isp_sl_s = self.engine.isp_sl_s or self.engine.isp_vac_s

    def thrust_n(self, altitude_m: float) -> float:
        """Thrust at an altitude, blending sea level to vacuum by ambient pressure.

        Args:
            altitude_m: Height above sea level, metres.

        Returns:
            Thrust, newtons.
        """
        ratio = pressure_ratio(altitude_m)
        return self.thrust_vac_n + (self.thrust_sl_n - self.thrust_vac_n) * ratio

    def isp_s(self, altitude_m: float) -> float:
        """Specific impulse at an altitude.

        Args:
            altitude_m: Height above sea level, metres.

        Returns:
            Specific impulse, seconds.
        """
        ratio = pressure_ratio(altitude_m)
        return self.isp_vac_s + (self.isp_sl_s - self.isp_vac_s) * ratio


def simulate(
    analysis: VehicleAnalysis,
    settings: AscentSettings | None = None,
    engines: dict[str, Engine] | None = None,
) -> AscentResult:
    """Fly a vehicle from the pad to the end of its last burn.

    Args:
        analysis: A vehicle already run through :func:`rocketry.vehicle.analyse`.
        settings: How to fly it. Defaults to a competently flown gravity turn.
        engines: Engine lookup. Defaults to the shared rocket library.

    Returns:
        The flight and its loss accounting.

    Raises:
        ValueError: If the vehicle cannot lift its own weight, which is a design
            error worth naming rather than integrating through.
    """
    from rocketry.library import load

    config = settings or AscentSettings()
    catalogue = engines if engines is not None else load().engines
    burns = _plan(analysis, catalogue, config)
    _check_it_can_fly(burns[0], analysis.liftoff_mass_t)

    state = [0.0, 0.0, 0.0, 0.001, analysis.liftoff_mass_t, 0.0, 0.0, 0.0, 0.0]
    time = 0.0
    samples: list[AscentSample] = []
    events: list[StageEvent] = []
    next_sample = 0.0

    crashed = False
    for burn in burns:
        while state[4] > burn.burnout_mass_t and not crashed:
            if time >= next_sample:
                samples.append(_sample(time, state, burn, config))
                next_sample += config.sample_every
            step = min(config.time_step, _step_to_burnout(state, burn, config))
            if step <= 0:
                break
            state = _rk4(state, step, burn, config)
            time += step
            if state[1] < 0.0 and time > 5.0:
                state[1] = 0.0
                crashed = True
        samples.append(_sample(time, state, burn, config))
        if crashed:
            break
        if burn is not burns[-1]:
            events.append(
                StageEvent(
                    time_s=time,
                    stage_index=burn.index,
                    name=burn.stage.name,
                    altitude_m=state[1],
                    downrange_m=state[0],
                    speed_ms=math.hypot(state[2], state[3]),
                )
            )
            state[4] -= burn.jettison_t

    return AscentResult(
        samples=tuple(samples),
        events=tuple(events),
        ideal_delta_v=state[8],
        gravity_loss=state[5],
        drag_loss=state[6],
        steering_loss=state[7],
        final_speed=math.hypot(state[2], state[3]),
        final_altitude_m=state[1],
        crashed=crashed,
    )


def _plan(
    analysis: VehicleAnalysis, engines: dict[str, Engine], settings: AscentSettings
) -> list[_Burn]:
    """Turn a vehicle analysis into the burns the integrator will fly.

    Args:
        analysis: The vehicle.
        engines: Engine lookup.
        settings: Flight settings.

    Returns:
        One burn per stage, in launch order.

    Raises:
        KeyError: If a stage names an engine that is not in the catalogue.
    """
    durations = [
        _burn_seconds(result.ascent_propellant_t, engines[result.stage.engine], result.stage)
        for result in analysis.stages
    ]
    return [
        _Burn(
            index=index,
            stage=result.stage,
            engine=engines[result.stage.engine],
            burnout_mass_t=result.burnout_mass_t,
            jettison_t=result.burnout_mass_t - result.mass_above_t,
            area_m2=math.pi * (result.stage.diameter_m / 2.0) ** 2,
            settings=settings,
            seconds_after_burnout=sum(durations[index + 1 :]),
        )
        for index, result in enumerate(analysis.stages)
    ]


def _burn_seconds(propellant_t: float, engine: Engine, stage: Stage) -> float:
    """How long a stage burns at full thrust.

    Vacuum figures throughout. This only ever feeds the guidance's estimate of
    how much time it has left, so being a few per cent long at sea level costs
    nothing worth an altitude-dependent integral.

    Args:
        propellant_t: Propellant spent accelerating, tonnes.
        engine: The stage's engine.
        stage: The stage.

    Returns:
        Burn duration, seconds.
    """
    flow = engine.thrust_vac_tf * stage.engine_count / engine.isp_vac_s
    return propellant_t / flow if flow > 0 else 0.0


def _check_it_can_fly(first: _Burn, liftoff_mass_t: float) -> None:
    """Refuse to integrate a rocket that cannot leave the pad.

    Args:
        first: The first stage's burn.
        liftoff_mass_t: Fully fuelled stack mass, tonnes.

    Raises:
        ValueError: If thrust does not exceed weight at liftoff.
    """
    twr = first.thrust_n(0.0) / (liftoff_mass_t * 1000.0 * G0)
    if twr <= 1.0:
        raise ValueError(
            f"thrust-to-weight at liftoff is {twr:.2f}: this rocket cannot leave the pad. "
            "Add engines, or take mass out of it."
        )


def _gravity(altitude_m: float) -> float:
    """Gravitational acceleration at an altitude.

    Args:
        altitude_m: Height above sea level, metres.

    Returns:
        Acceleration, m/s^2.
    """
    return G0 * (R_EARTH_M / (R_EARTH_M + altitude_m)) ** 2


def _guided_pitch_rad(
    state: list[float], burn: _Burn, thrust_n: float, flow_t_s: float
) -> float:
    """Thrust direction above the horizon, from the closed loop.

    Steers to arrive at `insertion_altitude` with no climb rate left, which is
    what putting something in orbit means and what the pitch program alone can
    never do. `6·Δh/T² - 4·v/T` is the standard terminal law: it is the constant
    the vertical acceleration would have to average to hit both the height and
    the zero climb rate at the same moment, given how much burn time is left.

    Gravity is added back because the rocket has to pay for it, and the
    centrifugal term is subtracted because going sideways fast pays some of it
    already. That subtraction is why the demanded angle falls away to nothing as
    the vehicle approaches orbital speed, and it is the whole lesson of the
    chapter expressed as a control law.

    Args:
        state: Current state.
        burn: The stage currently burning.
        thrust_n: Thrust right now, newtons.
        flow_t_s: Propellant consumption right now, tonnes per second.

    Returns:
        Pitch angle above horizontal, radians, capped at
        :data:`MAX_GUIDED_PITCH_RAD` in both directions.
    """
    _, altitude, vx, vy, mass_t, *_ = state
    remaining = burn.seconds_after_burnout
    if flow_t_s > 0:
        remaining += max(0.0, (mass_t - burn.burnout_mass_t) / flow_t_s)
    remaining = max(5.0, remaining)

    climb = burn.settings.insertion_altitude - altitude
    wanted = 6.0 * climb / (remaining * remaining) - 4.0 * vy / remaining
    needed = _gravity(altitude) - vx * vx / (R_EARTH_M + altitude) + wanted

    limit = math.sin(MAX_GUIDED_PITCH_RAD)
    share = needed * max(1.0, mass_t * 1000.0) / thrust_n if thrust_n > 0 else 0.0
    return math.asin(min(limit, max(-limit, share)))


def _pitch_rad(speed: float, settings: AscentSettings) -> float:
    """Thrust direction above the horizon, from the open-loop pitch program.

    A prescribed turn rather than a free gravity turn: it is stable, it is
    tunable by a reader with a slider, and it produces the same lesson. It flies
    the vehicle out of the atmosphere, where a real one cannot steer freely
    either, and then :func:`_guided_pitch_rad` takes over.

    Args:
        speed: Current speed, m/s.
        settings: Flight settings.

    Returns:
        Pitch angle above horizontal, radians.
    """
    span = settings.turn_complete_speed - settings.turn_start_speed
    if span <= 0:
        return 0.0
    progress = (speed - settings.turn_start_speed) / span
    progress = min(1.0, max(0.0, progress))
    return float((math.pi / 2.0) * (1.0 - progress) ** settings.turn_shape)


def _derivatives(state: list[float], burn: _Burn, settings: AscentSettings) -> list[float]:
    """Rate of change of the whole state, including the loss accumulators.

    Args:
        state: Current state.
        burn: The stage currently burning.
        settings: Flight settings.

    Returns:
        Derivatives, in the same order as the state.
    """
    _, altitude, vx, vy, mass_t, *_ = state
    mass_kg = max(1.0, mass_t * 1000.0)
    speed = math.hypot(vx, vy)

    heading = (vx / speed, vy / speed) if speed > 1e-6 else (0.0, 1.0)

    thrust = burn.thrust_n(altitude)
    flow_kg_s = thrust / (burn.isp_s(altitude) * G0)

    # Open loop through the atmosphere, closed loop above it, as a real vehicle
    # flies. Never on the first stage: that is where a reader is allowed to fly
    # it into the ground.
    if burn.index > 0 and altitude >= settings.guidance_handover_altitude:
        pitch = _guided_pitch_rad(state, burn, thrust, flow_kg_s / 1000.0)
    else:
        pitch = _pitch_rad(speed, settings)
    direction = (math.cos(pitch), math.sin(pitch))

    rho = density(altitude)
    drag = 0.5 * rho * speed * speed * settings.drag_coefficient * burn.area_m2
    gravity = _gravity(altitude)

    ax = (thrust * direction[0] - drag * heading[0]) / mass_kg
    ay = (thrust * direction[1] - drag * heading[1]) / mass_kg - gravity

    cos_alpha = direction[0] * heading[0] + direction[1] * heading[1]
    sin_gamma = heading[1]

    # Effective gravity. Going sideways fast holds the vehicle up: at orbital
    # speed the two cancel exactly, which is what being in orbit means. Without
    # this term a rocket flying horizontally simply falls, and the simulated
    # trajectory climbs to absurd altitudes trying to compensate.
    effective_gravity = gravity - vx * vx / (R_EARTH_M + altitude)
    ay += vx * vx / (R_EARTH_M + altitude)

    return [
        vx,
        vy,
        ax,
        ay,
        -flow_kg_s / 1000.0,
        effective_gravity * sin_gamma,
        drag / mass_kg,
        (thrust / mass_kg) * (1.0 - cos_alpha),
        thrust / mass_kg,
    ]


def _rk4(state: list[float], step: float, burn: _Burn, settings: AscentSettings) -> list[float]:
    """Advance the state by one fixed RK4 step.

    Args:
        state: Current state.
        step: Time step, seconds.
        burn: The stage currently burning.
        settings: Flight settings.

    Returns:
        The new state.
    """
    k1 = _derivatives(state, burn, settings)
    s2 = [state[i] + 0.5 * step * k1[i] for i in range(_STATE_SIZE)]
    k2 = _derivatives(s2, burn, settings)
    s3 = [state[i] + 0.5 * step * k2[i] for i in range(_STATE_SIZE)]
    k3 = _derivatives(s3, burn, settings)
    s4 = [state[i] + step * k3[i] for i in range(_STATE_SIZE)]
    k4 = _derivatives(s4, burn, settings)
    return [
        state[i] + (step / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i])
        for i in range(_STATE_SIZE)
    ]


def _step_to_burnout(state: list[float], burn: _Burn, settings: AscentSettings) -> float:
    """Time until this stage runs dry, so the last step lands exactly on burnout.

    Args:
        state: Current state.
        burn: The stage currently burning.
        settings: Flight settings.

    Returns:
        Seconds remaining in this burn.
    """
    flow = -_derivatives(state, burn, settings)[4]
    if flow <= 0:
        return 0.0
    return (state[4] - burn.burnout_mass_t) / flow


def _sample(
    time: float, state: list[float], burn: _Burn, settings: AscentSettings
) -> AscentSample:
    """Record one plottable point.

    Args:
        time: Seconds since liftoff.
        state: Current state.
        burn: The stage currently burning.
        settings: Flight settings.

    Returns:
        The sample.
    """
    _, altitude, vx, vy, mass_t, *_ = state
    speed = math.hypot(vx, vy)
    thrust = burn.thrust_n(altitude)
    weight = mass_t * 1000.0 * _gravity(altitude)
    rho = density(altitude)
    derivative = _derivatives(state, burn, settings)
    return AscentSample(
        time_s=time,
        altitude_m=altitude,
        downrange_m=state[0],
        speed_ms=speed,
        vertical_speed_ms=vy,
        mass_t=mass_t,
        thrust_tf=thrust / (1000.0 * G0),
        twr=thrust / weight if weight else 0.0,
        acceleration_g=math.hypot(derivative[2], derivative[3]) / G0,
        dynamic_pressure_pa=0.5 * rho * speed * speed,
        flight_path_angle_deg=math.degrees(math.atan2(vy, max(1e-9, abs(vx)))) if speed else 90.0,
        stage_index=burn.index,
    )
