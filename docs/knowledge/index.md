# Knowledge base index

Every page, with the library entries it stands behind. The design is in [knowledge-base.md](../knowledge-base.md); the operating record is in [log.md](log.md).

A page here is something the project **looked up**. Something it **worked out** goes in [studies/](../../studies/) instead.

## Vehicles

| Page | What it covers | Feeds |
|---|---|---|
| [vehicles/starship-v3.md](vehicles/starship-v3.md) | Starship Block 3, and the contested dry mass everything turns on | `vehicles.yaml#starship_v3`, `stages.yaml#starship_v3` |
| [vehicles/super-heavy-v3.md](vehicles/super-heavy-v3.md) | The booster, its recovery budget, and why the staging split sits where it does | `stages.yaml#super_heavy_v3` |
| [vehicles/falcon-9.md](vehicles/falcon-9.md) | The calibration reference. Published numbers the model has to reproduce | `stages.yaml#falcon9_stage1`, `stages.yaml#falcon9_stage2`, `vehicles.yaml#falcon9_droneship` |
| [vehicles/ariane-6.md](vehicles/ariane-6.md) | The counter-example, and the vehicle the model admits it cannot represent honestly | `stages.yaml#ariane6_ulpm`, `stages.yaml#ariane6_core`, `stages.yaml#ariane6_boosters`, `vehicles.yaml#ariane_64` |
| [vehicles/saturn-v.md](vehicles/saturn-v.md) | Best payload fraction ever flown, and what reuse costs against it | `vehicles.yaml#saturn_v` |

## Engines

| Page | What it covers | Feeds |
|---|---|---|
| [engines/raptor-3.md](engines/raptor-3.md) | Raptor 3, sea level and vacuum, and the 327 vs 330 s disagreement | `engines.yaml#raptor_3`, `engines.yaml#raptor_3_vacuum` |
| [engines/merlin-1d.md](engines/merlin-1d.md) | Falcon 9's engine, and why a 16 % efficiency deficit did not decide anything | `engines.yaml#merlin_1d`, `engines.yaml#merlin_1d_vacuum` |

## Flights

| Page | What it covers | Feeds |
|---|---|---|
| [flights/flight-12.md](flights/flight-12.md) | First Block 3 flight. First working satellites, and a source conflict about them | `flights.yaml#12` |
| [flights/flight-13.md](flights/flight-13.md) | First operational deployment. The relight that weighs the ship | `flights.yaml#13` |

## Concepts

The physics, in the order it builds. These back the chapters rather than the library, so most carry no `feeds`.

| Page | What it covers | Feeds |
|---|---|---|
| [concepts/the-rocket-equation.md](concepts/the-rocket-equation.md) | Tsiolkovsky, the logarithm, and the two questions that sound identical | |
| [concepts/mass-fractions.md](concepts/mass-fractions.md) | Dry-mass and payload fraction, and the trap in comparing them | |
| [concepts/ascent-losses.md](concepts/ascent-losses.md) | Where a fifth of the engines' work goes, and why gravity beats drag | |
| [concepts/staging.md](concepts/staging.md) | Why rockets throw themselves away, and what the split is worth | |
| [concepts/reuse.md](concepts/reuse.md) | What coming home costs, paid uphill | |
| [concepts/propellant-choices.md](concepts/propellant-choices.md) | Kerolox, methalox, hydrolox, and why the most efficient loses | |
| [concepts/reentry-and-scaling.md](concepts/reentry-and-scaling.md) | The square-cube law, and the exponent that swings V4 by nine | |
| [concepts/starlink-v3.md](concepts/starlink-v3.md) | The 1.705 t unit mass that turns a satellite count into a payload figure | `flights.yaml#12`, `flights.yaml#13` |

## Not yet covered

Gaps worth filling, in rough order of value to the app:

- **Flight 14**, once it flies. The [prediction is already pre-registered](../../studies/flight-14-prediction/finding.md) and the page is ready to be written the day it happens.
- **The Space Shuttle**, whose boosters burn in parallel like Ariane 64's. It reproduced its published payload to within 6 % while being flown as something it was not, which is why `modelling_limits` exists at all.
- **New Glenn and Long March 10B**, both discussed in the source article, neither yet given a page.
- **Starship V4**, currently reasoned about only in [studies/v4-scaling](../../studies/v4-scaling/finding.md).
