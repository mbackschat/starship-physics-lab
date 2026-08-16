# Knowledge base index

Every page, with the library entries it stands behind. The design is in [knowledge-base.md](../knowledge-base.md); the operating record is in [log.md](log.md).

A page here is something the project **looked up**. Something it **worked out** goes in [studies/](../../studies/) instead.

## Vehicles

| Page | What it covers | Feeds |
|---|---|---|
| [vehicles/starship-v3.md](vehicles/starship-v3.md) | Starship Block 3, and the contested dry mass everything turns on | `vehicles.yaml#starship_v3`, `stages.yaml#starship_v3` |
| [vehicles/super-heavy-v3.md](vehicles/super-heavy-v3.md) | The booster, its recovery budget, and why the staging split sits where it does | `stages.yaml#super_heavy_v3` |
| [vehicles/falcon-9.md](vehicles/falcon-9.md) | The calibration reference. Published numbers the model has to reproduce | `stages.yaml#falcon9_stage1`, `stages.yaml#falcon9_stage2`, `vehicles.yaml#falcon9_droneship` |

## Engines

| Page | What it covers | Feeds |
|---|---|---|
| [engines/raptor-3.md](engines/raptor-3.md) | Raptor 3, sea level and vacuum, and the 327 vs 330 s disagreement | `engines.yaml#raptor_3`, `engines.yaml#raptor_3_vacuum` |

## Flights

| Page | What it covers | Feeds |
|---|---|---|
| [flights/flight-12.md](flights/flight-12.md) | First Block 3 flight. First working satellites, and a source conflict about them | `flights.yaml#12` |
| [flights/flight-13.md](flights/flight-13.md) | First operational deployment. The relight that weighs the ship | `flights.yaml#13` |

## Concepts

| Page | What it covers | Feeds |
|---|---|---|
| [concepts/starlink-v3.md](concepts/starlink-v3.md) | The 1.705 t unit mass that turns a satellite count into a payload figure | `flights.yaml#12`, `flights.yaml#13` |

## Not yet covered

Gaps worth filling, in rough order of value to the app:

- **Flight 14**, once it flies. This is the one that matters, and the [prediction is already pre-registered](../../studies/flight-14-prediction/finding.md).
- **Ariane 6**, whose upper stage is the instructive counter-example: a worse mass fraction that still delivers more payload. It is also the vehicle whose parallel boosters the model cannot represent honestly.
- **Merlin 1D**, to pair with the Falcon 9 page the way Raptor pairs with Starship.
- **Saturn V**, the only flown vehicle that beats everything modern on payload fraction, and a useful antidote to assuming newer means better.
