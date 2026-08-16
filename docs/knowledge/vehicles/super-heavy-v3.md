---
type: Vehicle
title: Super Heavy V3
description: Starship's first stage, and the reason the staging split is where it is.
tags: [super-heavy, spacex, block-3, booster]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, section 5.2
    last_modified: 2026-08-16
  - id: wiki-f12
    resource: ../../../raw/2026-08-16-wikipedia-starship-flight-12.md
    title: Starship flight test 12
    last_modified: 2026-08-16
  - id: wiki-f13
    resource: ../../../raw/2026-08-16-wikipedia-starship-flight-13.md
    title: Starship flight test 13
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2026-10-31

provenance: estimated
feeds:
  - target: data/stages.yaml#super_heavy_v3
    asserts:
      dry_mass_t: 300.0
      propellant_t: 3650.0
      engine_count: 33
      diameter_m: 9.0
      isp_ascent_s: 340.0
---

# Super Heavy V3

The first stage. 33 Raptor 3 engines, 3,650 t of propellant, 9 m across, and it returns to the launch site to be caught by the tower.

## What the library holds

| Field | Value | Weight it bears |
|---|---:|---|
| Propellant | 3,650 t | published |
| Dry mass | 300 t | **estimated** |
| Engines | 33 × Raptor 3 | published |
| Diameter | 9.0 m | published |
| Ascent Isp | 340 s | estimated |

## The dry mass is estimated, not contested

Worth distinguishing from [the ship](starship-v3.md), where the equivalent number is genuinely fought over.

The source article estimates 300 t. Wikipedia lists 275 t for Block 1 and 2, and Block 3 is taller. Nobody is arguing about it, and no argument turns on it, because the booster is discarded before orbit and its mass therefore does not compete with payload the way the ship's does. That asymmetry is why one number is `estimated` and the other is `contested`, and the distinction is not decoration.

## Returning to the launch site is the expensive choice

The booster carries propellant for two recovery burns:

| Burn | Δv | Isp |
|---|---:|---:|
| Boostback | 1,800 m/s | 330 s |
| Landing | 600 m/s | 330 s |

Coming back to the pad means cancelling downrange velocity and flying home, which is why the boostback burn dominates. Landing on a ship downrange, as Falcon 9 usually does, skips most of that. The comparison is worth about a quarter of Falcon 9's payload, and the reuse chapter is built on it.

## Why the split is where it is, and why that hurts

Super Heavy carries 3,650 t against the ship's 1,600 t, a ratio of **2.28 : 1**. Falcon 9's is **3.70 : 1**.

A first stage that hands over earlier leaves the upper stage doing more of the work, and upper-stage mass is the mass that competes directly with cargo. This is the mechanism behind the whole staging argument, and it is why Starship separates at 6,000 km/h where the model puts the optimum near 11,500 km/h.

V4 makes it worse rather than better, moving the ratio to 1.76 : 1. See [studies/v4-scaling](../../../studies/v4-scaling/finding.md).

## Flight record

Block 3 boosters have flown twice and been lost both times, in both cases during the landing burn rather than during ascent.

- **[Flight 12](../flights/flight-12.md)**, B19. Flipped abnormally fast after separation, hit the Gulf at 1,450 km/h.
- **[Flight 13](../flights/flight-13.md)**, B20. Only 10 of 13 engines relit for the landing burn; destroyed on impact.

Ascent has not been the problem. Recovery has.

## What would change this page

A published dry mass, which would move this from `estimated` to `published`. Or Flight 14's booster returning to the launch site successfully, which would be the first Block 3 recovery and the first demonstration that the boostback budget above is right.
