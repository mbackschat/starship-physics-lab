---
type: Concept
title: What reuse costs
description: Coming home is paid for uphill, in propellant carried all the way to staging and never used to accelerate anything.
tags: [physics, reuse, recovery, rtls, droneship, tower-catch]

sources:
  - id: physics-ref
    resource: ../../physics-reference.md
    title: Rocket Physics Reference, section 2.7
    last_modified: 2026-08-16
  - id: reserve
    resource: ../../../raw/2026-08-16-falcon9-recovery-reserve.md
    title: What a Falcon 9 booster holds back to come home
    last_modified: 2026-08-16

generated: { by: claude-opus-5, at: 2026-08-16T00:00:00Z }

status: stable
stale_after: 2027-08-31

provenance: derived
---

# What reuse costs

A stage that comes home must hold propellant back. That propellant is carried the whole way up, accelerated along with everything else, and then used to slow down rather than to speed anything up.

**It is paid for uphill.** That is the entire idea, and it is why reuse costs payload rather than being free.

## The three ways down, and what they cost

| Mode | What it does | Relative cost |
|---|---|---|
| **Expendable** | Nothing. The stage is discarded. | none |
| **Droneship** | Lands downrange on a ship, roughly where the trajectory already took it. | moderate |
| **Return to launch site** | Cancels downrange velocity and flies back. | highest |
| **Tower catch** | As RTLS, but caught by the launch tower instead of landing on legs. | highest, minus the legs |

Falcon 9 carries 17.5 t with droneship recovery against 22.8 t expendable, **both quoted for the same 28.5° reference orbit**. Same rocket, same stages, same destination; recovery costs about a quarter of the payload.

That the two figures share a reference orbit is worth stating rather than assuming. Had one been a 53° Starlink orbit, part of the apparent difference would have been an inclination penalty rather than recovery propellant, and any model tuned to close the gap would have been fitted to the wrong thing.

The [Super Heavy booster](../vehicles/super-heavy-v3.md) returns to the launch site, which is the expensive choice: 1,800 m/s of boostback against 600 m/s of landing burn. Cancelling downrange velocity and flying home dominates everything else.

## Why the reserve compounds

The propellant a stage holds back is itself subject to [the rocket equation](the-rocket-equation.md). A heavier stage needs more to slow it, and that extra must also be carried, so the reserve grows faster than linearly with the manoeuvres asked of it.

The library models this properly. Recovery is stored as a list of burns whose mass ratios compose, rather than as a flat percentage, so the reserve scales with the stage's mass the way real propellant does. Stored last-burn-first, because that is the order the ratios compose in.

`Stage` validation rejects any stage that has committed more propellant than it carries, at load time and with the numbers in the message. A plausible-looking set of burns can quietly exceed the tanks, and caught later it surfaces as an impossible mass ratio deep inside a calculation.

## What it costs Starship

Super Heavy carries about **330 t** of propellant to staging purely so it can come home.

The ship holds back roughly **38 t** for its deorbit and landing burns, on a 220 t vehicle. The source article assumes about 40 t, and the model reproduces that without being told to, because the burns are modelled rather than assumed.

## The honest counterweight

Payload fraction is the wrong scoreboard for a reusable vehicle. [Saturn V](../vehicles/saturn-v.md) beats everything modern at 4.75 %, and it threw away three stages every flight and flew thirteen times.

A vehicle optimised for payload fraction and one optimised for cost per tonne are solving different problems. What this page quantifies is the *physical* price of reuse. Whether it is worth paying is an economic question the physics cannot answer.

## Where this is modelled

`src/rocketry/reuse.py`, surfaced in the reuse chapter and reused by the sandbox.

## Checking a reserve without trusting a velocity

A recovery budget quoted in m/s is only as good as the frame it was quoted in. "An entry burn of 1,300 m/s" is ambiguous between the velocity the *engines* removed, which is what propellant is charged for, and the velocity the *stage* lost, which includes drag. Most of a Falcon 9's entry deceleration is the atmosphere. Charging propellant for the second double-counts the air.

So a reserve is worth checking by routes that mention no velocity at all:

- **As a share of the propellant load.** All three return-to-launch-site burns run 6 to 10 % of a Falcon 9 first stage's propellant. A droneship recovery skips the boostback and should sit below that.
- **As engine flow times burn duration.** A Merlin 1D flows about 305 kg/s at sea level and cannot throttle below 57 %. Falcon 9 flies an entry burn of roughly 20 to 30 s on three engines and a landing burn of roughly 30 s on one. At 70 % throttle that is 21 to 24 t.

Both agree with the delta-v route, which is what makes the delta-v route usable. The library's earlier 10.1 t failed all three: 2.6 % of the load, and an entry burn of about six seconds. `tests/test_scenarios.py::TestRecoveryProfilesMatchTheReference` now holds the reserve against all of them.
