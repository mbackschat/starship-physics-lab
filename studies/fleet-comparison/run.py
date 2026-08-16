"""How does every rocket in the library compare, once it is actually flown?

Analyses each vehicle, solves it for payload against the LEO budget, then flies
it from the pad to engine cutoff, and puts the lot in one table. Shares its rows
with chapter 12 of the app through `labbook.fleet`, so a number here and a number
on the page cannot disagree.

Run:  uv run python studies/fleet-comparison/run.py
Out:  studies/fleet-comparison/out/fleet.{md,csv}, fleet-full.{md,csv}
"""

from dataclasses import asdict

from labbook import beside, save_data, save_table, table
from labbook.fleet import CORE_COLUMNS, EXTRA_COLUMNS, fleet
from labbook.units import METRIC
from rocketry.library import load

FORMATTER = METRIC  # swap for US to produce the same report in pounds and mph

rows = fleet(load())

summary = table(
    rows,
    list(CORE_COLUMNS),
    formatter=FORMATTER,
    title="Every vehicle in the library, solved and flown",
)

full = table(
    rows,
    [*CORE_COLUMNS, *EXTRA_COLUMNS],
    formatter=FORMATTER,
    title="The same vehicles, with the whole ascent breakdown",
)

print(summary)
print()

flown = [row for row in rows if row.category in {"flown", "historic"}]
honest = [row for row in flown if not row.limits]
worst = max(honest, key=lambda row: abs(row.payload_error))
best = min(honest, key=lambda row: abs(row.payload_error))

print(f"Vehicles modelled as they fly : {len(honest)} of {len(rows)}")
print(f"Closest to its published claim: {best.name} ({best.payload_error:+.1%})")
print(f"Furthest                      : {worst.name} ({worst.payload_error:+.1%})")
print(f"Still descending at cutoff    : ", end="")
falling = [row.name for row in rows if row.climb_rate_ms < -100]
print(", ".join(falling) if falling else "none")

OUT = beside(__file__)
save_table(summary, "fleet", out_dir=OUT)
save_table(full, "fleet-full", out_dir=OUT)
save_data([asdict(row) for row in rows], "fleet", out_dir=OUT)

print()
print("wrote: fleet.md, fleet-full.md, fleet.csv")
