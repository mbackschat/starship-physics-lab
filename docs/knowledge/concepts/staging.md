---
type: Concept
title: Staging
description: Why rockets throw themselves away, where the split should go, and why getting it wrong costs a factor of two.
tags: [physics, staging, fundamentals, starship-argument]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, sections 2.6 and 3.7
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-08-31

provenance: derived
---

# Staging

The crude trick that makes orbit reachable at all, and the argument the whole project turns on.

## Why throw the rocket away

[The rocket equation](the-rocket-equation.md) says reaching orbit takes about fifteen tonnes of propellant per tonne of everything else. Building a single vehicle that light is not possible with metal.

Staging resets the sum. Burn the first stage, drop it, and the second stage no longer carries those empty tanks. Its mass ratio is computed fresh from a much smaller starting mass. Two modest mass ratios multiply into one enormous one.

It is genuinely crude, and it is the only reason spaceflight works.

## Where to split, which is the interesting part

Not obvious, and it is worth a factor of two.

Stage **too early** and the upper stage must supply most of the velocity itself. Its own weight then competes directly with cargo, because every tonne of upper-stage structure is a tonne that reaches orbit and is not payload.

Stage **too late** and the first stage becomes enormous, carrying its own empty mass to a high speed before letting go.

The optimum sits between. For identical stages, theory says roughly half the velocity each; slightly less than half for the first stage when it has the lower-efficiency engines, which is usual.

**Real vehicles run well below that**, and Starship runs furthest below.

## The comparison that carries the argument

| Vehicle | First : second stage propellant | Staging speed |
|---|---:|---:|
| [Falcon 9](../vehicles/falcon-9.md) | 3.70 : 1 | 8,000 km/h |
| [Starship V3](../vehicles/starship-v3.md) | 2.28 : 1 | 6,000 km/h |
| Starship V4, announced | 1.76 : 1 | lower still |

Sweeping the staging speed on the same 5,850 t vehicle puts the payload optimum near **11,500 km/h** against the 6,000 km/h Starship actually flies. That is worth roughly **2.2× the payload**, and it was reproduced independently in [studies/staging-split](../../../studies/staging-split/finding.md) rather than taken from the source article.

## The counter-example that proves it is the split, not the welding

[Ariane 6](../vehicles/ariane-6.md)'s upper stage has a dry-mass fraction of **16.2 %**, worse than Starship's **12.1 %**. It is more structure per tonne of propellant by the standard measure.

It carries 21.6 t at a payload fraction of 2.58 %, against Starship's claimed 1.70 %.

Worse built, better result, because it stages much faster. If Starship's payload disappoints, better manufacturing is not the fix.

## Why more stages help, and why nobody uses many

Each stage discarded resets the mass ratio again, so three beats two. [Saturn V](../vehicles/saturn-v.md) used three and still holds the best payload fraction here at 4.75 %.

The returns diminish while the complexity does not: every separation is a chance to fail, and every stage needs its own engines, tanks and control. Two is the usual answer for a reusable vehicle, because each stage you keep is a stage you must also bring home.

## Where this is modelled

`src/rocketry/staging.py`, with the sweep and the optimum. A known limit: stages that burn **in parallel** cannot be represented honestly by a bottom-up walk. [Ariane 64](../vehicles/ariane-6.md) and the Space Shuttle both declare `modelling_limits: [parallel_burn]`, and the calibration test therefore does not treat what they compute as evidence. The Shuttle is the reason that distinction exists: it reproduced its published payload to within 6 %, closely enough to pass the test that decides whether anything else can be believed, while being flown as something it was not. Passing calibration and being honestly modelled are not the same thing.
