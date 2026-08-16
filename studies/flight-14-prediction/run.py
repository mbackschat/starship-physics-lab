"""What does the model predict Flight 14 will deliver to orbit?

Written and committed BEFORE the flight. Once telemetry exists it is impossible
to prove a prediction was not adjusted to fit it, and this project's whole claim
is that its numbers were arrived at independently.

Run:  uv run python studies/flight-14-prediction/run.py
Out:  studies/flight-14-prediction/out/flight-14-prediction.{png,html,md,csv}
"""

from labbook import Col, Quantity, beside, save_data, save_figure, save_table, table
from labbook.casestudy import ESTIMATES, payload_curve
from labbook.charts import payload_against_dry_mass
from labbook.palette import Mode
from labbook.units import METRIC
from rocketry.library import load
from rocketry.vehicle import LEO_MISSION_DELTA_V

# Derived from Flight 13, which deployed 20 operational satellites massing
# 34.1 t. Flight 12's 37.5 t for 22 units reproduces from the same figure, so it
# is the best unit mass available without a published spec.
SATELLITE_T = 34.1 / 20

lib = load()
estimates = sorted(ESTIMATES, key=lambda estimate: estimate.dry_mass_t)
points = payload_curve(lib, "starship_v3", [estimate.dry_mass_t for estimate in estimates])

rows = [
    {
        "label": estimate.label,
        "dry": point.dry_mass_t,
        "payload": point.payload_t,
        "satellites": point.payload_t / SATELLITE_T,
        "in_orbit": point.mass_in_orbit_t,
    }
    for point, estimate in zip(points, estimates, strict=True)
]

report = table(
    rows,
    [
        Col("label", "Dry mass estimate"),
        Col("dry", "Assumed ship dry mass", Quantity.MASS, digits=0),
        Col("payload", "Predicted payload", Quantity.MASS, digits=1),
        Col("satellites", "Starlink V3 units", digits=0),
        Col("in_orbit", "Total reaching orbit", Quantity.MASS, digits=0),
    ],
    formatter=METRIC,
    title="Flight 14 prediction, before the flight",
)
print(report)

arriving = [point.mass_in_orbit_t for point in points]
print(f"\nMission budget assumed: {LEO_MISSION_DELTA_V:,.0f} m/s")
print(f"Starlink V3 unit mass:  {SATELLITE_T:.3f} t, from Flight 13")
print(
    f"Total reaching orbit:   {min(arriving):,.0f} to {max(arriving):,.0f} t "
    f"across every assumption, a spread of {max(arriving) - min(arriving):,.1f} t"
)
print(
    f"Payload:                {min(r['payload'] for r in rows):,.1f} to "
    f"{max(r['payload'] for r in rows):,.1f} t"
)
print("\nThe first line barely moves. The second moves by a factor of five.")
print("That gap is the entire prediction, and Flight 14 measures which end is right.")

figure = payload_against_dry_mass(
    [(point.dry_mass_t, point.payload_t) for point in points],
    arriving=[(point.dry_mass_t, point.mass_in_orbit_t) for point in points],
    markers=[(estimate.label, point.dry_mass_t, point.payload_t)
             for point, estimate in zip(points, estimates, strict=True)],
    formatter=METRIC,
    mode=Mode.LIGHT,
    title="What Flight 14 will settle",
    subtitle="Predicted before launch. The dotted line is fixed; only its composition is in doubt.",
)

out = beside(__file__)
save_table(report, "flight-14-prediction", out_dir=out)
save_figure(figure, "flight-14-prediction", out_dir=out)
save_data(rows, "flight-14-prediction", out_dir=out)
