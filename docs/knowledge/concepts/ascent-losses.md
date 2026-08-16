---
type: Concept
title: Ascent losses
description: Roughly a fifth of what the engines produce never becomes speed, and gravity takes most of it.
tags: [physics, losses, gravity-loss, drag, ascent]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, sections 2.4 and 2.5
    last_modified: 2026-08-16
  - id: guidance
    resource: ../../../raw/2026-08-16-ascent-guidance-open-and-closed-loop.md
    title: Ascent guidance, open loop and closed loop
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-08-31

provenance: derived
---

# Ascent losses

[The rocket equation](the-rocket-equation.md) describes a burn in empty space. A real launch is fought against gravity and air the whole way up, and the gap is not small.

For a Falcon 9 as simulated here, the engines produce **9,669 m/s** and only **7,832 m/s** becomes speed.

| Where it went | Share |
|---|---:|
| Speed gained | 81 % |
| Gravity | 16 % |
| Steering | 3 % |
| Air | 0.2 % |

## Gravity takes far more than air, which surprises people

**Gravity loss** is the big one, typically 1,000 to 1,800 m/s. Every second the rocket spends climbing, Earth removes about 9.8 m/s from its vertical speed. A launch lasting several hundred seconds hands over well over a kilometre per second that way.

**Drag loss** is tiny by comparison, often under 100 m/s. Air is essentially gone above 60 km and the rocket is only moving fast enough to care about it for about a minute.

This inverts most people's intuition, and it explains why launches look the way they do. **Rockets tip over almost immediately** because going straight up is expensive and altitude is not the goal. Orbit is sideways speed; height only buys thin air to build that speed in.

**Steering loss** is what you pay for thrust that is not pointing along the direction of travel. Small, but it is the term that punishes pitching over too aggressively.

## Gravity loss shrinks towards the end

Going sideways fast holds you up. The faster the horizontal speed, the more the Earth curves away beneath the vehicle and the less thrust it must spend fighting its own weight. At orbital speed the two cancel exactly, which is the definition of being in orbit.

## The budget to orbit

Total ideal Δv from the pad is normally **9,300 to 9,600 m/s** for low Earth orbit. This project uses **9,404 m/s**, calibrated against Falcon 9 and the Space Shuttle, both of which land inside the band at their published payloads.

Circular orbital velocity itself is only 7,784 m/s at 200 km. The rest is losses and the climb.

## Launch site latitude is worth real payload

Earth's surface moves east at `465.1 · cos(latitude)` m/s, and a rocket starts with that for free if it flies east.

From Starbase at 26° N: **+418 m/s** due east, +280 m/s to Starlink's 53° inclination, and **nothing at all** for a polar orbit. Kourou at 5.2° N gives [Ariane](../vehicles/ariane-6.md) more of this than any other site in the library.

That is why polar and sun-synchronous launches carry noticeably less, and it is geometry rather than engineering.

## Where this is modelled

`src/rocketry/ascent.py`, a 2D numerical integration with the losses decomposed by an exact identity rather than estimated. A hand-written RK4 integrator and a forty-line standard atmosphere, both written out rather than imported, which kept about 15 MB of `scipy` out of the browser bundle.

Model limits worth knowing: one drag coefficient for the whole stack, a prescribed pitch program rather than a free gravity turn, and a non-rotating Earth. Good enough to be right about the size and ordering of the losses, not a trajectory design tool.

## Which losses you pay depends on how it is steered

A launch vehicle is not steered the same way for the whole flight. Inside the atmosphere it has to fly close to zero angle of attack or the structural loads become unsurvivable, so its attitude comes from a **stored pitch program** that cannot chase a target. Above the atmosphere that constraint lifts and **closed-loop guidance** takes over, steering at whatever attitude the target orbit demands. See [the captured source](../../../raw/2026-08-16-ascent-guidance-open-and-closed-loop.md).

Both halves matter to the accounting here, and modelling only the first is what a naive simulation does. The open-loop program can put a vehicle on a ballistic arc that peaks above 200 km and then falls back while the engines are still running, which no real launch does. Nothing in the loss decomposition looks wrong when that happens: gravity, drag and steering still add up exactly. The trajectory is simply not one anybody would fly.

The closed loop aims at an altitude *and* at zero climb rate, arriving at both when the propellant runs out, because an orbit is a position and a velocity together. As the vehicle approaches orbital speed the thrust it needs to hold itself up falls away to nothing, which is the same statement as **orbit is sideways speed** written as a control law.
