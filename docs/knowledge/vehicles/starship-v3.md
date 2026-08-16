---
type: Vehicle
title: Starship / Super Heavy V3
description: SpaceX's two-stage reusable launch vehicle, Block 3, flying since May 2026.
tags: [starship, spacex, block-3, contested]

sources:
  - id: wiki-f12
    resource: ../../../raw/2026-08-16-wikipedia-starship-flight-12.md
    title: Starship flight test 12
    last_modified: 2026-08-16
  - id: wiki-f13
    resource: ../../../raw/2026-08-16-wikipedia-starship-flight-13.md
    title: Starship flight test 13
    last_modified: 2026-08-16
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, sections 3.2 and 5.2
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2026-09-30

provenance: contested
feeds:
  - data/vehicles.yaml#starship_v3
  - data/stages.yaml#starship_v3
---

# Starship / Super Heavy V3

The vehicle the whole case study is about. Two stages, both intended to be reusable, both caught by the launch tower rather than landed on legs.

## What the library holds

| Field | Value | Weight it bears |
|---|---:|---|
| Ship propellant | 1,600 t | published |
| Ship dry mass | 220 t | **contested** |
| Ship engines | 6 × Raptor 3 | published |
| Ship ascent Isp | 365 s | estimated |
| Diameter | 9.0 m | published |
| Staging speed | 6,000 km/h | published |
| Claimed LEO payload | 100 t | **contested** |

## The one number everything turns on

**SpaceX has not published the ship's dry mass since 2019.** Every disagreement about Starship's payload reduces to this, and the credible estimates span a factor of nearly three:

| Estimate | Source | Implied payload |
|---:|---|---:|
| 85 t | Wikipedia, listed for Block 2, no primary source | 199 t |
| 100 t | Wikipedia, listed for Block 1 | 181 t |
| 120 t | Musk, September 2019, target for Mk4 or Mk5 | 157 t |
| 160 t | Derived: what the 100 t payload claim requires | 109 t |
| 200 t | Musk, September 2019, "Mk1 ship is around 200 tons dry", no heat shield | 62 t |
| 220 t | Reconstructed from Flight 13's 14 s relight | 38 t |

The implied payloads come from the model, holding the mission budget fixed at 9,404 m/s. See [physics-reference.md](../../physics-reference.md) correction C15.

**The mass reaching orbit does not move.** Across that entire range it stays between 296 and 298 t, because the rocket equation fixes it. Only the split between ship and cargo is in doubt. That is the single most important thing about this vehicle and the reason the app hands the reader a slider rather than an answer.

## Recovery

The header tanks hold propellant for the deorbit and landing burns. The library records these as recovery burns rather than as a flat residual, so the reserve scales with the ship's mass the way real propellant does and is counted exactly once. On a 220 t ship the two burns come to about 38 t, which matches the roughly 40 t the source article assumes.

## Flight record

Block 3 has flown twice, both times deliberately short of orbital velocity.

- **[Flight 12](../flights/flight-12.md)**, 22 May 2026. First Block 3 flight. Booster lost.
- **[Flight 13](../flights/flight-13.md)**, 24 July 2026. First operational satellite deployment. Booster lost, ship recovered intact.
- **Flight 14**, not yet flown. First orbital attempt.

Neither flown mission reached orbit, which is why no direct measurement of orbital payload exists yet.

## What would change this page

Flight 14 delivering a payload to a real orbit. That measurement pins the dry mass through the table above, and would collapse most of the range. The prediction is pre-registered in [studies/flight-14-prediction/](../../../studies/flight-14-prediction/finding.md).
