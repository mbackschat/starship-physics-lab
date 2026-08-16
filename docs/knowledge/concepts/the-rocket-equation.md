---
type: Concept
title: The rocket equation
description: Tsiolkovsky, 1903, and why one logarithm decides almost everything about launch vehicles.
tags: [physics, fundamentals, tsiolkovsky, delta-v]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, sections 2.2 and 2.3
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-08-31

provenance: published
---

# The rocket equation

```
Δv = v_e · ln(m₀ / m_f)
```

Velocity change equals effective exhaust velocity times the natural logarithm of the mass ratio. Written down by Konstantin Tsiolkovsky in 1903, and everything else in this project is built on it.

Implemented in `src/rocketry/tsiolkovsky.py`, along with its four inverse forms, because the interesting questions usually come at it backwards: not *how fast will this go*, but *how much propellant do I need*, or *how heavy may this stage be*.

## Why a logarithm, and why that is the whole problem

Because the rocket has to accelerate its own propellant. The propellant burnt at the end of a flight had to be carried, and accelerated, by the propellant burnt at the start. That feedback turns a straightforward push into a logarithm.

The practical consequence is that **speed climbs in equal steps while propellant doubles**. At 350 s of specific impulse, every doubling of the mass ratio buys exactly 2,379 m/s:

| Doublings | Mass ratio | Speed | Propellant per tonne of dry rocket |
|---:|---:|---:|---:|
| 1 | 2:1 | 2,379 m/s | 1 t |
| 2 | 4:1 | 4,758 m/s | 3 t |
| 3 | 8:1 | 7,137 m/s | 7 t |
| 4 | 16:1 | 9,516 m/s | **15 t** |
| 5 | 32:1 | 11,896 m/s | 31 t |

Reaching orbit needs roughly the fourth row. Fifteen tonnes of propellant per tonne of everything else, and that is before losses, before staging, before anything comes home.

## Two questions that sound identical and are not

This confuses nearly everyone, and the codebase keeps them apart deliberately, as `Scenario.at_payload()` and `Scenario.solve_payload()`.

**During a burn**, the vehicle keeps getting lighter, so equal chunks of propellant buy *more and more* speed. The last tonne is worth many times the first. This is why crews are pressed hardest into their seats just before engine cutoff.

**Across designs**, loading more propellant onto the pad buys *less and less*, because the extra propellant has to lift itself. This is the wall.

Both are consequences of the same equation. Chapter 1 shows them side by side for exactly this reason.

## The other half: specific impulse

`v_e = Isp · g₀`. Specific impulse is quoted in seconds because the number is then identical in every unit system, which is why this project never converts it.

One doubling of mass ratio buys:

| Engine | Isp | Exhaust velocity | Speed per doubling |
|---|---:|---:|---:|
| [Merlin 1D](../engines/merlin-1d.md), kerolox | 283 s | 2,775 m/s | 1,924 m/s |
| [Raptor 3](../engines/raptor-3.md), methalox | 327 s | 3,207 m/s | 2,223 m/s |
| Vinci, hydrolox vacuum | 457 s | 4,482 m/s | 3,106 m/s |

Isp enters linearly; the mass ratio enters through a logarithm. **Better engines move the whole curve, which is real and valuable, and still moves it less than most people expect.** See [propellant choices](propellant-choices.md).

## What it deliberately ignores

Gravity, atmosphere, steering. The equation describes a burn in empty space, so it is an upper bound and a real launch never achieves it. What it loses is [ascent losses](ascent-losses.md), roughly a fifth of everything the engines produce.
