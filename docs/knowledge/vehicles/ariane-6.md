---
type: Vehicle
title: Ariane 64
description: >-
  The counter-example: a worse-built upper stage that carries more, and the
  vehicle the model admits it cannot represent honestly.
tags: [ariane, esa, arianegroup, counter-example, model-limit]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, section 5.2
    last_modified: 2026-08-16
  - id: esa
    resource: https://www.esa.int/Enabling_Support/Space_Transportation/Ariane_6
    title: ESA, Ariane 6
    last_modified: 2026-08-16
  - id: avio
    resource: https://www.avio.com/p120c
    title: Avio, P120C solid booster
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-02-28

provenance: published
feeds:
  - target: data/stages.yaml#ariane6_ulpm
    asserts:
      dry_mass_t: 6.0
      propellant_t: 31.0
      isp_ascent_s: 457.0
  - target: data/stages.yaml#ariane6_core
    asserts:
      dry_mass_t: 14.0
      propellant_t: 110.0
      isp_ascent_s: 420.0
  - target: data/stages.yaml#ariane6_boosters
    asserts:
      dry_mass_t: 44.0
      propellant_t: 608.0
      engine_count: 4
  - target: data/vehicles.yaml#ariane_64
    asserts:
      payload_leo_t: 21.6
      fairing_t: 2.5
---

# Ariane 64

Here for one argument, and for one confession.

## The argument: build quality is not the problem

| Upper stage | Dry mass fraction | Payload to LEO |
|---|---:|---:|
| Ariane 6 ULPM | **16.2 %** | 21.6 t |
| Starship V3 ship | **12.1 %** | disputed, 38 to 199 t |

Ariane's upper stage is *worse built* by the standard measure. It carries proportionally more structure per tonne of propellant, and by the reasoning most people reach for first, it should therefore perform worse.

It lifts 21.6 t on a vehicle massing 837 t at liftoff, a payload fraction of 2.58 %, against Starship's claimed 1.70 %.

**The difference is where the stages separate.** Ariane's upper stage takes over from a booster that has already done most of the work, so it starts fast and needs less of its own. Starship's ship separates at 6,000 km/h and has to supply far more of the total itself, where its own weight competes directly with cargo.

This is the single most useful comparison in the project, because it kills the intuitive explanation. If Starship's payload is disappointing, better welding is not the fix. The staging split is.

## The confession: the model cannot represent this vehicle honestly

Ariane 6's four solid boosters and its core stage **burn at the same time**. The model walks a stack bottom-up, one stage after another, and there is no honest way to express a parallel burn in that form.

A serial model of a parallel burn always **flatters** the vehicle, because it lets the core burn its propellant at the low mass it only actually reaches once the boosters have gone. Left uncorrected, this vehicle computes 10,700 m/s and a 35 t payload against a real 21.6 t, which is 60 % high.

The library applies the standard correction: the core's propellant is split between the two phases in proportion to how long each lasts, and the boosters carry a blended specific impulse. That recovers most of it. The computed payload still runs about 50 % high.

**So this entry is trustworthy for the upper-stage comparison and not for payload.** It sits on the excused list in `tests/test_library_calibration.py` with that reason attached, and a test fails if the excuse is ever quietly dropped or ever stops being needed.

Recording a known limit where anyone can see it is worth more than a number that looks right.

## The numbers as modelled

| Stage | Dry fraction | Δv contributed |
|---|---:|---:|
| Four P120C boosters | 6.7 % | 3,558 m/s |
| Core (LLPM) | 11.3 % | 3,715 m/s |
| Upper (ULPM) | 16.2 % | 3,173 m/s |

Launching from Kourou at 5.2° latitude gives it more of Earth's rotation than any other site here, which is worth real payload and is a genuine advantage unrelated to the vehicle.

## What would change this page

A proper parallel-staging model, which would take Ariane 64 off the excused list and let the Space Shuttle be flown at all, and is the most valuable outstanding improvement to the physics core. Until then, the 50 % overshoot is the honest state of things.
