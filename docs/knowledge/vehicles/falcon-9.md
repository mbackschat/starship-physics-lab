---
type: Vehicle
title: Falcon 9 Block 5
description: SpaceX's workhorse, and the reference the whole model is calibrated against.
tags: [falcon-9, spacex, calibration, reference]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, sections 3.4 and 5.2
    last_modified: 2026-08-16
  - id: wiki-f9
    resource: https://en.wikipedia.org/wiki/Falcon_9
    title: Wikipedia, Falcon 9
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-02-28

provenance: published
feeds:
  - target: data/stages.yaml#falcon9_stage1
    asserts:
      dry_mass_t: 25.6
      propellant_t: 395.7
      engine_count: 9
      isp_ascent_s: 301.0
  - target: data/stages.yaml#falcon9_stage2
    asserts:
      dry_mass_t: 4.0
      propellant_t: 107.0
      isp_ascent_s: 348.0
      residual_propellant_t: 0.5
  - target: data/vehicles.yaml#falcon9_droneship
    asserts:
      payload_leo_t: 17.5
      staging_speed_kmh: 8000.0
      fairing_t: 1.9
---

# Falcon 9 Block 5

**This is the page that makes the rest of the project believable.**

Falcon 9's masses, engines and payload are all published. Run them through the same model that produces the disputed Starship numbers and the answer comes out right. That is the only reason the Starship result can be quoted at all: the method has been checked where checking is possible.

## What the library holds

| | First stage | Second stage |
|---|---:|---:|
| Dry mass | 25.6 t | 4.0 t |
| Propellant | 395.7 t | 107.0 t |
| Engines | 9 × Merlin 1D | 1 × Merlin 1D vacuum |
| Ascent Isp | 301 s | 348 s |
| Residual | 0 t | 0.5 t, for a controlled deorbit |

Fairing 1.9 t. Staging at 8,000 km/h. Published LEO payload 17.5 t with droneship recovery.

## The calibration

| Configuration | Liftoff mass | Ideal Δv | Payload | Payload fraction |
|---|---:|---:|---:|---:|
| Droneship recovery | 552 t | 9,333 m/s | 17.5 t | 3.17 % |
| Expendable | 557 t | 8,901 m/s | 22.8 t | 4.09 % |

9,333 m/s sits inside the normal 9,300 to 9,600 m/s band for reaching low Earth orbit, at the vehicle's *published* payload. Nothing was tuned to make that happen.

**Recovery costs about a quarter of the payload.** 17.5 t against 22.8 t, for the same rocket and the same stages. The only difference is propellant held back to land, and it is held back all the way uphill.

## Two figures worth knowing about

**First stage propellant is quoted as 385 t by the source article**, against Wikipedia's 395.7 t. The library takes the higher published figure. About 2.7 %, which is inside the project's precision target but worth knowing when a number lands slightly off a source.

**Second stage propellant spans 92.7 t to 111 t across sources.** 107 t is the commonly used Block 5 figure and what the article uses. This is a genuinely wide spread for a published vehicle, and a useful reminder that "published" does not mean "agreed".

## Why it is the instructive comparison

Falcon 9 stages at 8,000 km/h. Starship stages at 6,000 km/h. On the same physics, that difference is worth roughly a factor of two in payload, and it is the whole argument of the staging chapter.

Its first stage is also **already as slender as it can be**: stretching it further would make bending loads the limiting factor. That matters because "just add propellant" is the intuitive fix for every rocket problem and it is usually unavailable.

## What would change this page

Block 5 is a mature vehicle and its figures have been stable for years. The likeliest change is a payload restatement, or better published propellant numbers settling the 92.7 to 111 t spread.
