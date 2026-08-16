# How does every rocket in the library compare, once it is actually flown?

**Answer: five of the thirteen are modelled exactly as they fly, and those five land within 12 % of their published payloads. The rest are either thought experiments, contested, or vehicles this model is honest about not representing.**

Run: `uv run python studies/fleet-comparison/run.py`

## What it does

For every vehicle that publishes a payload figure:

1. **Analyse** it at that figure, walking the stack bottom-up.
2. **Solve** it for payload against the 9,404 m/s LEO budget, which is the question a reader actually has.
3. **Fly** it, from the pad to the last engine cutoff, and account for where the velocity went.

The rows come from [`labbook.fleet`](../../src/labbook/fleet.py), which is also what chapter 12 of the app renders. That is the point of it living there: a figure in this report and a figure on that page are the same computation, not two that agree today.

## What it shows

| | |
|---|---|
| Vehicles modelled as they fly | 5 of 13 |
| Closest to its published claim | Falcon 9 droneship, −2.0 % |
| Furthest | Falcon 9 expendable, −11.8 % |
| Still descending at cutoff | Saturn V |

Full tables in `out/fleet.md` and `out/fleet-full.md`.

**Three things are worth reading off it.**

**The spread on Starship is the whole project.** Its row says 37.7 t modelled against a 100 t claim, and V4's says 9.2 t against 200 t. Neither is a verdict: both rest on a dry mass SpaceX has not published since 2019, and [chapter 7](../../app/pages/7_The_payload_question.py) hands the reader the slider instead of the answer.

**Losses cluster tightly, and that is the reassuring part.** Every vehicle loses between 18 % and 31 % of what its engines produce, mostly to gravity. A model that produced 5 % for one vehicle and 50 % for another would be describing its own bugs rather than rocketry.

**Saturn V is the weakest row and says so.** It is still descending when its engines stop, and it reaches 6,393 m/s where the real vehicle reached orbit. Its solved payload is 11 % under the published 140 t, so the shortfall in the flown number and the shortfall in the analytic one are the same shortfall seen twice, not two separate problems.

## Assumptions

- **One mission budget for everybody**, 9,404 m/s, calibrated in [docs/physics-reference.md](../../docs/physics-reference.md) section 3.3. Real vehicles fly to different orbits on different trajectories, and a single budget cannot match all of them. This is the largest source of disagreement between the modelled and published payload columns, and it is why the calibration tolerance is 15 %.
- **The flown numbers assume a competently flown ascent**: a stored pitch program through the atmosphere, closed-loop guidance above 60 km aiming at 200 km with no climb rate left, and one drag coefficient for the whole stack. Good enough for the size and ordering of the losses. Not a trajectory design tool.
- **A parallel burn is flown as a sequence**, which always flatters the vehicle. Ariane 64 and the Space Shuttle declare this in `data/vehicles.yaml` and are excluded from the "modelled as they fly" count for exactly that reason.
- **Drag comes out low**, around 25 m/s where published figures run nearer 100. A single drag coefficient applied to one stage's frontal area understates a real stack. Max-Q lands at 20 to 37 kPa, which is right, so the aerodynamic environment is closer than the integrated loss.
- **Payload claims are claims.** `payload_leo_t` is what the operator published, and this study exists to test it rather than to assume it.
- **They are also quoted for a reference orbit, and the two must match before a comparison means anything.** Falcon 9's 22.8 t and 17.5 t are both for 28.5°, so the difference between them really is the cost of recovery. Where a claim's reference orbit is unknown, the row is a comparison between vehicles rather than a verdict on one.

## Reproducing

```sh
uv run python studies/fleet-comparison/run.py
```

Nothing is hard-coded: the vehicle list comes from `data/`, so adding a rocket adds a row.
