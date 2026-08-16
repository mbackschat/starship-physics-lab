---
type: Concept
title: Reentry and the square-cube law
description: Why bringing a big stage back is harder than bringing a small one back, and the one assumption that swings the V4 argument by a factor of nine.
tags: [physics, reentry, square-cube, scaling, heat-shield]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, section 2.8
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-08-31

provenance: derived
---

# Reentry and the square-cube law

## Bigger things come back harder

Mass grows with the **cube** of size. Frontal area grows only with the **square**.

So a larger vehicle arrives with more mass behind every square metre of the surface that has to slow it down. It decelerates lower, in thicker air, and its heat shield works harder. This is why scaling a returning vehicle up is not free, and it is the physical reason [Starship's](../vehicles/starship-v3.md) heat shield is such a persistent difficulty.

It also cuts the other way, and is why small vehicles reenter comparatively gently.

Modelled in `src/rocketry/reentry.py` as a ballistic coefficient, with a helper for the diameter that would keep loading equal as a vehicle grows.

## The scaling exponent, which decides more than anything else here

When a stage is stretched, how much heavier does it get?

```
dry_mass = reference_dry · (propellant / reference_propellant) ^ k
```

- **k = 1** means weight grows in exact proportion to propellant.
- **k = 0** means stretching the tanks adds no weight at all.
- Reality is in between, because tanks scale with size while engines, nose, flaps and avionics largely do not. Somewhere near **0.8** is a fair guess.

**That single exponent swings the V4 answer by a factor of nine**: a stretched Starship carries about 12 t at k = 1 and over 100 t at k = 0. See [studies/v4-scaling](../../../studies/v4-scaling/finding.md).

Nobody can settle it from outside, so the app hands the reader the slider rather than a verdict. It is the same shape of problem as the dry mass itself: one unpublished assumption doing all the work.

## The trap it creates in the sandbox

Shrinking a stage while holding its dry mass fixed makes the rocket **worse**. So the obvious advice, "cut the upper stage in half", teaches the exact opposite of the truth unless the stage is also allowed to get lighter.

The sandbox therefore scales dry mass with propellant by default and offers a checkbox to turn it off, which turns the trap into the lesson. Two tests hold both directions in place, because this is the kind of thing that silently reverts.

## Why V4 makes things worse

Starship V4 grows the ship to 2,300 t of propellant on a 4,050 t booster, moving the [staging](staging.md) ratio from 2.28:1 to **1.76:1**, further in the direction the sweep says is expensive.

Two things partly rescue it: weight probably does not scale linearly, and V4's ship gets six vacuum engines instead of three, worth roughly 23 t of payload from the larger nozzles alone. Together they make V4 look survivable rather than good.

What would actually help is separating the stages later, not making the upper stage bigger.
