"""Where should a two-stage rocket separate, and what does getting it wrong cost?

Answers the source article's central claim without taking its word for anything:
builds the model from the library, sweeps the staging speed, and marks where the
real vehicles and the article's redesigns land.

Run:  uv run python studies/staging-split/run.py
Out:  studies/staging-split/out/staging-split.{png,html,md,csv}
"""

from labbook import US, Col, Quantity, beside, save_data, save_figure, save_table, table
from labbook.charts import staging_sweep
from labbook.units import METRIC, from_kmh, to_kmh
from rocketry.library import load
from rocketry.staging import (
    REFERENCE_STAGING,
    SWEEP_CEILING,
    StagingModel,
    optimal_staging_speed,
)
from rocketry.staging import staging_sweep as sweep_model
from rocketry.vehicle import analyse

FORMATTER = METRIC  # swap for US to produce the same report in pounds and mph

lib = load()
model = StagingModel()
curve = [
    (to_kmh(speed), payload)
    for speed, payload in sweep_model(model, REFERENCE_STAGING, SWEEP_CEILING, from_kmh(250.0))
]
best_speed = optimal_staging_speed(model)
best_payload = model.payload_at(best_speed)
as_flown = model.payload_at(REFERENCE_STAGING)

# --- Where the real vehicles and the article's concepts sit ------------------

COMPARISONS = [
    "starship_v3",
    "starship_v4",
    "falcon9_droneship",
    "falcon9_expendable",
    "ariane_64",
    "space_shuttle",
    "raptor33_raptor4",
    "raptor33_raptor3",
    "raptor33_expendable",
    "raptor33_pessimistic",
]

rows = []
for key in COMPARISONS:
    vehicle = lib.vehicle(key)
    result = analyse(lib, key)
    rows.append(
        {
            "name": vehicle.name,
            "kind": vehicle.category.value,
            "article": vehicle.in_article,
            "liftoff": result.liftoff_mass_t,
            "staging": vehicle.staging_speed_kmh or None,
            "s1_share": result.first_stage_share,
            "total_dv": result.total_delta_v,
            "payload": result.payload_t,
            "payload_frac": result.payload_fraction,
        }
    )

report = table(
    rows,
    [
        Col("name", "Vehicle"),
        Col("kind", "Kind"),
        Col("liftoff", "Liftoff", Quantity.MASS),
        Col("staging", "Staging", Quantity.SPEED),
        Col("s1_share", "Stage 1 share of Δv", Quantity.PERCENT),
        Col("total_dv", "Ideal Δv", Quantity.VELOCITY),
        Col("payload", "Payload claimed", Quantity.MASS, digits=1),
        Col("payload_frac", "Payload fraction", Quantity.PERCENT, digits=2),
    ],
    formatter=FORMATTER,
    title="Staging split against payload, at each operator's claimed payload",
)

print(report)
print()
print(f"Optimum staging speed in this model : {FORMATTER.speed(to_kmh(best_speed))}")
print(f"Payload there                       : {FORMATTER.mass(best_payload)}")
print(f"Payload as flown at 6 000 km/h      : {FORMATTER.mass(as_flown)}")
print(f"Cost of the current split           : {best_payload / as_flown:.1f}x less payload")
print()
print("Same report in US customary units, to show the toggle works:")
print(FORMATTER.mass(5850), "->", US.mass(5850), "|", FORMATTER.speed(10000), "->", US.speed(10000))

# --- Chart -------------------------------------------------------------------

# Labelled in km/h, the way the article and the chart speak; the model takes m/s.
markers = [
    (label, kmh, model.payload_at(from_kmh(kmh)))
    for label, kmh in (
        ("Starship as flown", 6000.0),
        ("Falcon 9 split", 8000.0),
        ("Article: Raptor 33 + 4", 10000.0),
        ("Article: Raptor 33 + 3", 12000.0),
    )
]

figure = staging_sweep(
    curve,
    markers=markers,
    formatter=FORMATTER,
    title="The staging split is worth a factor of two in payload",
    subtitle=(
        "Same 5 850 t rocket every time. Only the speed at which the stages separate changes. "
        "Diamonds mark real and proposed vehicles."
    ),
)

OUT = beside(__file__)
paths = save_figure(figure, "staging-split", out_dir=OUT)
save_table(report, "staging-split", out_dir=OUT)
save_data(
    [{k: ("" if v is None else v) for k, v in row.items()} for row in rows],
    "staging-split",
    out_dir=OUT,
)
print()
print("wrote:", ", ".join(str(p.name) for p in paths), "staging-split.md, staging-split.csv")
