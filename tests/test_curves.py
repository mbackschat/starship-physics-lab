"""Two curves that answer two different questions, and must not be confused.

Chapter 1 shows both. Getting them the wrong way round is the single most common
misreading of the rocket equation, so the shapes are pinned here:

- during a burn, equal chunks of propellant buy *more and more* speed, because
  the vehicle keeps getting lighter;
- across designs, equal chunks of propellant *loaded* buy less and less, because
  the logarithm flattens.

Both are true at once. The tests assert the two curves genuinely bend in
opposite directions, so a refactor cannot quietly swap them.
"""

import pytest

from labbook.curves import burn_trace, loading_sweep
from rocketry.tsiolkovsky import delta_v


def test_burn_starts_at_rest_and_ends_at_the_rocket_equation():
    trace = burn_trace(dry_t=10.0, propellant_t=90.0, isp_s=350.0, steps=40)
    assert trace[0].velocity_ms == pytest.approx(0.0)
    assert trace[0].burnt_t == pytest.approx(0.0)
    assert trace[-1].burnt_t == pytest.approx(90.0)
    assert trace[-1].velocity_ms == pytest.approx(delta_v(100.0, 10.0, 350.0))


def test_burn_mass_falls_from_wet_to_dry():
    trace = burn_trace(dry_t=10.0, propellant_t=90.0, isp_s=350.0, steps=40)
    assert trace[0].mass_t == pytest.approx(100.0)
    assert trace[-1].mass_t == pytest.approx(10.0)
    masses = [sample.mass_t for sample in trace]
    assert masses == sorted(masses, reverse=True)


def test_burn_speeds_up_as_the_tanks_empty():
    # Equal steps of propellant, so any difference in speed gained is the
    # physics and not the sampling.
    trace = burn_trace(dry_t=10.0, propellant_t=90.0, isp_s=350.0, steps=40)
    first_gain = trace[1].velocity_ms - trace[0].velocity_ms
    last_gain = trace[-1].velocity_ms - trace[-2].velocity_ms
    assert last_gain > first_gain * 5


def test_loading_more_propellant_buys_less_and_less():
    sweep = loading_sweep(dry_t=10.0, isp_s=350.0, up_to_t=900.0, steps=40)
    first_gain = sweep[1].delta_v_ms - sweep[0].delta_v_ms
    last_gain = sweep[-1].delta_v_ms - sweep[-2].delta_v_ms
    assert last_gain < first_gain


def test_the_two_curves_bend_in_opposite_directions():
    trace = burn_trace(dry_t=10.0, propellant_t=900.0, isp_s=350.0, steps=40)
    sweep = loading_sweep(dry_t=10.0, isp_s=350.0, up_to_t=900.0, steps=40)

    def bend(values: list[float]) -> float:
        return (values[-1] - values[-2]) - (values[1] - values[0])

    assert bend([sample.velocity_ms for sample in trace]) > 0
    assert bend([sample.delta_v_ms for sample in sweep]) < 0


def test_loading_sweep_starts_from_an_empty_rocket():
    sweep = loading_sweep(dry_t=10.0, isp_s=350.0, up_to_t=900.0, steps=40)
    assert sweep[0].propellant_t == pytest.approx(0.0)
    assert sweep[0].delta_v_ms == pytest.approx(0.0)
    assert sweep[-1].propellant_t == pytest.approx(900.0)


def test_both_curves_honour_the_step_count():
    assert len(burn_trace(dry_t=1.0, propellant_t=9.0, isp_s=300.0, steps=12)) == 13
    assert len(loading_sweep(dry_t=1.0, isp_s=300.0, up_to_t=90.0, steps=12)) == 13


@pytest.mark.parametrize("steps", [0, -3])
def test_a_curve_needs_at_least_one_step(steps: int):
    with pytest.raises(ValueError, match="at least one step"):
        burn_trace(dry_t=1.0, propellant_t=9.0, isp_s=300.0, steps=steps)
    with pytest.raises(ValueError, match="at least one step"):
        loading_sweep(dry_t=1.0, isp_s=300.0, up_to_t=90.0, steps=steps)


def test_a_rocket_with_no_dry_mass_is_rejected_rather_than_dividing_by_zero():
    with pytest.raises(ValueError, match="positive"):
        burn_trace(dry_t=0.0, propellant_t=9.0, isp_s=300.0)
    with pytest.raises(ValueError, match="positive"):
        loading_sweep(dry_t=0.0, isp_s=300.0, up_to_t=90.0)
