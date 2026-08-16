"""The numerical ascent: does a simulated launch behave like a real one?

The rocket equation says what a rocket could do in empty space. This says what
it actually gets, and where the difference went. The decomposition is the point,
so it is tested as an identity rather than as a set of plausible-looking numbers.
"""

import pytest

from rocketry.ascent import AscentSettings, simulate
from rocketry.library import load
from rocketry.vehicle import analyse


@pytest.fixture(scope="module")
def lib():
    return load()


@pytest.fixture(scope="module")
def falcon9(lib):
    return simulate(analyse(lib, "falcon9_droneship"))


@pytest.fixture(scope="module")
def starship(lib):
    return simulate(analyse(lib, "starship_v3"))


class TestEnergyBookkeeping:
    """Every metre per second is accounted for or the model is lying."""

    def test_losses_and_speed_add_up_to_the_ideal_delta_v(self, falcon9):
        """v_final = ideal delta-v minus gravity, drag and steering, exactly.

        This is not an approximation. It falls out of integrating the equation
        of motion along the velocity vector, so any drift means the integrator
        or the bookkeeping is wrong.
        """
        reconstructed = (
            falcon9.ideal_delta_v
            - falcon9.gravity_loss
            - falcon9.drag_loss
            - falcon9.steering_loss
        )
        assert reconstructed == pytest.approx(falcon9.final_speed, rel=1e-3)

    def test_all_losses_are_positive(self, falcon9):
        assert falcon9.gravity_loss > 0
        assert falcon9.drag_loss > 0
        assert falcon9.steering_loss >= 0

    def test_ideal_delta_v_matches_the_analytic_budget(self, lib, falcon9):
        analytic = analyse(lib, "falcon9_droneship").total_delta_v
        assert falcon9.ideal_delta_v == pytest.approx(analytic, abs=150)


class TestPhysicalPlausibility:
    """Numbers a launch engineer would recognise."""

    def test_gravity_loss_is_in_the_normal_band(self, falcon9):
        """Published launch vehicle gravity losses run roughly 1000 to 1800 m/s."""
        assert 1000 < falcon9.gravity_loss < 1800

    def test_drag_loss_is_small_but_real(self, falcon9):
        """Drag is the smallest of the three losses and easy to over-imagine.

        A single drag coefficient for a whole stack understates it somewhat, so
        the band is wide on purpose. The lesson is its size relative to gravity
        loss, which is right, not its exact value.
        """
        assert 10 < falcon9.drag_loss < 400

    def test_it_actually_gets_somewhere(self, falcon9):
        assert not falcon9.crashed
        assert falcon9.reached_space
        assert falcon9.final_speed > 6500

    def test_max_dynamic_pressure_is_realistic(self, falcon9):
        assert 20_000 < falcon9.max_dynamic_pressure_pa < 60_000

    def test_max_q_happens_early_and_low(self, falcon9):
        peak = max(falcon9.samples, key=lambda sample: sample.dynamic_pressure_pa)
        assert peak.time_s < 120
        assert peak.altitude_m < 20_000

    def test_starship_loses_more_to_gravity_than_falcon9(self, falcon9, starship):
        """It burns a smaller fraction of its mass per second, so it stays heavy."""
        assert starship.gravity_loss > falcon9.gravity_loss


class TestTrajectoryShape:
    def test_it_starts_vertical(self, falcon9):
        early = falcon9.samples[2]
        assert early.downrange_m < early.altitude_m

    def test_it_ends_mostly_horizontal(self, falcon9):
        assert falcon9.samples[-1].flight_path_angle_deg < 25

    def test_altitude_never_goes_negative(self, falcon9):
        assert all(sample.altitude_m >= -1.0 for sample in falcon9.samples)

    def test_mass_only_decreases(self, falcon9):
        masses = [sample.mass_t for sample in falcon9.samples]
        assert masses == sorted(masses, reverse=True)

    def test_staging_is_recorded(self, falcon9):
        assert len(falcon9.events) >= 1
        assert falcon9.events[0].time_s > 60


class TestSettings:
    def test_hanging_on_to_the_vertical_costs_gravity_loss(self, lib):
        """Below 1 the pitch program stays vertical longer, and pays for it."""
        vehicle = analyse(lib, "falcon9_droneship")
        lazy = simulate(vehicle, AscentSettings(turn_shape=0.6))
        brisk = simulate(vehicle, AscentSettings(turn_shape=1.0))
        assert lazy.gravity_loss > brisk.gravity_loss

    def test_gravity_loss_falls_off_monotonically_with_the_turn(self, lib):
        vehicle = analyse(lib, "falcon9_droneship")
        losses = [
            simulate(vehicle, AscentSettings(turn_shape=shape)).gravity_loss
            for shape in (0.6, 0.8, 1.0, 1.2)
        ]
        assert losses == sorted(losses, reverse=True)

    def test_a_rocket_flown_into_the_ground_says_so(self, lib):
        """A beginner will do this. It must report a crash, not silent nonsense."""
        vehicle = analyse(lib, "falcon9_droneship")
        result = simulate(vehicle, AscentSettings(turn_start_speed=1.0, turn_shape=6.0))
        assert result.crashed
        assert not result.reached_space

    def test_more_drag_costs_more_drag_loss(self, lib):
        vehicle = analyse(lib, "falcon9_droneship")
        slippery = simulate(vehicle, AscentSettings(drag_coefficient=0.2))
        blunt = simulate(vehicle, AscentSettings(drag_coefficient=0.6))
        assert blunt.drag_loss > slippery.drag_loss

    def test_samples_are_dense_enough_to_plot(self, falcon9):
        assert len(falcon9.samples) > 100


class TestItRefusesWhatCannotLeaveThePad:
    """The refusal used to be exercised by the Space Shuttle, and is not any more.

    Its boosters named a placeholder engine, so the model computed a liftoff
    thrust-to-weight of 0.19 and refused a vehicle that flew 135 times. Giving
    the stage its real solid motor fixed the data and left this guard with no
    caller, which is exactly when a guard quietly stops working.
    """

    def test_a_rocket_too_heavy_for_its_engines_is_refused(self, lib):
        overloaded = analyse(lib, "falcon9_droneship", payload_t=5000.0)
        with pytest.raises(ValueError, match="cannot leave the pad"):
            simulate(overloaded)

    def test_the_message_names_the_thrust_to_weight(self, lib):
        with pytest.raises(ValueError, match=r"0\.\d\d"):
            simulate(analyse(lib, "falcon9_droneship", payload_t=5000.0))

    def test_the_real_thing_still_flies(self, falcon9):
        assert not falcon9.crashed
